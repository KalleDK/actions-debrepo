#!/usr/bin/env bash

mkdir ~/.gnupg
chmod 700 ~/.gnupg

KEYNAME="${KEYNAME:-My Name}"
KEYCOMMENT="${KEYCOMMENT:-My Comment}"
KEYMAIL="${KEYMAIL:-test@example.com}"

gpg --batch --passphrase "" --quick-gen-key "${KEYNAME} (${KEYCOMMENT}) <${KEYMAIL}>" ed25519/sign+cv25519/encr
gpg --list-secret-keys --keyid-format=long
gpg --export --armor "${KEYNAME}" > /keys/pubkey.asc
gpg --export-secret-keys --armor "${KEYNAME}" > /keys/privkey.asc