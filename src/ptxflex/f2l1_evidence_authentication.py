"""Offline F2/L1 evidence integrity audit. SHA agreement is NOT supplier authentication."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROLES = frozenset(("manufacturer_document", "pressure_conformity", "installed_bom", "native_lci_provider"))

def audit_evidence_manifest(manifest: dict, root: Path) -> dict:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("records"), list) or not manifest["records"]:
        raise ValueError("nonempty evidence records list required")
    root = root.resolve()
    seen = set()
    findings = []
    for item in manifest["records"]:
        if not isinstance(item, dict):
            raise ValueError("record must be an object")
        ident, role, rel, expected = (item.get(k) for k in ("id", "role", "relative_path", "sha256"))
        if not isinstance(ident, str) or not ident.strip() or ident in seen:
            raise ValueError("duplicate or invalid evidence ID")
        seen.add(ident)
        if role not in ROLES:
            raise ValueError("unsupported evidence role")
        if not isinstance(rel, str) or not rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
            raise ValueError("unsafe evidence path")
        if not isinstance(expected, str) or len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            raise ValueError("invalid lowercase SHA256")
        relative = Path(rel)
        path = root / relative
        if not path.resolve().is_relative_to(root):
            raise ValueError("evidence path escapes root")
        if any((root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
            raise ValueError("symlink evidence forbidden")
        present = path.is_file()
        actual = None
        if present:
            with path.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
        findings.append({
            "id": ident, "role": role, "file_present": present,
            "sha256_matches": bool(present and actual == expected),
            "sha256_observed": actual,
            "manufacturer_authenticity_verified": False,
            "independent_review_verified": False,
            "physical_design_approved": False,
            "native_lca_admitted": False,
        })
    return {
        "schema_version": "oem.ptx.f2l1.offline_evidence_integrity.v1",
        "all_files_hash_verified": all(r["sha256_matches"] for r in findings),
        "records": findings,
        "f2_gate_passed": False, "l1_gate_passed": False,
        "complete_industrial_lca_admitted": False,
    }

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("private_evidence_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit_evidence_manifest(json.loads(args.manifest.read_text(encoding="utf-8")), args.private_evidence_root), indent=2))

if __name__ == "__main__":
    main()
