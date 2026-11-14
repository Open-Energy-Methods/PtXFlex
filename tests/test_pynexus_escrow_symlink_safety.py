"""P0 negative controls use only synthetic ZIP bytes, never licensed source data."""
import json
import zipfile
import pytest
from scripts import preserve_pynexus_evidence as escrow


def test_symlinked_valid_archive_is_rejected_before_hash(tmp_path):
    real = tmp_path / "real.zip"
    with zipfile.ZipFile(real, "w") as z:
        for i in range(4):
            z.writestr(f"synthetic_{i}.txt", str(i))
    alias = tmp_path / "alias.zip"
    alias.symlink_to(real)
    assert escrow.valid_archive(real, escrow.file_sha256(real))
    with pytest.raises(escrow.EvidenceEscrowError, match="non-symlink"):
        escrow.valid_archive(alias, escrow.file_sha256(real))


def test_existing_symlinked_destination_cannot_be_accepted(tmp_path):
    real = tmp_path / "real.zip"
    with zipfile.ZipFile(real, "w") as z:
        for i in range(4):
            z.writestr(f"synthetic_{i}.txt", str(i))
    destination = tmp_path / "private"
    destination.mkdir()
    (destination / "source.zip").symlink_to(real)
    entry = {"filename": "source.zip", "sha256": escrow.file_sha256(real)}
    with pytest.raises(escrow.EvidenceEscrowError, match="non-symlink"):
        escrow.save_from_api(entry, destination, "unused-token")


def test_dangling_symlink_destination_cannot_be_replaced(tmp_path):
    destination = tmp_path / "private"
    destination.mkdir()
    (destination / "source.zip").symlink_to(tmp_path / "nonexistent.zip")
    entry = {"filename": "source.zip", "sha256": "0" * 64}
    with pytest.raises(escrow.EvidenceEscrowError, match="non-symlink"):
        escrow.save_from_api(entry, destination, "unused-token")
