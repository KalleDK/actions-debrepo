#!/usr/bin/env bash
# create-repo.sh - Build and sign a Debian APT repository from a set of .deb packages.
#
# This script is the main entry point for the Docker container.  It reads
# configuration from GitHub Actions input environment variables (INPUT_*),
# builds the repository structure using apt-ftparchive, signs the Release
# files with GPG, and exports the public key alongside a browsable index.
#
# Required environment variables (set automatically by GitHub Actions):
#   INPUT_PKGS_PATH  - Path to a directory containing the source .deb files.
#   INPUT_REPO_URL   - Public base URL at which the repo will be served.
#   INPUT_KEY_NAME   - Stem for the exported public key files (<name>.gpg/.asc).
#   INPUT_REPO_NAME  - Identifier used in the APT sources list file.
#   INPUT_KEY_PUB    - Base64-encoded armored GPG public key.
#   INPUT_KEY_PRIV   - Base64-encoded armored GPG private key.

set -e -u -o pipefail

# ---------------------------------------------------------------------------
# Repo configuration – map INPUT_* variables to descriptive names
# ---------------------------------------------------------------------------
export REPO_PKGS=${INPUT_PKGS_PATH}
export DEB_REPO_URL=${INPUT_REPO_URL}
export DEB_PUBLIC_KEY_NAME=${INPUT_KEY_NAME}
export DEB_REPO_NAME=${INPUT_REPO_NAME}
export KEY_PUB=${INPUT_KEY_PUB}
export KEY_PRIV=${INPUT_KEY_PRIV}

export BUILD_DIR_REL=.build
export KEY_DIR_REL=${BUILD_DIR_REL}/keys
export REPO_DIR_REL=${BUILD_DIR_REL}/deb

# ---------------------------------------------------------------------------
# Create the build directory layout expected by apt-ftparchive
# ---------------------------------------------------------------------------
mkdir -p ${BUILD_DIR_REL}

# Repository tree:  deb/dists/<suite>/main/binary-<arch>/  and pool/main/
mkdir -p ${REPO_DIR_REL}/dists/{stable,testing}/main/{binary-all,binary-i386,binary-amd64,binary-armhf,binary-arm64,source}
mkdir -p ${REPO_DIR_REL}/pool/main

# Copy all .deb packages from the source directory into the pool.
# `find` is used instead of a glob pattern to handle nested sub-directories
# reliably across all POSIX shells without requiring the bash `globstar` option.
find "${REPO_PKGS}" -name "*.deb" -exec cp {} "${REPO_DIR_REL}/pool/main/" \;

mkdir -p ${BUILD_DIR_REL}/cache

# ---------------------------------------------------------------------------
# Generate Packages / Sources / Contents indices
# ---------------------------------------------------------------------------
pushd ${BUILD_DIR_REL}
apt-ftparchive generate /etc/repoconf/apt-ftparchive.conf
apt-ftparchive -c /etc/repoconf/stable.conf  release deb/dists/stable  > deb/dists/stable/Release
apt-ftparchive -c /etc/repoconf/testing.conf release deb/dists/testing > deb/dists/testing/Release
popd

# ---------------------------------------------------------------------------
# Sign the Release files
# ---------------------------------------------------------------------------
export KEY_WORKDIR=${KEY_DIR_REL}

mkdir -p ${KEY_DIR_REL}
chmod 700 ${KEY_DIR_REL}

# Import private key into the isolated keyring
sign-repo import

# Produce detached signature (.gpg) and inline clear-text signature (InRelease)
sign-repo sign       ${REPO_DIR_REL}/dists/stable/Release  > ${REPO_DIR_REL}/dists/stable/Release.gpg
sign-repo sign --clear ${REPO_DIR_REL}/dists/stable/Release  > ${REPO_DIR_REL}/dists/stable/InRelease
sign-repo sign       ${REPO_DIR_REL}/dists/testing/Release > ${REPO_DIR_REL}/dists/testing/Release.gpg
sign-repo sign --clear ${REPO_DIR_REL}/dists/testing/Release > ${REPO_DIR_REL}/dists/testing/InRelease

# Export the public key in both binary (.gpg) and ASCII-armored (.asc) formats
sign-repo export       > ${REPO_DIR_REL}/${INPUT_KEY_NAME}.gpg
sign-repo export --clear > ${REPO_DIR_REL}/${INPUT_KEY_NAME}.asc

# Generate browsable index.md files for GitHub Pages
create-markdown ${REPO_DIR_REL}

# Emit the output for downstream GitHub Actions steps
echo "repo_path=${REPO_DIR_REL}" >> $GITHUB_OUTPUT
