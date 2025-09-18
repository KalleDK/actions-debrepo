#!/usr/bin/env python3

import pathlib
import subprocess

TMPL = """export GITHUB_TOKEN=ghp_yourtokenhere
export GITHUB_OUTPUT="./github-output"
"""

envrc_file = pathlib.Path(".envrc")

if not envrc_file.exists():
    envrc_file.write_text(TMPL.format())

subprocess.run(["direnv", "allow"], check=True)
