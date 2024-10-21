#!/usr/bin/env bash

set -v -e -u -o pipefail

# Repo Configuration
export REPO_PKGS=${INPUT_PKGS_PATH}
export DEB_REPO_URL=${INPUT_REPO_URL}
export DEB_PUBLIC_KEY_NAME=${INPUT_KEY_NAME}
export DEB_REPO_NAME=${INPUT_REPO_NAME}
export KEY_PUB=${INPUT_KEY_PUB}
export KEY_PRIV=${INPUT_KEY_PRIV}


export BUILD_DIR_REL=.build
export KEY_DIR_REL=${BUILD_DIR_REL}/keys
export REPO_DIR_REL=${BUILD_DIR_REL}/deb

# Create the build directory
mkdir -p ${BUILD_DIR_REL}

# Create the repo directory
mkdir -p ${REPO_DIR_REL}
mkdir -p ${REPO_DIR_REL}/dists/{stable,testing}/main/{binary-all,binary-i386,binary-amd64,source}
mkdir -p ${REPO_DIR_REL}/pool/main

cp -r ${REPO_PKGS}/**/*.deb ${REPO_DIR_REL}/pool/main/
mkdir -p ${BUILD_DIR_REL}/cache

# Create the repo
pushd ${BUILD_DIR_REL}
apt-ftparchive generate ../apt-ftparchive.conf
apt-ftparchive -c ../stable.conf release deb/dists/stable > deb/dists/stable/Release
apt-ftparchive -c ../testing.conf release deb/dists/testing > deb/dists/testing/Release
popd


# Sign Repo Configuration
export KEY_WORKDIR=${KEY_DIR_REL}

# Create the key directory
mkdir -p ${KEY_DIR_REL}
chmod 700 ${KEY_DIR_REL}

# Import the signing key
sign-repo import

# Sign the repo
sign-repo sign ${REPO_DIR_REL}/dists/stable/Release > ${REPO_DIR_REL}/dists/stable/Release.gpg
sign-repo sign --clear ${REPO_DIR_REL}/dists/stable/Release > ${REPO_DIR_REL}/dists/stable/InRelease
sign-repo sign ${REPO_DIR_REL}/dists/testing/Release > ${REPO_DIR_REL}/dists/testing/Release.gpg
sign-repo sign --clear ${REPO_DIR_REL}/dists/testing/Release > ${REPO_DIR_REL}/dists/testing/InRelease

sign-repo export --clear > ${REPO_DIR_REL}/${INPUT_KEY_NAME}.asc
sign-repo export > ${REPO_DIR_REL}/${INPUT_KEY_NAME}.gpg

create-markdown ${REPO_DIR_REL}

echo "repo_path=${REPO_DIR_REL}" >> $GITHUB_OUTPUT