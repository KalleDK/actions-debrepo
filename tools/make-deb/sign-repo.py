#!/usr/bin/env python3

import pathlib
import base64
import subprocess
from typing import Optional
import typer
import pydantic_settings
from dotenv import load_dotenv
import sys

class Stdout:
    def write_bytes(self, data: bytes):        
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()


def unpack_key(key: str):
    return base64.b64decode(key)


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(env_prefix='KEY_')
    
    workdir: pathlib.Path = pathlib.Path(".keys")
    priv: str
    pub: str

    def run(self, args: list[str], input: bytes | None = None):
        return subprocess.run(args, input=input, check=True, env={"GNUPGHOME": str(self.workdir)}, capture_output=True)

    def get_key_uid(self):
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
    load_dotenv(env)
    settings = Settings() # type: ignore
    settings.workdir.mkdir(parents=True, exist_ok=True, mode=0o700)
    settings.run(["gpg", "--import"], input=unpack_key(settings.priv))
    key_uid = settings.get_key_uid()
    print("Imported key with uid:", key_uid)
    

@app.command("sign")
def sign_repo(src: pathlib.Path, dst: Optional[pathlib.Path] = None, clear: bool = False , env: pathlib.Path = pathlib.Path(".env")):
    load_dotenv(env)
    stdout = Stdout() if dst is None else dst
    settings = Settings() # type: ignore
    key_uid = settings.get_key_uid()
    signed_data = settings.run(["gpg", "--default-key", key_uid, "--armor", ("--clear" if clear else "--detach-sign")], input=src.read_bytes()).stdout
    stdout.write_bytes(signed_data)
    

@app.command("export")
def export_keys(path: Optional[pathlib.Path] = None, env: pathlib.Path = pathlib.Path(".env"), clear: bool = False):
    load_dotenv(env)
    stdout = Stdout() if path is None else path
    settings = Settings() # type: ignore
    key_uid = settings.get_key_uid()
    if clear:
        clear_pub_key = settings.run(["gpg", "--armor", "--export", key_uid]).stdout
    else:
        clear_pub_key = settings.run(["gpg", "--export", key_uid]).stdout
    stdout.write_bytes(clear_pub_key)
    

def main():
    app()

if __name__ == "__main__":
    main()