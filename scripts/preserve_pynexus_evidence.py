#!/usr/bin/env python3
"""Private evidence escrow for the *original* 2023 PyNEXUS source ZIPs.

Run LOCALLY with a GitHub token permitted to read the upstream source repo.
Never commit the archives or their provider raw ENTSO-E XML to GitHub. The
original Actions artifacts are scheduled to expire 2026-12-24. Program P0
release may not rely on ephemeral historical GitHub Actions retention.

Original archives are preserved UNMODIFIED, compared byte-for-byte to
published SHA256 and ZIP CRC validation, then a source-provenance manifest is
generated in a private destination outside the repository. No API token or
licensed source bytes are included in generated research code/artifacts.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
import stat
from pathlib import Path
import shutil
import tempfile
from urllib.request import Request,urlopen
import zipfile

SOURCE_REPO="abhijith-sivaprasadan/PyNEXUS"
SOURCE_RUN="https://github.com/abhijith-sivaprasadan/PyNEXUS/actions/runs/40229852457"
EXPIRES="2026-12-24"
REGISTER={
    "E":{"artifact_id":12612294862,
         "sha256":"069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051",
         "filename":"original_PyNEXUS_E_2023.zip",
         "kind":"original_2023_market_weather_modelled_hydrogen_dispatch"},
    "E_plus_S":{"artifact_id":12613045475,
         "sha256":"cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9",
         "filename":"original_PyNEXUS_EplusS_2023.zip",
         "kind":"original_2023_market_weather_modelled_hydrogen_dispatch"},
    "A44_source_XML":{"artifact_id":12610917985,
         "sha256":"bc1751b86a3fe712ac2713985c4e189c922a031bacb53a7bd8f422809ba24248",
         "filename":"original_2023_NL_ENTSOE_A44_XML.zip",
         "kind":"original_market_provider_data_license_not_reissued"}
}
REPO_ROOT=Path(__file__).resolve().parents[1]


class EvidenceEscrowError(RuntimeError):
    pass


def file_sha256(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as inp:
        for chunk in iter(lambda:inp.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def valid_archive(path, expected):
    # Reject links and non-regular files before reading source bytes.
    # A symlink can redirect an otherwise SHA-valid archive outside private escrow.
    path=Path(path)
    try:
        mode=path.lstat().st_mode
    except OSError as exc:
        raise EvidenceEscrowError("original source archive unavailable") from exc
    if not stat.S_ISREG(mode):
        raise EvidenceEscrowError("original source archive must be a regular non-symlink file")
    if file_sha256(path)!=expected:
        raise EvidenceEscrowError("original source ZIP bytes do not match frozen verified SHA256")
    try:
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                raise EvidenceEscrowError("original source ZIP has an invalid CRC")
            if len(z.namelist())<4:
                raise EvidenceEscrowError("source archive has unexpectedly few entries")
    except (OSError,zipfile.BadZipFile) as exc:
        raise EvidenceEscrowError("original source is not a valid ZIP archive") from exc
    return True


def legal_destination(path):
    target=Path(path).expanduser().resolve()
    if target==REPO_ROOT or REPO_ROOT in target.parents:
        raise EvidenceEscrowError("original provider source must be stored OUTSIDE this GitHub working tree")
    for parent in (target, *target.parents):
        if (parent / ".git").exists() or (parent / ".git").is_symlink():
            raise EvidenceEscrowError("original provider source must be stored OUTSIDE every Git working tree")
        if (parent / "HEAD").is_file() and (parent / "objects").is_dir() and (parent / "refs").is_dir():
            raise EvidenceEscrowError("original provider source must be stored OUTSIDE bare Git repositories")
    if target.exists() and not target.is_dir():
        raise EvidenceEscrowError("destination is not a private directory")
    return target


def save_from_api(entry,target,token,*,opener=urlopen):
    """Stream original bytes into temporary file and atomically replace ONLY after SHA audit."""
    path=target/entry["filename"]
    if path.exists() or path.is_symlink():
        valid_archive(path,entry["sha256"])
        return "existing_verified"
    url=f"https://api.github.com/repos/{SOURCE_REPO}/actions/artifacts/{entry['artifact_id']}/zip"
    req=Request(url,headers={
        "Authorization":f"Bearer {token}",
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
        "User-Agent":"PtXFlex-v1-science-source-escrow"
    })
    name=None
    try:
        with tempfile.NamedTemporaryFile(dir=target,prefix=".original_tmp_",suffix=".zip",delete=False) as tmp:
            name=Path(tmp.name)
            with opener(req,timeout=120) as resp:
                bytes_seen=0
                while True:
                    chunk=resp.read(1024*1024)
                    if not chunk:break
                    bytes_seen+=len(chunk)
                    if bytes_seen>1024*1024*1024:
                        raise EvidenceEscrowError("source exceeds 1GB safety limit")
                    tmp.write(chunk)
        valid_archive(name,entry["sha256"])
        name.replace(path)
        return "downloaded_and_verified"
    finally:
        if name is not None:
            name.unlink(missing_ok=True)


def preserve(destination,token,*,opener=urlopen):
    if not token or not token.strip():
        raise EvidenceEscrowError("set GH_TOKEN with permission to read ORIGINAL upstream Actions artifacts")
    target=legal_destination(destination)
    target.mkdir(parents=True,exist_ok=True)
    results={}
    for key,entry in REGISTER.items():
        status=save_from_api(entry,target,token,opener=opener)
        p=target/entry["filename"]
        results[key]={
            "artifact_id":entry["artifact_id"],"original_archive_sha256":entry["sha256"],
            "original_filename":entry["filename"],"file_bytes":p.stat().st_size,
            "verified_private_escrow_status":status,"content_class":entry["kind"],
        }
    manifest={
        "schema_version":"oem.ptx.original_2023_evidence_private_escrow.v1.0",
        "preserved_at_utc":datetime.now(timezone.utc).isoformat(),
        "source_workflow_run":SOURCE_RUN,
        "source_repo":SOURCE_REPO,
        "original_source_artifact_expiration":EXPIRES,
        "original_source_SHA_lock":results,
        "original_2023_hydrogen_is_modelled_not_monetized_plant_telemetry":True,
        "contains_original_provider_market_XML":True,
        "raw_market_data_reuse_and_redistribution_licence_must_be_independently_checked":True,
        "copied_to_public_GitHub":False,
        "reference":"PtXFlex / PtXLens P0 evidence escrow; only versioned derived non-restricted summaries go into public research outputs"
    }
    out=target/"PRIVATE_original_2023_source_provenance.json"
    if out.exists() or out.is_symlink():
        if out.is_symlink() or not out.is_file():
            raise EvidenceEscrowError("existing private provenance manifest must be a regular non-symlink file")
        # Prevent silently replacing source/audit manifest.
        old=json.loads(out.read_text(encoding="utf-8"))
        if set(old["original_source_SHA_lock"])!=set(results):
            raise EvidenceEscrowError("existing source manifest incompatible; refuse to overwrite")
        for k in results:
            if old["original_source_SHA_lock"][k]["original_archive_sha256"]!=results[k]["original_archive_sha256"]:
                raise EvidenceEscrowError("existing manifest source hash changed")
    else:
        out.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return manifest


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--destination",type=Path,required=True,
                       help="PRIVATE folder outside repo (no original data uploaded/committed)")
    parser.add_argument("--verify-only",action="store_true",help="verify existing original local ZIPs without token/network")
    a=parser.parse_args(argv)
    if a.verify_only:
        target=legal_destination(a.destination)
        for entry in REGISTER.values():
            valid_archive(target/entry["filename"],entry["sha256"])
        print("All three original immutable source ZIPs match registered SHA256 and CRC; kept outside Git.")
        return
    token=os.environ.get("GH_TOKEN","")
    result=preserve(a.destination,token)
    print(json.dumps({"source_hashes":{k:v["original_archive_sha256"] for k,v in result["original_source_SHA_lock"].items()},
                      "raw_data_location":"PRIVATE user-specified folder outside Git",
                      "original_artifact_expiration":EXPIRES},indent=2))


if __name__=="__main__":
    main()
