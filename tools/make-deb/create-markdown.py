#!/usr/bin/env python3

import os
import pathlib
import typer

DEB_REPO_URL = os.environ["DEB_REPO_URL"]
DEB_PUBLIC_KEY_NAME = os.environ["DEB_PUBLIC_KEY_NAME"]
DEB_REPO_NAME = os.environ["DEB_REPO_NAME"]

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


def create_static_indexes(path: pathlib.Path, header: str = "", base: pathlib.Path | None = None):
    base = base or path
    files: list[pathlib.Path] = list(p for p in path.iterdir() if p.name != "index.md")
    for p in files:
        if p.is_dir():
            create_static_indexes(p, header=header, base=base)
    
    filelinks = sorted(list(f" - [🗁 {p.name}]({p.name})" for p in files if p.is_dir()))
    filelinks.extend(sorted(list(f" - [🗋 {p.name}]({p.name})" for p in files if p.is_file())))
    files_str = "\n".join(filelinks)
    rel_path = path.relative_to(base.parent)
    parts = rel_path.parts
    link_parts = parts[:-1]
    
    link_parts = [f"[{p}](" + ("../" * (len(parts) - n)) + ") / " for n, p in enumerate(link_parts, 1)]
    print(link_parts)


    navline = "/ " + "".join(link_parts) + parts[-1]
    
    INDEX = f"""
{header}

{navline}

## Files:
{files_str}
"""
    (path / "index.md").write_text(INDEX)



def main(repo: pathlib.Path):
    create_static_indexes(repo, HEADER)


if __name__ == "__main__":
    typer.run(main)