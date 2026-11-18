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
    if manifest.is_symlink() or not manifest.is_file():
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
        # Never follow a symlink as a source when validating primary archive.
        if a.is_symlink():
            raise EvidenceEscrowError("source escrow archives must be regular files, not symbolic links")
        valid_archive(a,item["sha256"])
        if (recorded[key].get("original_archive_sha256")!=item["sha256"]
                or recorded[key].get("original_filename")!=item["filename"]
                or recorded[key].get("file_bytes")!=a.stat().st_size):
            raise EvidenceEscrowError("original private provenance manifest bytes inconsistent")
        b=s/item["filename"]
        if b.is_symlink():
            raise EvidenceEscrowError("source escrow archives must be regular files, not symbolic links")
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
        # Reject aliases BEFORE archive verification: valid_archive itself is
        # fail-closed and may raise a different symlink exception first.
        if b.is_symlink():
            raise EvidenceEscrowError("source escrow archives must be regular files, not symbolic links")
        valid_archive(b,item["sha256"])
        # Distinct paths can still name the same bytes through symlinks or hardlinks.
        # Such aliases are not a recoverable second copy, even if ZIP/SHA pass.
        if a.is_symlink() or b.is_symlink():
            raise EvidenceEscrowError("source escrow archives must be regular files, not symbolic links")
        if a.resolve()==b.resolve() or (a.stat().st_dev==b.stat().st_dev and a.stat().st_ino==b.stat().st_ino):
            raise EvidenceEscrowError("primary and secondary source archives alias the same file/inode")
        results[key]={
            "verified_SHA256":item["sha256"],
            "verified_zip_crc_primary_and_secondary":True,
            "byte_length_primary":a.stat().st_size,
            "byte_length_secondary":b.stat().st_size,
            "filenames_identical_to_original_private_registry":True,
            "raw_content_uploaded_or_returned":False,
        }
    # The second copy must be independently restorable, including its provenance
    # manifest. Never overwrite an existing but inconsistent manifest.
    backup_manifest = s / manifest.name
    if backup_manifest.is_symlink():
        raise EvidenceEscrowError("secondary provenance manifest must not be a symlink")
    if make_secondary and not backup_manifest.exists():
        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=s, prefix=".private_manifest_", delete=False) as tmp:
                temp = Path(tmp.name)
                tmp.write(manifest.read_bytes())
            # Exclusively create the new backup manifest, never replace a user's copy.
            with backup_manifest.open("xb") as dest:
                dest.write(temp.read_bytes())
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
    manifest_verified = False
    if backup_manifest.exists():
        if not backup_manifest.is_file() or backup_manifest.read_bytes() != manifest.read_bytes():
            raise EvidenceEscrowError("secondary provenance manifest differs from original")
        if (backup_manifest.stat().st_dev, backup_manifest.stat().st_ino) == (
                manifest.stat().st_dev, manifest.stat().st_ino):
            raise EvidenceEscrowError("secondary provenance manifest aliases the primary")
        manifest_verified = True
    different_filesystem_id=p.stat().st_dev!=s.stat().st_dev
    return {
        "schema_version":"oem.ptx.private_two_copy_restoration_verification.v1",
        "verified_at_utc":datetime.now(timezone.utc).isoformat(),
        "original_source_repo":SOURCE_REPO,
        "registered_source_action_artifacts_expiration_not_live_reverified":EXPIRES,
        "all_three_original_source_archives_sha_and_crc_verified_in_two_directories":True,
        "separate_root_directories_eligible":True,
        "secondary_independent_provenance_manifest_sha_bytes_verified":manifest_verified,
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


def restore_from_secondary(primary, secondary, restore_into):
    """Restore only from the secondary in a fresh non-Git directory.

    No network, no original primary archive bytes used to build the restored
    files. Caller first verifies the independent two-copy pair. A full restore
    still does not establish different physical devices or legal rights.
    """
    p = legal_destination(primary)
    s = legal_destination(secondary)
    r = legal_destination(restore_into)
    if r.exists() or r == p or r == s or p in r.parents or s in r.parents or r in p.parents or r in s.parents:
        raise EvidenceEscrowError("restoration must target a new, separate non-nested private directory")
    if not (s / "PRIVATE_original_2023_source_provenance.json").is_file():
        raise EvidenceEscrowError("secondary lacks independent provenance manifest; use --copy-secondary first")
    # Use the secondary as the sole source for all restored bytes.
    result = verify_pair(s, r, make_secondary=True)
    if not result["secondary_independent_provenance_manifest_sha_bytes_verified"]:
        raise EvidenceEscrowError("restored manifest not independently verified")
    return {
        "all_three_archives_restored_and_verified_from_secondary_only": True,
        "restored_private_provenance_manifest_verified": True,
        "no_network_or_original_primary_archive_bytes_used_for_restoration": True,
        "restoration_location": "PRIVATE_OUTSIDE_GIT_NOT_DISCLOSED",
        "independent_physical_storage_device_verified": False,
        "licence_and_external_review_verified": False,
        "full_P0_release_gate_passed": False,
    }


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--primary",required=True,help="existing PRIVATE escrow directory outside git")
    ap.add_argument("--secondary",required=True,help="different PRIVATE backup directory outside git")
    ap.add_argument("--copy-secondary",action="store_true",
                    help="copy original source files to private secondary if absent, validate SHA before commit")
    ap.add_argument("--strict-different-device",action="store_true",
                    help="fail if both directories are on the same storage device")
    ap.add_argument("--restore-into", help="restore solely from verified secondary into this NEW private directory")
    args=ap.parse_args(argv)
    report=verify_pair(args.primary,args.secondary,make_secondary=args.copy_secondary)
    if args.strict_different_device and not report["different_filesystem_device_id_verified"]:
        raise EvidenceEscrowError("two verified private folders have the SAME filesystem device identifier")
    if args.restore_into:
        report["secondary_only_restoration_test"] = restore_from_secondary(
            args.primary, args.secondary, args.restore_into)
    # Print ONLY provenance and boolean checks. No private paths, raw files or API token.
    print(json.dumps(report,sort_keys=True,indent=2,allow_nan=False))


if __name__=="__main__":
    main()
