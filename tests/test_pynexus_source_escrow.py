"""Original provider escrow safeguards; all ZIP bytes here are synthetic TEST ONLY."""
import hashlib
from io import BytesIO
from pathlib import Path
import zipfile

import pytest

from importlib.util import module_from_spec,spec_from_file_location

MODULE=Path(__file__).resolve().parents[1]/"scripts/preserve_pynexus_evidence.py"
spec=spec_from_file_location("pynexus_escrow_private_source",MODULE)
escrow=module_from_spec(spec)
spec.loader.exec_module(escrow)


def test_reference_artifact_source_hashes_unique_and_exact():
    assert len(escrow.REGISTER)==3
    assert len({x["artifact_id"] for x in escrow.REGISTER.values()})==3
    assert all(len(x["sha256"])==64 for x in escrow.REGISTER.values())
    assert escrow.EXPIRES=="2026-12-24"


def test_refuses_original_raw_market_archive_inside_public_repo():
    with pytest.raises(escrow.EvidenceEscrowError,match="OUTSIDE"):
        escrow.legal_destination(escrow.REPO_ROOT/"private-evidence")
    with pytest.raises(escrow.EvidenceEscrowError,match="OUTSIDE"):
        escrow.legal_destination(escrow.REPO_ROOT)


def fabricated_zip_bytes():
    b=BytesIO()
    with zipfile.ZipFile(b,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for i in range(4):z.writestr(f"unit_test_only_{i}.txt","pure mathematical test data")
    return b.getvalue()


def test_only_exact_byte_verified_zip_is_accepted(tmp_path):
    original=fabricated_zip_bytes()
    expected=hashlib.sha256(original).hexdigest()
    path=tmp_path/"test_source.zip"
    path.write_bytes(original)
    assert escrow.valid_archive(path,expected) is True
    with pytest.raises(escrow.EvidenceEscrowError,match="SHA256"):
        escrow.valid_archive(path,"0"*64)


def test_fake_network_bytes_rejected_before_escrow_filename_created(tmp_path):
    original=fabricated_zip_bytes()
    entry={
        "filename":"synthetic_example_ONLY.zip",
        "sha256":"0"*64, # deliberate mismatch, never actual source SHA
        "artifact_id":123,
    }
    with pytest.raises(escrow.EvidenceEscrowError,match="SHA256"):
        escrow.save_from_api(entry,tmp_path,"unit-test-bearer-only",
            opener=lambda request,timeout:BytesIO(original))
    assert not (tmp_path/entry["filename"]).exists()
    assert not list(tmp_path.glob(".original_tmp_*"))


def test_fake_authenticated_stream_is_verified_and_not_overwritten(tmp_path):
    original=fabricated_zip_bytes()
    entry={
        "filename":"synthetic_example_ONLY.zip",
        "sha256":hashlib.sha256(original).hexdigest(),
        "artifact_id":123,
    }
    status=escrow.save_from_api(entry,tmp_path,"unit-test-bearer-only",
                                opener=lambda request,timeout:BytesIO(original))
    assert status=="downloaded_and_verified"
    assert escrow.file_sha256(tmp_path/entry["filename"])==entry["sha256"]
    again=escrow.save_from_api(entry,tmp_path,"unit-test-bearer-only",
                               opener=lambda request,timeout:BytesIO(b"should never download again"))
    assert again=="existing_verified"
