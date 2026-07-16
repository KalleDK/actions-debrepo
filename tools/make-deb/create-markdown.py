#!/usr/bin/env python3
"""create-markdown: Generate ``index.md`` files for every directory in a
Debian repository tree so that static file hosting (e.g. GitHub Pages) can
render a browsable directory listing.

Usage::

    create-markdown <repo-path>

Environment variables required:
    DEB_REPO_URL         - Base URL where the repository is hosted.
    DEB_PUBLIC_KEY_NAME  - Stem used for the public key files (<name>.gpg / <name>.asc).
    DEB_REPO_NAME        - Human-readable name used in the sources list file.
"""

import os
import pathlib
import typer

DEB_REPO_URL = os.environ["DEB_REPO_URL"]
DEB_PUBLIC_KEY_NAME = os.environ["DEB_PUBLIC_KEY_NAME"]
DEB_REPO_NAME = os.environ["DEB_REPO_NAME"]

# Header injected at the top of every generated index.md.
# It contains copy-paste instructions for adding the repository to a Debian/Ubuntu system.
HEADER = f"""
```bash
# Install key
sudo curl -o /usr/share/keyrings/{DEB_PUBLIC_KEY_NAME}.gpg '{DEB_REPO_URL}/{DEB_PUBLIC_KEY_NAME}.gpg'
# or
curl '{DEB_REPO_URL}/{DEB_PUBLIC_KEY_NAME}.asc' | sudo gpg --dearmor -o /usr/share/keyrings/{DEB_PUBLIC_KEY_NAME}.gpg

# Install stable repo
echo -e \"Types: deb\\nURIs: {DEB_REPO_URL}\\nSuites: stable\\nComponents: main\\nSigned-By: /usr/share/keyrings/{DEB_PUBLIC_KEY_NAME}.gpg" | sudo tee /etc/apt/sources.list.d/{DEB_REPO_NAME}.sources
# or
echo \"deb [arch=amd64 signed-by=/usr/share/keyrings/{DEB_PUBLIC_KEY_NAME}.gpg] {DEB_REPO_URL} stable main\" | sudo tee /etc/apt/sources.list.d/{DEB_REPO_NAME}.list
```
# Debian Repository

"""


def create_static_indexes(
    path: pathlib.Path, header: str = "", base: pathlib.Path | None = None
):
    """Recursively create ``index.md`` files for *path* and all sub-directories.

    Each ``index.md`` contains:
    - The shared *header* block (install instructions).
    - A breadcrumb navigation line relative to the repository root.
    - A sorted list of links to child directories and files.

    Args:
        path:   Current directory being processed.
        header: Markdown content prepended to every generated index.
        base:   Root directory of the repository tree (used for building
                relative breadcrumb links).  Defaults to *path* on the first
                call and is passed through recursion unchanged.
    """
    base = base or path

    # Collect all entries except an existing index.md to avoid self-referencing
    files: list[pathlib.Path] = list(p for p in path.iterdir() if p.name != "index.md")

    # Recurse into sub-directories first so children are indexed before parents
    for p in files:
        if p.is_dir():
            create_static_indexes(p, header=header, base=base)

    # Build directory links (folder icon) then file links (document icon), sorted
    filelinks = sorted(list(f" - [🗁 {p.name}]({p.name})" for p in files if p.is_dir()))
    filelinks.extend(
        sorted(list(f" - [🗋 {p.name}]({p.name})" for p in files if p.is_file()))
    )
    files_str = "\n".join(filelinks)

    # Build a breadcrumb trail: "/ root / parent / current"
    rel_path = path.relative_to(base.parent)
    parts = rel_path.parts
    link_parts = parts[:-1]

    link_parts = [
        f"[{p}](" + ("../" * (len(parts) - n)) + ") / "
        for n, p in enumerate(link_parts, 1)
    ]

    navline = "/ " + "".join(link_parts) + parts[-1]

    INDEX = f"""
{header}

{navline}

## Files:
{files_str}
"""
    (path / "index.md").write_text(INDEX)


def main(repo: pathlib.Path):
    """Entry point: generate index files for the entire repository tree."""
    create_static_indexes(repo, HEADER)


if __name__ == "__main__":
    typer.run(main)
