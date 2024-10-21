import hashlib
import pathlib
import enum
from typing import NewType, NamedTuple
import re
import subprocess
import dataclasses

ARCH_RE = re.compile(r"Architecture: (.*)")
PACKAGE_RE = re.compile(r"Package: (.*)")

class Arch(enum.Enum):
    amd64 = "amd64"
    arm64 = "arm64"
    i386 = "i386"

Dist = NewType("Dist", str)
Component = NewType("Component", str)

class DistComponentArch(NamedTuple):
    dist: Dist
    component: Component
    arch: Arch

class DistsComponent(NamedTuple):
    dists: list[Dist]
    component: Component

def detect_dist_component(path: pathlib.Path, scan_output: str) -> DistsComponent:
    return DistsComponent([Dist("stable")], Component("main"))

def detect_arch(path: pathlib.Path, scan_output: str) -> Arch:
    m = ARCH_RE.search(scan_output)
    if not m:
        raise ValueError("No architecture found")
    return Arch(m.group(1))

def detect_name(path: pathlib.Path, scan_output: str) -> str:
    m = PACKAGE_RE.search(scan_output)
    if not m:
        raise ValueError("No package found")
    return m.group(1)


@dataclasses.dataclass
class DebPackageSrc:
    name: str
    arch: Arch
    dists_component: DistsComponent
    path: pathlib.Path

    @classmethod
    def from_file(cls, path: pathlib.Path):
        output = subprocess.check_output(["dpkg-deb", "-I", str(path)]).decode()
        name = detect_name(path, output)
        arch = detect_arch(path, output)
        dist_component = detect_dist_component(path, output)
        return cls(name, arch, dist_component, path)
    
@dataclasses.dataclass
class HashedFile:
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
    
    def write(self):
        self.path.write_bytes(self.data)
        return self
    
def find_packages(path: pathlib.Path) -> list[DebPackageSrc]:
    return [DebPackageSrc.from_file(p,) for p in path.glob("**/*.deb")]

def main():
    packages = find_packages(pathlib.Path("pkgs"))
    print(packages)