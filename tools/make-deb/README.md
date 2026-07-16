# make-deb

Python tools used inside the `actions-debrepo` Docker container to sign a
Debian APT repository and generate a browsable index.

## Tools

### `sign-repo`

Manages an isolated GPG keyring and signs APT `Release` files.

```
Usage: sign-repo [import|sign|export] [OPTIONS]

Commands:
  import   Import KEY_PRIV / KEY_PUB from environment into KEY_WORKDIR keyring.
  sign     Sign a Release file (detached .gpg or clear-text InRelease).
  export   Export the public key from the keyring (binary .gpg or armored .asc).

Environment variables:
  KEY_WORKDIR  Directory used as GNUPGHOME (default: .keys)
  KEY_PRIV     Base64-encoded armored GPG private key
  KEY_PUB      Base64-encoded armored GPG public key
```

### `create-markdown`

Recursively generates `index.md` files for a repository tree so that GitHub
Pages can render a browsable directory listing.

```
Usage: create-markdown REPO_PATH

Environment variables:
  DEB_REPO_URL         Base URL where the repo is hosted
  DEB_PUBLIC_KEY_NAME  Stem for the public key files
  DEB_REPO_NAME        Name used in the sources-list snippet
```

### `create-repo` (module)

Utility helpers for inspecting `.deb` files: extracting architecture and
package name, computing SHA-256 / SHA-1 / MD5 hashes.  Not yet wired into
the main pipeline — currently the repository index is built by
`apt-ftparchive`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Running tests

```bash
pytest tests/ -v
```
