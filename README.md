# Create DEB Repository

A GitHub Action that builds and signs a Debian APT repository from a set of
`.deb` packages and publishes it to a static host such as GitHub Pages.

## Overview

The action:

1. Copies your pre-built `.deb` files into the standard APT pool layout.
2. Runs `apt-ftparchive` to generate `Packages`, `Sources`, and `Contents`
   indices for the **stable** and **testing** suites.
3. Signs the `Release` files with your GPG key to produce `Release.gpg`
   (detached) and `InRelease` (clear-text) signatures.
4. Exports the public key in both binary (`.gpg`) and ASCII-armored (`.asc`)
   formats so clients can easily add the repository.
5. Generates browsable `index.md` files for every directory in the tree
   (useful when hosting on GitHub Pages with a Jekyll/static renderer).
6. Emits the repository root path as the `repo_path` output for downstream
   steps (e.g. publishing to Pages).

## Inputs

| Name         | Required | Default | Description |
|--------------|----------|---------|-------------|
| `pkgs_path`  | No       | `pkgs`  | Path to the directory containing `.deb` packages to include. Sub-directories are scanned recursively. |
| `key_name`   | **Yes**  | —       | Stem name for the exported public-key files (produces `<key_name>.gpg` and `<key_name>.asc`). |
| `key_priv`   | **Yes**  | —       | Base64-encoded armored GPG **private** key used to sign the repository. Store as a GitHub Actions **secret**. |
| `key_pub`    | **Yes**  | —       | Base64-encoded armored GPG **public** key. Store as a GitHub Actions **variable**. |
| `repo_url`   | **Yes**  | —       | Public base URL where the repository will be served (e.g. `https://user.github.io/deb`). Embedded in the generated install instructions. |
| `repo_name`  | **Yes**  | —       | Identifier used in the generated APT sources-list file (e.g. `myrepo`). |

## Outputs

| Name        | Description |
|-------------|-------------|
| `repo_path` | Relative path to the built repository root (`.build/deb`). Pass this to your Pages deployment step. |

## Usage

```yaml
- name: Build DEB repository
  uses: KalleDK/actions-debrepo@v0.0.1
  id: build_debrepo
  with:
    key_name: myrepo
    key_priv: ${{ secrets.DEB_KEY_PRIV }}
    key_pub:  ${{ vars.DEB_KEY_PUB }}
    repo_url: https://myuser.github.io/deb
    repo_name: myrepo
    pkgs_path: pkgs

- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v4
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ${{ steps.build_debrepo.outputs.repo_path }}
```

Once deployed, clients can add the repository with:

```bash
# Install the signing key
sudo curl -o /usr/share/keyrings/myrepo.gpg 'https://myuser.github.io/deb/myrepo.gpg'
# or (ASCII-armored form)
curl 'https://myuser.github.io/deb/myrepo.asc' | sudo gpg --dearmor -o /usr/share/keyrings/myrepo.gpg

# Add the stable repository
echo -e "Types: deb\nURIs: https://myuser.github.io/deb\nSuites: stable\nComponents: main\nSigned-By: /usr/share/keyrings/myrepo.gpg" \
  | sudo tee /etc/apt/sources.list.d/myrepo.sources

sudo apt update
```

## Generating a signing key pair

Use the bundled helper (requires Docker):

```bash
make img          # build the Docker image
mkdir keys
make keys         # generates keys/pubkey.asc and keys/privkey.asc
```

Then Base64-encode the keys for storage in GitHub:

```bash
# Store output as the DEB_KEY_PRIV secret
base64 -w0 keys/privkey.asc

# Store output as the DEB_KEY_PUB variable
base64 -w0 keys/pubkey.asc
```

## Local development

```bash
make img     # build the Docker image
# Place .deb files in ./pkgs, create a .env file with the required variables
make run     # run the build
make debug   # open a shell inside the container
```

### Running Python tests

```bash
cd tools/make-deb
pip install -e ".[dev]"
pytest
```

## Repository structure

```
.
├── action.yml            # GitHub Action metadata
├── Dockerfile            # Container image definition
├── Makefile              # Developer convenience targets
├── conf/
│   ├── apt-ftparchive.conf   # Index generation configuration
│   ├── stable.conf           # Release metadata for the stable suite
│   └── testing.conf          # Release metadata for the testing suite
└── tools/
    ├── create-gpg.sh     # Key-pair generation helper
    ├── create-repo.sh    # Main build script (entry point)
    └── make-deb/
        ├── sign-repo.py          # GPG key import / signing / export
        ├── create-markdown.py    # Browsable index generator
        ├── create-repo.py        # Package inspection utilities
        └── tests/                # pytest test suite
```

