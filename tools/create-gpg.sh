#!/usr/bin/env bash
# create-gpg.sh - Generate a new GPG key pair and export it to /keys.
#
# This script is a developer convenience tool for creating the signing keys
# required by the repository action.  Run it once via:
#
#   docker run --rm -v "$PWD/keys:/keys" debrepo create_gpg
#
# The exported files can then be Base64-encoded and stored as GitHub repository
# secrets (KEY_PRIV) and variables (KEY_PUB).
#
# Optional environment variables:
#   KEYNAME    - Name field for the key (default: "My Name").
#   KEYCOMMENT - Comment field for the key (default: "My Comment").
#   KEYMAIL    - E-mail address for the key (default: "test@example.com").

set -e -u -o pipefail

mkdir -p ~/.gnupg
chmod 700 ~/.gnupg

KEYNAME="${KEYNAME:-My Name}"
KEYCOMMENT="${KEYCOMMENT:-My Comment}"
KEYMAIL="${KEYMAIL:-test@example.com}"

# Generate an Ed25519 signing key with no passphrase
gpg --batch --passphrase "" --quick-gen-key "${KEYNAME} (${KEYCOMMENT}) <${KEYMAIL}>" ed25519/sign+cv25519/encr

# Show the newly created key for verification
gpg --list-secret-keys --keyid-format=long

# Export to /keys (bind-mounted volume)
gpg --export --armor "${KEYNAME}" > /keys/pubkey.asc
gpg --export-secret-keys --armor "${KEYNAME}" > /keys/privkey.asc

echo "Keys written to /keys/pubkey.asc and /keys/privkey.asc"
