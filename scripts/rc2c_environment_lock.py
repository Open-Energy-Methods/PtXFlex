"""Generate or validate the RC2-C binary-only hash lock for a supported host.

Generation is a controlled maintenance operation: review candidate hashes,
provenance and numerical results before publishing a new lock. It is never
invoked automatically as part of a normal locked installation.
"""
from __future__ import annotations

import argparse
import email
import hashlib
import importlib.metadata as metadata
import json
import platform
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINS = ROOT / "environment/rc2c-pins.txt"
PYTHON = {"linux": (3, 11, 18), "win32": (3, 11, 9)}
INDEX = "https://pypi.org/simple"


def need(ok, msg):
    if not ok:
        raise RuntimeError("RC2-C lock: " + msg)


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def host():
    need(sys.implementation.name == "cpython" and tuple(sys.version_info[:3]) == PYTHON.get(sys.platform),
         "platform-specific exact CPython version required (Linux 3.11.18; Windows 3.11.9)")
    need(platform.machine().lower() in {"amd64", "x86_64"} and sys.maxsize > 2**32,
         "x86-64 host required")
    need(sys.platform in {"win32", "linux"}, "Windows/Linux only")
    return "windows-x64" if sys.platform == "win32" else "linux-x64"


def pins():
    rows = {}
    for line in PINS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        need(re.fullmatch(r"[A-Za-z0-9_.-]+==[A-Za-z0-9_.+-]+", line) is not None,
             "not an exact version: " + line)
        name, version = line.split("==")
        name = normalize(name)
        need(name not in rows, "duplicate pin " + name)
        rows[name] = version
    return rows


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def inspect_wheels(directory, expected):
    seen = {}
    for p in sorted(directory.iterdir()):
        need(p.is_file() and p.suffix == ".whl" and not p.is_symlink(),
             "unexpected non-wheel file")
        with zipfile.ZipFile(p) as z:
            entries = [n for n in z.namelist() if n.count("/") == 1 and n.endswith(".dist-info/METADATA")]
            need(len(entries) == 1, "wheel has invalid package metadata")
            m = email.message_from_bytes(z.read(entries[0]))
        name, version = normalize(m["Name"]), m["Version"]
        need(name in expected and expected[name] == version and name not in seen,
             "wheel version, name, or multiplicity differs: " + p.name)
        seen[name] = {"version": version, "sha256": sha256(p), "wheel_filename": p.name}
    need(set(seen) == set(expected), "not all pinned wheel files present")
    return seen


def lock_text(seen, target):
    lines = [
        "# RC2-C CPython 3.11 " + target + " binary-only lock; generated from actual PyPI wheels.",
        "# Review wheel provenance before accepting a new lock. No source distributions.",
    ]
    for name, row in sorted(seen.items()):
        lines.append(f"{name}=={row['version']} --hash=sha256:{row['sha256']}")
    return "\n".join(lines) + "\n"


def generate():
    target = host()
    expected = pins()
    with tempfile.TemporaryDirectory(prefix="rc2c-wheel-candidate-") as temp:
        p = Path(temp)
        subprocess.run([sys.executable, "-m", "pip", "--isolated", "download",
                        "--index-url", INDEX, "--no-deps", "--only-binary=:all:",
                        "--disable-pip-version-check", "--no-cache-dir", "--dest", str(p),
                        "-r", str(PINS)], check=True)
        seen = inspect_wheels(p, expected)
    # Print only public wheel identities/hashes, never any local paths from the environment.
    print("RC2C_LOCK_MANIFEST " + json.dumps({"target": target, "wheels": seen}, sort_keys=True))
    for line in lock_text(seen, target).splitlines():
        if not line.startswith("#"):
            print("RC2C_LOCK_LINE " + target + " " + line)
    print("RC2C_LOCK_CANDIDATE_COMPLETE " + target)


def parse_lock(path, expected):
    seen = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        m = re.fullmatch(r"([a-z0-9-]+)==([A-Za-z0-9_.+-]+) --hash=sha256:([0-9a-f]{64})", line)
        need(m is not None, "invalid lock row")
        name, version, digest = m.groups()
        need(name not in seen and expected.get(name) == version, "lock differs from exact input pins")
        seen[name] = {"version": version, "sha256": digest}
    need(set(seen) == set(expected), "lock missing or adds distributions")
    return seen


def verify_environment(lock):
    target = host()
    expected = pins()
    parsed = parse_lock(lock, expected)
    need(lock.name == "rc2c-" + target + ".lock", "wrong platform lock")
    for name, row in parsed.items():
        need(metadata.version(name) == row["version"], "installed version mismatch: " + name)
    installed = {normalize(d.metadata["Name"]) for d in metadata.distributions()}
    need(installed <= set(expected) | {"ptxflex", "ptxlens"},
         "unexpected installed distributions: " + ", ".join(sorted(installed - set(expected) - {"ptxflex", "ptxlens"})))
    subprocess.run([sys.executable, "-m", "pip", "check"], check=True)
    print("RC2C_LOCKED_VERSIONS_AND_DEPENDENCY_GRAPH_PASS " + target)


def install(lock, lens_root=None):
    target = host()
    expected = pins()
    need(lock.name == "rc2c-" + target + ".lock", "wrong platform lock")
    parsed = parse_lock(lock, expected)
    need(sys.prefix != sys.base_prefix, "use a fresh virtual environment, not system Python")
    with tempfile.TemporaryDirectory(prefix="rc2c-verified-wheels-") as temp:
        p = Path(temp)
        subprocess.run([sys.executable, "-m", "pip", "--isolated", "download",
                        "--index-url", INDEX, "--no-deps", "--only-binary=:all:",
                        "--require-hashes", "--no-cache-dir", "--dest", str(p),
                        "-r", str(lock)], check=True)
        seen = inspect_wheels(p, expected)
        need(all(seen[n]["sha256"] == row["sha256"] for n, row in parsed.items()),
             "downloaded wheel differs from committed SHA256")
        # All bytes have been checked. No dependency resolution or network at installation.
        subprocess.run([sys.executable, "-m", "pip", "--isolated", "install",
                        "--no-index", "--find-links", str(p), "--only-binary=:all:",
                        "--require-hashes", "--force-reinstall", "--no-deps",
                        "-r", str(lock)], check=True)
    projects = [str(ROOT)]
    if lens_root is not None:
        projects.append(str(lens_root.resolve()))
    for project in projects:
        subprocess.run([sys.executable, "-m", "pip", "--isolated", "install",
                        "--no-index", "--no-deps", "--no-build-isolation", "-e", project], check=True)
    verify_environment(lock)
    print("RC2C_HASH_VERIFIED_BINARY_INSTALL_PASS " + target)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["generate", "install", "verify"])
    p.add_argument("--lens-root", type=Path)
    a = p.parse_args(argv)
    if a.mode == "generate":
        generate()
    else:
        lock = ROOT / "environment" / ("rc2c-" + host() + ".lock")
        if a.mode == "install":
            install(lock, a.lens_root)
        else:
            verify_environment(lock)


if __name__ == "__main__":
    main()
