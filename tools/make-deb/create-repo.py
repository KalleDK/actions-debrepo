"""create-repo: Utility module for inspecting .deb packages.

This module provides helpers for scanning a directory of Debian packages,
extracting their metadata (architecture, package name) and computing file
hashes — groundwork for a pure-Python repository builder.

Note: this module is not yet wired into the main build pipeline; the
repository is currently built via ``apt-ftparchive`` in ``create-repo.sh``.
"""

import hashlib
import pathlib
import enum
from typing import NewType, NamedTuple
import re
import subprocess
import dataclasses

# Regex patterns for extracting metadata fields from `dpkg-deb -I` output
ARCH_RE = re.compile(r"Architecture: (.*)")
PACKAGE_RE = re.compile(r"Package: (.*)")


class Arch(enum.Enum):
    """Debian CPU architectures supported by this repository."""

    amd64 = "amd64"
    arm64 = "arm64"
    i386 = "i386"
    armhf = "armhf"


# Typed aliases to distinguish distribution names and component names in
# function signatures and data structures.
Dist = NewType("Dist", str)
Component = NewType("Component", str)


class DistComponentArch(NamedTuple):
    """Fully qualified location of a package within the repository tree."""

    dist: Dist
    component: Component
    arch: Arch


class DistsComponent(NamedTuple):
    """The set of distributions and component a package belongs to."""

    dists: list[Dist]
    component: Component


def detect_dist_component(path: pathlib.Path, scan_output: str) -> DistsComponent:
    """Determine which distributions and component a package targets.

    Currently always returns ``stable / main``; future implementations could
    parse control-file fields such as ``XB-Apt-Repository`` to allow per-package
    targeting.
    """
    return DistsComponent([Dist("stable")], Component("main"))


def detect_arch(path: pathlib.Path, scan_output: str) -> Arch:
    """Extract the ``Architecture`` field from ``dpkg-deb -I`` output."""
    m = ARCH_RE.search(scan_output)
    if not m:
        raise ValueError(f"No Architecture field found in {path}")
    return Arch(m.group(1))


def detect_name(path: pathlib.Path, scan_output: str) -> str:
    """Extract the ``Package`` (name) field from ``dpkg-deb -I`` output."""
    m = PACKAGE_RE.search(scan_output)
    if not m:
        raise ValueError(f"No Package field found in {path}")
    return m.group(1)


@dataclasses.dataclass
class DebPackageSrc:
    """Metadata about a single .deb file discovered on disk."""

    name: str
    arch: Arch
    dists_component: DistsComponent
    path: pathlib.Path

    @classmethod
    def from_file(cls, path: pathlib.Path) -> "DebPackageSrc":
        """Inspect *path* with ``dpkg-deb -I`` and return a populated instance."""
        output = subprocess.check_output(["dpkg-deb", "-I", str(path)]).decode()
        name = detect_name(path, output)
        arch = detect_arch(path, output)
        dist_component = detect_dist_component(path, output)
        return cls(name, arch, dist_component, path)


@dataclasses.dataclass
class HashedFile:
    """A file together with its pre-computed size and content hashes.

    Hashes are computed eagerly in ``__post_init__`` so that callers always
    have consistent, up-to-date values without needing to call a separate
    method.
    """

    path: pathlib.Path
    data: bytes
    size: int = dataclasses.field(init=False)
    md5: str = dataclasses.field(init=False)
    sha1: str = dataclasses.field(init=False)
    sha256: str = dataclasses.field(init=False)

    def __post_init__(self):
        self.size = len(self.data)
        self.md5 = hashlib.md5(self.data).hexdigest()
        self.sha1 = hashlib.sha1(self.data).hexdigest()
        self.sha256 = hashlib.sha256(self.data).hexdigest()

    def write(self) -> "HashedFile":
        """Write *data* to *path* and return ``self`` for chaining."""
        self.path.write_bytes(self.data)
        return self


def find_packages(path: pathlib.Path) -> list[DebPackageSrc]:
    """Recursively scan *path* for ``*.deb`` files and return their metadata."""
    return [
        DebPackageSrc.from_file(p)
        for p in path.glob("**/*.deb")
    ]


def main():
    packages = find_packages(pathlib.Path("pkgs"))
    print(packages)
