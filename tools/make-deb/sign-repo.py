#!/usr/bin/env python3
"""sign-repo: GPG key management and repository signing tool.

Commands:
    import  - Import private and public keys from environment variables into a
              temporary GPG keyring.
    sign    - Sign a Release file (detached or clear-text) using the imported key.
    export  - Export the public key from the temporary keyring to stdout or a file.

Environment variables used by all commands:
    KEY_WORKDIR  - Directory used as the isolated GNUPGHOME (default: ".keys").
    KEY_PRIV     - Base64-encoded armored GPG private key.
    KEY_PUB      - Base64-encoded armored GPG public key.
"""

import dataclasses
import os
import pathlib
import base64
import subprocess
from typing import Optional
import typer
from dotenv import load_dotenv
import sys


class Stdout:
    """Thin wrapper that writes bytes directly to stdout's binary buffer."""

    def write_bytes(self, data: bytes):
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()


def unpack_key(key: str) -> bytes:
    """Decode a Base64-encoded GPG key back to its raw bytes."""
    return base64.b64decode(key)


@dataclasses.dataclass
class Settings:
    """Runtime configuration loaded from environment variables.

    Attributes:
        workdir: Isolated GNUPGHOME directory that holds the temporary keyring.
        priv: Base64-encoded private GPG key (used for signing/importing).
        pub: Base64-encoded public GPG key (used for verification/importing).
    """

    workdir: pathlib.Path = dataclasses.field(
        default_factory=lambda: pathlib.Path(os.environ.get("KEY_WORKDIR", ".keys"))
    )
    priv: str = dataclasses.field(default_factory=lambda: os.environ["KEY_PRIV"])
    pub: str = dataclasses.field(default_factory=lambda: os.environ["KEY_PUB"])

    def run(self, args: list[str], input: bytes | None = None):
        """Run a subprocess, overriding GNUPGHOME to use the isolated keyring.

        The current process environment is inherited so that system executables
        (such as ``gpg``) remain findable via ``PATH``.
        """
        env = os.environ.copy()
        env["GNUPGHOME"] = str(self.workdir)
        return subprocess.run(
            args,
            input=input,
            check=True,
            env=env,
            capture_output=True,
        )

    def get_key_uid(self) -> str:
        """Return the long key-ID of the first public key in the keyring.

        Parses the colon-delimited output of ``gpg --with-colons`` where the
        ``pub`` record's fifth field (index 4) contains the key ID.
        """
        p = self.run(["gpg", "-k", "--with-colons"])
        output = p.stdout.decode("utf-8")
        lines = output.splitlines()
        for line in lines:
            if line.startswith("pub"):
                return line.split(":")[4]
        raise RuntimeError("No key found")


app = typer.Typer()


@app.command("import")
def import_keys(env: pathlib.Path = pathlib.Path(".env")):
    """Import private and public GPG keys into the isolated keyring.

    Keys are read from KEY_PRIV and KEY_PUB (Base64-encoded) and imported
    into the directory specified by KEY_WORKDIR.
    """
    load_dotenv(env)
    settings = Settings()  # type: ignore
    settings.workdir.mkdir(parents=True, exist_ok=True, mode=0o700)
    settings.run(["gpg", "--import"], input=unpack_key(settings.priv))
    key_uid = settings.get_key_uid()
    print("Imported key with uid:", key_uid)


@app.command("sign")
def sign_repo(
    src: pathlib.Path,
    dst: Optional[pathlib.Path] = None,
    clear: bool = False,
    env: pathlib.Path = pathlib.Path(".env"),
):
    """Sign a Release file and write the signature to stdout or a file.

    With ``--clear`` the output is an inline clear-text signature (InRelease).
    Without ``--clear`` the output is a detached ASCII-armored signature
    (Release.gpg).
    """
    load_dotenv(env)
    # Use stdout wrapper when no destination file is provided
    stdout = Stdout() if dst is None else dst
    settings = Settings()  # type: ignore
    key_uid = settings.get_key_uid()
    signed_data = settings.run(
        [
            "gpg",
            "--default-key",
            key_uid,
            "--armor",
            # --clearsign produces an inline clear-text signature (InRelease);
            # --detach-sign produces a separate binary/armored signature (Release.gpg).
            ("--clearsign" if clear else "--detach-sign"),
        ],
        input=src.read_bytes(),
    ).stdout
    stdout.write_bytes(signed_data)


@app.command("export")
def export_keys(
    path: Optional[pathlib.Path] = None,
    env: pathlib.Path = pathlib.Path(".env"),
    clear: bool = False,
):
    """Export the public key from the isolated keyring.

    With ``--clear`` the key is exported in ASCII-armored (PEM) format (.asc).
    Without ``--clear`` the key is exported in binary GPG format (.gpg).
    """
    load_dotenv(env)
    # Use stdout wrapper when no destination file is provided
    stdout = Stdout() if path is None else path
    settings = Settings()  # type: ignore
    key_uid = settings.get_key_uid()
    if clear:
        # ASCII-armored public key (.asc) – human-readable, suitable for curl install
        clear_pub_key = settings.run(["gpg", "--armor", "--export", key_uid]).stdout
    else:
        # Binary public key (.gpg) – used by apt directly via signed-by
        clear_pub_key = settings.run(["gpg", "--export", key_uid]).stdout
    stdout.write_bytes(clear_pub_key)


def main():
    app()


if __name__ == "__main__":
    main()
