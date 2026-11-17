"""Synthetic fake ZIP archives only; no original ENTSO-E/PyNEXUS data in CI."""
import json
from pathlib import Path
import shutil
import zipfile
import pytest

from scripts import verify_private_pynexus_recovery as rec
from scripts import preserve_pynexus_evidence as old


def fake_data(tmp_path,monkeypatch):
    root=tmp_path/"PRIVATE_ORIGINAL_ESCROW";other=tmp_path/"PRIVATE_RECOVERY"
    root.mkdir();other.mkdir()
    registry={}
    original_meta={}
    for i,key in enumerate(("E","E_plus_S","A44_source_XML")):
        name=f"frozen_{i}.zip"
        f=root/name
        with zipfile.ZipFile(f,"w") as z:
            for q in range(4):
                z.writestr(f"file{q}.txt",f"{key}-{q}")
        digest=old.file_sha256(f)
        registry[key]={"filename":name,"sha256":digest}
        original_meta[key]={"original_filename":name,"original_archive_sha256":digest,"file_bytes":f.stat().st_size}
    monkeypatch.setattr(rec,"REGISTER",registry)
    meta={
        "schema_version":"oem.ptx.original_2023_evidence_private_escrow.v1.0",
        "source_repo":old.SOURCE_REPO,
        "copied_to_public_GitHub":False,
        "raw_market_data_reuse_and_redistribution_licence_must_be_independently_checked":True,
        "original_source_SHA_lock":original_meta
    }
    (root/"PRIVATE_original_2023_source_provenance.json").write_text(json.dumps(meta))
    return root,other,registry


def test_second_private_copy_restored_and_both_hash_checked(tmp_path,monkeypatch):
    root,other,registry=fake_data(tmp_path,monkeypatch)
    x=rec.verify_pair(root,other,make_secondary=True)
    assert x["all_three_original_source_archives_sha_and_crc_verified_in_two_directories"]
    assert len(x["source_file_checks"])==3
    assert not x["full_P0_release_gate_passed"]
    assert not x["licence_conditions_and_permitted_redistribution_independently_reviewed"]
    assert x["same_filesystem_not_independent_backup"]
    assert not x["independent_physical_storage_device_verified"]
    assert x["independent_physical_device_requires_manual_verification"]
    assert all((other/v["filename"]).is_file() for v in registry.values())


def test_second_private_copy_tampering_fails_sha(tmp_path,monkeypatch):
    root,other,registry=fake_data(tmp_path,monkeypatch)
    rec.verify_pair(root,other,make_secondary=True)
    (other/registry["E"]["filename"]).write_text("changed")
    with pytest.raises(old.EvidenceEscrowError,match="SHA256"):
        rec.verify_pair(root,other)


def test_same_or_nested_location_is_not_independent_private_archive(tmp_path,monkeypatch):
    root,other,registry=fake_data(tmp_path,monkeypatch)
    with pytest.raises(old.EvidenceEscrowError,match="distinct"):
        rec.verify_pair(root,root)
    nested=root/"nested";nested.mkdir()
    with pytest.raises(old.EvidenceEscrowError,match="distinct"):
        rec.verify_pair(root,nested)


def test_incomplete_original_source_manifest_rejected(tmp_path,monkeypatch):
    root,other,registry=fake_data(tmp_path,monkeypatch)
    meta_path=root/"PRIVATE_original_2023_source_provenance.json"
    meta=json.loads(meta_path.read_text())
    del meta["original_source_SHA_lock"]["A44_source_XML"]
    meta_path.write_text(json.dumps(meta))
    with pytest.raises(old.EvidenceEscrowError,match="not completely"):
        rec.verify_pair(root,other,make_secondary=True)



def test_hardlinked_secondary_is_not_independent_backup(tmp_path, monkeypatch):
    """Two valid ZIP paths pointing to the same inode are only one physical copy."""
    import os
    root, other, registry = fake_data(tmp_path, monkeypatch)
    for entry in registry.values():
        os.link(root / entry["filename"], other / entry["filename"])
    with pytest.raises(old.EvidenceEscrowError, match="same file/inode"):
        rec.verify_pair(root, other)


def test_symlinked_secondary_is_not_independent_backup(tmp_path, monkeypatch):
    """A symlink to an original ZIP cannot satisfy the recovery-copy contract."""
    root, other, registry = fake_data(tmp_path, monkeypatch)
    for entry in registry.values():
        (other / entry["filename"]).symlink_to(root / entry["filename"])
    with pytest.raises(old.EvidenceEscrowError, match="symbolic links"):
        rec.verify_pair(root, other)


def test_actual_copied_zip_has_distinct_inode(tmp_path, monkeypatch):
    """The synthetic-copy success path is not rejected by alias checks."""
    root, other, registry = fake_data(tmp_path, monkeypatch)
    rec.verify_pair(root, other, make_secondary=True)
    for entry in registry.values():
        a, b = root / entry["filename"], other / entry["filename"]
        assert (a.stat().st_dev, a.stat().st_ino) != (b.stat().st_dev, b.stat().st_ino)


def test_symlinked_primary_manifest_rejected(tmp_path, monkeypatch):
    root, other, registry = fake_data(tmp_path, monkeypatch)
    manifest = root / "PRIVATE_original_2023_source_provenance.json"
    independent = tmp_path / "manifest_copy.json"
    independent.write_bytes(manifest.read_bytes())
    manifest.unlink()
    manifest.symlink_to(independent)
    with pytest.raises(old.EvidenceEscrowError, match="manifest missing"):
        rec.verify_pair(root, other, make_secondary=True)


def test_dangling_secondary_symlink_not_overwritten(tmp_path, monkeypatch):
    root, other, registry = fake_data(tmp_path, monkeypatch)
    target = tmp_path / "nonexistent_original.zip"
    alias = other / registry["E"]["filename"]
    alias.symlink_to(target)
    with pytest.raises(old.EvidenceEscrowError, match="symbolic links"):
        rec.verify_pair(root, other, make_secondary=True)
    assert alias.is_symlink()
    assert not target.exists()
