"""Tests for create-repo.py.

These tests cover the pure-Python helpers that inspect .deb files
(detect_arch, detect_name, HashedFile, etc.) without requiring
``dpkg-deb`` to be installed.
"""

import hashlib
import importlib.util
import pathlib

import pytest

# ---------------------------------------------------------------------------
# Module import helper for hyphenated filename
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).parent.parent


def _import_create_repo():
    spec = importlib.util.spec_from_file_location(
        "create_repo", ROOT / "create-repo.py"
    )
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


mod = _import_create_repo()


# ---------------------------------------------------------------------------
# detect_arch
# ---------------------------------------------------------------------------


class TestDetectArch:
    def test_amd64(self, tmp_path):
        assert mod.detect_arch(tmp_path, "Architecture: amd64") == mod.Arch.amd64

    def test_arm64(self, tmp_path):
        assert mod.detect_arch(tmp_path, "Architecture: arm64") == mod.Arch.arm64

    def test_i386(self, tmp_path):
        assert mod.detect_arch(tmp_path, "Architecture: i386") == mod.Arch.i386

    def test_armhf(self, tmp_path):
        assert mod.detect_arch(tmp_path, "Architecture: armhf") == mod.Arch.armhf

    def test_missing_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Architecture"):
            mod.detect_arch(tmp_path, "Package: mypkg\nVersion: 1.0")

    def test_unknown_arch_raises(self, tmp_path):
        """An architecture not in the Arch enum should raise a ValueError."""
        with pytest.raises(ValueError):
            mod.detect_arch(tmp_path, "Architecture: riscv64")


# ---------------------------------------------------------------------------
# detect_name
# ---------------------------------------------------------------------------


class TestDetectName:
    def test_extracts_name(self, tmp_path):
        assert mod.detect_name(tmp_path, "Package: mypkg\nVersion: 1.0") == "mypkg"

    def test_name_with_hyphens(self, tmp_path):
        assert (
            mod.detect_name(tmp_path, "Package: my-pkg-name") == "my-pkg-name"
        )

    def test_missing_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Package"):
            mod.detect_name(tmp_path, "Architecture: amd64\nVersion: 1.0")


# ---------------------------------------------------------------------------
# detect_dist_component
# ---------------------------------------------------------------------------


class TestDetectDistComponent:
    def test_returns_stable_main(self, tmp_path):
        """Default implementation always returns stable/main."""
        result = mod.detect_dist_component(tmp_path, "")
        assert result.dists == [mod.Dist("stable")]
        assert result.component == mod.Component("main")


# ---------------------------------------------------------------------------
# HashedFile
# ---------------------------------------------------------------------------


class TestHashedFile:
    def test_size(self, tmp_path):
        data = b"hello world"
        hf = mod.HashedFile(path=tmp_path / "f", data=data)
        assert hf.size == len(data)

    def test_md5(self, tmp_path):
        data = b"hello world"
        hf = mod.HashedFile(path=tmp_path / "f", data=data)
        assert hf.md5 == hashlib.md5(data).hexdigest()

    def test_sha1(self, tmp_path):
        data = b"hello world"
        hf = mod.HashedFile(path=tmp_path / "f", data=data)
        assert hf.sha1 == hashlib.sha1(data).hexdigest()

    def test_sha256(self, tmp_path):
        data = b"hello world"
        hf = mod.HashedFile(path=tmp_path / "f", data=data)
        assert hf.sha256 == hashlib.sha256(data).hexdigest()

    def test_write(self, tmp_path):
        data = b"content"
        p = tmp_path / "out.bin"
        hf = mod.HashedFile(path=p, data=data)
        returned = hf.write()
        assert p.read_bytes() == data
        assert returned is hf  # write() returns self for chaining

    def test_empty_data(self, tmp_path):
        hf = mod.HashedFile(path=tmp_path / "empty", data=b"")
        assert hf.size == 0
        assert hf.md5 == hashlib.md5(b"").hexdigest()


# ---------------------------------------------------------------------------
# find_packages (uses a real filesystem but no dpkg-deb)
# ---------------------------------------------------------------------------


class TestFindPackages:
    def test_empty_directory(self, tmp_path):
        """find_packages on a directory with no .deb files returns an empty list."""
        # Verify no .deb files means empty result (no dpkg-deb needed)
        assert mod.find_packages(tmp_path) == []

    def test_finds_deb_files(self, tmp_path, monkeypatch):
        """find_packages should discover .deb files in sub-directories."""
        sub = tmp_path / "sub"
        sub.mkdir()
        deb = sub / "pkg_1.0_amd64.deb"
        deb.write_bytes(b"")

        # Stub out from_file to avoid needing dpkg-deb
        fake_pkg = mod.DebPackageSrc(
            name="pkg",
            arch=mod.Arch.amd64,
            dists_component=mod.DistsComponent([mod.Dist("stable")], mod.Component("main")),
            path=deb,
        )
        monkeypatch.setattr(mod.DebPackageSrc, "from_file", staticmethod(lambda p: fake_pkg))

        packages = mod.find_packages(tmp_path)
        assert len(packages) == 1
        assert packages[0].name == "pkg"

    def test_ignores_non_deb_files(self, tmp_path, monkeypatch):
        """Non-.deb files should not be included."""
        (tmp_path / "README.md").write_text("not a deb")
        (tmp_path / "pkg.tar.gz").write_bytes(b"")

        # from_file should never be called
        def fail(_):
            raise AssertionError("from_file called for a non-.deb file")

        monkeypatch.setattr(mod.DebPackageSrc, "from_file", staticmethod(fail))

        assert mod.find_packages(tmp_path) == []
