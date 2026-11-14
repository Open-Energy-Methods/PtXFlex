#!/usr/bin/env python3
"""Verify/copy two private, unrestored-on-Git 2023 PyNEXUS source archives.

This tool NEVER downloads or publishes original provider data. It validates
sha256 + ZIP CRC for the THREE source registry originals and optionally
creates a second SHA-audited copy outside Git. Separate directories and distinct filesystem device IDs do NOT prove
independent physical storage devices. st_dev is a minimum filesystem check;
physical drive separation, backup portability and restoration require review.
Legal redistribution rights and independent reviewer signoff remain open.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile

if __package__:
    from .preserve_pynexus_evidence import (
        REGISTER, SOURCE_REPO, EXPIRES, EvidenceEscrowError,
        legal_destination, valid_archive, file_sha256,
    )
else:  # Local direct invocation from the scripts/ directory.
    from preserve_pynexus_evidence import (
        REGISTER, SOURCE_REPO, EXPIRES, EvidenceEscrowError,
        legal_destination, valid_archive, file_sha256,
    )


def verify_pair(primary,secondary,*,make_secondary=False):
    p=legal_destination(primary)
    s=legal_destination(secondary)
    if p==s or p in s.parents or s in p.parents:
        raise EvidenceEscrowError("original source primary and private recovery directories must be distinct, non-nested")
    if not p.is_dir():
        raise EvidenceEscrowError("original private source preservation must be completed first")
    if not s.is_dir():
        if make_secondary:
            s.mkdir(parents=True,exist_ok=False)
        else:
            raise EvidenceEscrowError("secondary private recovery directory missing")
    for directory in (p,s):
        if not directory.is_dir():
            raise EvidenceEscrowError("private storage must be a directory")
    manifest=p/"PRIVATE_original_2023_source_provenance.json"
    if not manifest.is_file():
        raise EvidenceEscrowError("first private escrow manifest missing; run existing source preservation script")
    meta=json.loads(manifest.read_text(encoding="utf-8"))
    if (meta.get("schema_version")!="oem.ptx.original_2023_evidence_private_escrow.v1.0"
            or meta.get("source_repo")!=SOURCE_REPO
            or meta.get("copied_to_public_GitHub") is not False
            or meta.get("raw_market_data_reuse_and_redistribution_licence_must_be_independently_checked") is not True):
        raise EvidenceEscrowError("original archive licensing/source manifest incompatible")
    recorded=meta.get("original_source_SHA_lock")
    if not isinstance(recorded,dict) or set(recorded)!=set(REGISTER):
        raise EvidenceEscrowError("original market/wind/H2 sources not completely registered")
    results={}
    for key,item in REGISTER.items():
        a=p/item["filename"]
        if not a.is_file():
            raise EvidenceEscrowError("missing original private source archive "+key)
        valid_archive(a,item["sha256"])
        if (recorded[key].get("original_archive_sha256")!=item["sha256"]
                or recorded[key].get("original_filename")!=item["filename"]
                or recorded[key].get("file_bytes")!=a.stat().st_size):
            raise EvidenceEscrowError("original private provenance manifest bytes inconsistent")
        b=s/item["filename"]
        if not b.is_file():
            if not make_secondary:
                raise EvidenceEscrowError("secondary restoration copy missing "+key)
            temp=None
            try:
                with tempfile.NamedTemporaryFile(dir=s,prefix=".private_copy_",suffix=".zip",delete=False) as tmp:
                    temp=Path(tmp.name)
                    with a.open("rb") as src:
                        shutil.copyfileobj(src,tmp,1024*1024)
                valid_archive(temp,item["sha256"])
                temp.replace(b)
            finally:
                if temp is not None:
                    temp.unlink(missing_ok=True)
        valid_archive(b,item["sha256"])
        if a.resolve()==b.resolve():
            raise EvidenceEscrowError("primary and secondary source path resolve to same file")
        results[key]={
            "verified_SHA256":item["sha256"],
            "verified_zip_crc_primary_and_secondary":True,
            "byte_length_primary":a.stat().st_size,
            "byte_length_secondary":b.stat().st_size,
            "filenames_identical_to_original_private_registry":True,
            "raw_content_uploaded_or_returned":False,
        }
    different_filesystem_id=p.stat().st_dev!=s.stat().st_dev
    return {
        "schema_version":"oem.ptx.private_two_copy_restoration_verification.v1",
        "verified_at_utc":datetime.now(timezone.utc).isoformat(),
        "original_source_repo":SOURCE_REPO,
        "registered_source_action_artifacts_expiration_not_live_reverified":EXPIRES,
        "all_three_original_source_archives_sha_and_crc_verified_in_two_directories":True,
        "separate_root_directories_eligible":True,
        "different_filesystem_device_id_verified":different_filesystem_id,
        "same_filesystem_not_independent_backup":not different_filesystem_id,
        "independent_physical_storage_device_verified":False,
        "independent_physical_device_requires_manual_verification":True,
        "second_copy_location": "PRIVATE_OUTSIDE_GIT_NOT_DISCLOSED",
        "primary_copy_location":"PRIVATE_OUTSIDE_GIT_NOT_DISCLOSED",
        "licence_conditions_and_permitted_redistribution_independently_reviewed":False,
        "external_independent_scientific_signoff":False,
        "full_P0_release_gate_passed":False,
        "source_file_checks":results,
    }


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--primary",required=True,help="existing PRIVATE escrow directory outside git")
    ap.add_argument("--secondary",required=True,help="different PRIVATE backup directory outside git")
    ap.add_argument("--copy-secondary",action="store_true",
                    help="copy original source files to private secondary if absent, validate SHA before commit")
    ap.add_argument("--strict-different-device",action="store_true",
                    help="fail if both directories are on the same storage device")
    args=ap.parse_args(argv)
    report=verify_pair(args.primary,args.secondary,make_secondary=args.copy_secondary)
    if args.strict_different_device and not report["different_filesystem_device_id_verified"]:
        raise EvidenceEscrowError("two verified private folders have the SAME filesystem device identifier")
    # Print ONLY provenance and boolean checks. No private paths, raw files or API token.
    print(json.dumps(report,sort_keys=True,indent=2,allow_nan=False))


if __name__=="__main__":
    main()
