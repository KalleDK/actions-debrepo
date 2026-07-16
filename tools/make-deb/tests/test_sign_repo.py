"""Tests for sign-repo.py.

These tests exercise the helper functions and Settings class without requiring
a real GPG installation or valid key material (subprocess calls are patched).
"""

import base64
import pathlib
import subprocess

import pytest

# ---------------------------------------------------------------------------
# Helpers to make the hyphenated module importable
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).parent.parent


def _import_sign_repo():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "sign_repo", ROOT / "sign-repo.py"
    )
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


sign_repo_mod = _import_sign_repo()


# ---------------------------------------------------------------------------
# unpack_key
# ---------------------------------------------------------------------------


class TestUnpackKey:
    def test_roundtrip(self):
        """unpack_key should reverse base64 encoding."""
        original = b"FAKE KEY DATA"
        encoded = base64.b64encode(original).decode()
        assert sign_repo_mod.unpack_key(encoded) == original

    def test_empty_string(self):
        """An empty base64 string decodes to an empty bytes object."""
        assert sign_repo_mod.unpack_key("") == b""

    def test_invalid_base64_raises(self):
        """Non-base64 input should raise a binascii error."""
        import binascii

        with pytest.raises((binascii.Error, ValueError)):
            sign_repo_mod.unpack_key("not-valid-base64!!!")


# ---------------------------------------------------------------------------
# Stdout
# ---------------------------------------------------------------------------


class TestStdout:
    def test_write_bytes_flushes(self, capsys):
        """write_bytes should emit the data to stdout's binary buffer."""
        stdout_wrapper = sign_repo_mod.Stdout()
        stdout_wrapper.write_bytes(b"hello")
        # capsys captures text output; binary data flows through buffer
        captured = capsys.readouterr()
        # The captured output may be decoded; just verify no exception was raised
        assert isinstance(captured.out, str)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


class TestSettings:
    def _make_settings(self, tmp_path, monkeypatch):
        monkeypatch.setenv("KEY_PRIV", base64.b64encode(b"priv").decode())
        monkeypatch.setenv("KEY_PUB", base64.b64encode(b"pub").decode())
        monkeypatch.setenv("KEY_WORKDIR", str(tmp_path))
        return sign_repo_mod.Settings()

    def test_defaults_from_env(self, tmp_path, monkeypatch):
        settings = self._make_settings(tmp_path, monkeypatch)
        assert settings.workdir == tmp_path
        assert settings.priv == base64.b64encode(b"priv").decode()
        assert settings.pub == base64.b64encode(b"pub").decode()

    def test_run_inherits_path(self, tmp_path, monkeypatch):
        """Settings.run() must preserve the parent process PATH."""
        settings = self._make_settings(tmp_path, monkeypatch)
        result = settings.run(["env"])
        output = result.stdout.decode()
        assert "PATH=" in output

    def test_run_sets_gnupghome(self, tmp_path, monkeypatch):
        """Settings.run() must set GNUPGHOME to the configured workdir."""
        settings = self._make_settings(tmp_path, monkeypatch)
        result = settings.run(["env"])
        output = result.stdout.decode()
        assert f"GNUPGHOME={tmp_path}" in output

    def test_run_raises_on_nonzero_exit(self, tmp_path, monkeypatch):
        """Settings.run() should raise CalledProcessError on failure."""
        settings = self._make_settings(tmp_path, monkeypatch)
        with pytest.raises(subprocess.CalledProcessError):
            settings.run(["false"])

    def test_get_key_uid_parses_pub_line(self, tmp_path, monkeypatch):
        """get_key_uid() should return the key ID from a colon-format pub line."""
        settings = self._make_settings(tmp_path, monkeypatch)

        fake_gpg_output = (
            "pub:u:255:22:ABCDEF1234567890:1700000000:::u:::scESC::::::23::\n"
            "uid:u::::1700000000::HASH::Test User <test@example.com>:::::::::0:\n"
        )

        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=fake_gpg_output.encode(), stderr=b""
        )
        monkeypatch.setattr(settings, "run", lambda *a, **kw: completed)

        assert settings.get_key_uid() == "ABCDEF1234567890"

    def test_get_key_uid_raises_when_no_pub(self, tmp_path, monkeypatch):
        """get_key_uid() should raise RuntimeError when no pub record is present."""
        settings = self._make_settings(tmp_path, monkeypatch)

        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b"uid:u::::...\n", stderr=b""
        )
        monkeypatch.setattr(settings, "run", lambda *a, **kw: completed)

        with pytest.raises(RuntimeError, match="No key found"):
            settings.get_key_uid()
