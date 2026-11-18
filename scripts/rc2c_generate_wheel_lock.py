"""Generate an exact wheel-only candidate lock on the target platform.

Run in disposable environment. No project/private data accessed. A public
candidate lock is accepted only after review and fresh hash-verified installation.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile
from email.parser import BytesParser


def lock_lines(wheel_dir):
    rows = {}
    for wheel in sorted(Path(wheel_dir).glob("*.whl")):
        with zipfile.ZipFile(wheel) as z:
            files = [n for n in z.namelist() if n.endswith(".dist-info/METADATA")]
            if len(files) != 1:
                raise ValueError("wheel metadata missing or ambiguous")
            meta = BytesParser().parsebytes(z.read(files[0]))
        name = re.sub(r"[-_.]+", "-", meta["Name"]).lower()
        version = meta["Version"]
        if name in rows:
            raise ValueError("duplicate platform wheel for " + name)
        rows[name] = (version, hashlib.sha256(wheel.read_bytes()).hexdigest(), wheel.name)
    if not rows:
        raise ValueError("empty wheel download")
    return [f"{k}=={v} --hash=sha256:{h}  # {filename}"
            for k, (v, h, filename) in sorted(rows.items())]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("candidate output already exists")
    if sys.version_info[:2] != (3, 11):
        raise ValueError("RC2-C lock targets CPython 3.11")
    with tempfile.TemporaryDirectory(prefix="rc2c-wheel-") as d:
        subprocess.run([sys.executable, "-m", "pip", "download", "--disable-pip-version-check",
                        "--only-binary=:all:", "--index-url", "https://pypi.org/simple",
                        "--dest", d, "-r", str(a.seed)], check=True)
        lines = lock_lines(d)
    # Pip's requirement syntax allows comments after a complete hash.
    a.output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("RC2C_LOCK_BEGIN")
    print("\n".join(lines))
    print("RC2C_LOCK_END")


if __name__ == "__main__":
    main()
