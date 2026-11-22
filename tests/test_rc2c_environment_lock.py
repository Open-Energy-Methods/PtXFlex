"""No network in unit tests; actual wheel downloads are verified by separate CI."""
import hashlib
from pathlib import Path
import zipfile
import pytest
from scripts import rc2c_environment_lock as m


def test_committed_platform_locks_cover_all_exact_pins():
    expected = m.pins()
    assert len(expected) == 25
    for platform in ("linux-x64", "windows-x64"):
        lock = m.ROOT / "environment" / ("rc2c-" + platform + ".lock")
        rows = m.parse_lock(lock, expected)
        assert all(len(v["sha256"]) == 64 for v in rows.values())


@pytest.mark.parametrize("content", [
    "abc>=1 --hash=sha256:" + "a"*64 + "\n",
    "abc==2 --hash=sha256:" + "a"*64 + "\n",
    "abc==1 --hash=sha256:bad\n",
    "abc==1 --hash=sha256:" + "a"*64 + "\nabc==1 --hash=sha256:" + "b"*64 + "\n",
    "",
])
def test_malformed_mutated_or_incomplete_lock_rejected(tmp_path, content):
    p = tmp_path / "bad.lock"
    p.write_text(content, encoding="utf-8")
    with pytest.raises(RuntimeError):
        m.parse_lock(p, {"abc": "1"})


def test_wheel_metadata_only_top_level_and_actual_sha(tmp_path):
    p = tmp_path / "sample-1-py3-none-any.whl"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("sample-1.dist-info/METADATA", "Name: sample\nVersion: 1\n")
        z.writestr("sample/vendor/other-2.dist-info/METADATA", "Name: other\nVersion: 2\n")
    rows = m.inspect_wheels(tmp_path, {"sample": "1"})
    assert rows["sample"]["sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError):
        m.inspect_wheels(tmp_path, {"sample": "2"})


def test_wheel_set_incomplete_rejected(tmp_path):
    with pytest.raises(RuntimeError):
        m.inspect_wheels(tmp_path, {"sample": "1"})
