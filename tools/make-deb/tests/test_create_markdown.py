"""Tests for create-markdown.py.

These tests verify that ``create_static_indexes`` produces correct ``index.md``
files without touching environment variables or a real repository tree beyond
a small temporary directory fixture.
"""

import importlib.util
import pathlib

import pytest

# ---------------------------------------------------------------------------
# Module import helper for hyphenated filename
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).parent.parent


def _import_create_markdown(monkeypatch):
    """Import create-markdown.py with the required environment variables set."""
    monkeypatch.setenv("DEB_REPO_URL", "https://example.com/deb")
    monkeypatch.setenv("DEB_PUBLIC_KEY_NAME", "myrepo")
    monkeypatch.setenv("DEB_REPO_NAME", "myrepo")

    spec = importlib.util.spec_from_file_location(
        "create_markdown", ROOT / "create-markdown.py"
    )
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# ---------------------------------------------------------------------------
# create_static_indexes
# ---------------------------------------------------------------------------


class TestCreateStaticIndexes:
    @pytest.fixture()
    def mod(self, monkeypatch):
        return _import_create_markdown(monkeypatch)

    def test_creates_index_in_root(self, tmp_path, mod):
        """An index.md should be created in the root directory."""
        mod.create_static_indexes(tmp_path)
        assert (tmp_path / "index.md").exists()

    def test_creates_index_in_subdirs(self, tmp_path, mod):
        """An index.md should be created in every sub-directory."""
        sub = tmp_path / "pool" / "main"
        sub.mkdir(parents=True)
        (sub / "pkg_1.0_amd64.deb").write_bytes(b"")
        mod.create_static_indexes(tmp_path)
        assert (tmp_path / "pool" / "index.md").exists()
        assert (sub / "index.md").exists()

    def test_file_links_appear_in_index(self, tmp_path, mod):
        """Files in a directory should be listed in its index.md."""
        (tmp_path / "Release").write_text("dummy")
        mod.create_static_indexes(tmp_path)
        content = (tmp_path / "index.md").read_text()
        assert "Release" in content

    def test_dir_links_appear_in_index(self, tmp_path, mod):
        """Sub-directories should be listed in the parent index.md."""
        (tmp_path / "pool").mkdir()
        mod.create_static_indexes(tmp_path)
        content = (tmp_path / "index.md").read_text()
        assert "pool" in content

    def test_existing_index_is_excluded_from_listing(self, tmp_path, mod):
        """A pre-existing index.md should not link to itself."""
        (tmp_path / "index.md").write_text("old content")
        mod.create_static_indexes(tmp_path)
        content = (tmp_path / "index.md").read_text()
        # The file list must not contain a self-referencing link to index.md
        assert "index.md" not in content

    def test_header_appears_in_index(self, tmp_path, mod):
        """The provided header text should be present in every generated index.md."""
        mod.create_static_indexes(tmp_path, header="CUSTOM HEADER TEXT")
        content = (tmp_path / "index.md").read_text()
        assert "CUSTOM HEADER TEXT" in content

    def test_navline_contains_directory_name(self, tmp_path, mod):
        """The breadcrumb navline should contain the current directory name."""
        mod.create_static_indexes(tmp_path)
        content = (tmp_path / "index.md").read_text()
        assert tmp_path.name in content

    def test_no_debug_print_output(self, tmp_path, mod, capsys):
        """create_static_indexes must not produce stray debug output to stdout."""
        (tmp_path / "sub").mkdir()
        mod.create_static_indexes(tmp_path)
        captured = capsys.readouterr()
        assert captured.out == "", (
            "Unexpected stdout output — a debug print() was left in the code"
        )
