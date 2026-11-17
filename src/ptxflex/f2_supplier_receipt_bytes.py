"""Offline cryptographic check of privately held F2/L1 supplier source bytes.

No supplier documents are committed or uploaded. This verifies identity only,
not technical correctness, supplier authenticity, PED approval or native LCA.
"""
from __future__ import annotations

import hashlib
import hmac
import re
from collections.abc import Mapping
from pathlib import Path


def verify_local_supplier_receipts(records: Mapping, local_files: Mapping) -> dict:
    """Compare every BOM receipt to locally accessible original document bytes.

    local_files maps receipt ID to local Path; caller retains custody. Reject
    unlisted receipts, missing files, empty files, nonregular files, and SHA
    mismatches. A passing result is only a *local bytes integrity subcheck*.
    """
    issues = []
    if not isinstance(records, Mapping) or not isinstance(local_files, Mapping):
        return {"passed": False, "findings": ["records and local_files must be mappings"],
                "claim_scope": "local SHA-256 byte identity only; not certification or LCA"}
    declared = {}
    for category, row in sorted(records.items(), key=lambda pair: str(pair[0])):
        if not isinstance(category, str) or not isinstance(row, Mapping):
            issues.append(f"{category}: invalid category or record")
            continue
        receipt = row.get("supplier_document_receipt_id")
        digest = row.get("supplier_document_sha256")
        if not isinstance(receipt, str) or not receipt.strip() or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            issues.append(f"{category}: missing valid receipt and SHA-256")
            continue
        receipt = receipt.strip()
        if receipt in declared and declared[receipt] != digest:
            issues.append(f"{category}: conflicting digest for receipt")
        declared[receipt] = digest
    for receipt, expected in sorted(declared.items()):
        path = local_files.get(receipt)
        if not isinstance(path, (str, Path)):
            issues.append(f"{receipt}: no local original document")
            continue
        try:
            source = Path(path)
            if not source.is_file() or source.is_symlink():
                raise ValueError("not a regular nonsymlink file")
            h = hashlib.sha256()
            nbytes = 0
            with source.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    nbytes += len(block)
                    h.update(block)
            if nbytes == 0 or not hmac.compare_digest(h.hexdigest(), expected):
                issues.append(f"{receipt}: empty file or SHA-256 mismatch")
        except (OSError, ValueError):
            issues.append(f"{receipt}: unreadable or nonregular local original")
    for receipt in local_files:
        if receipt not in declared:
            issues.append(f"{receipt}: local receipt not declared in BOM")
    return {"passed": not issues and bool(declared), "findings": issues if issues else ([] if declared else ["no supplier receipts"]),
            "receipts_checked": len(declared),
            "claim_scope": "local SHA-256 byte identity only; not certification or LCA"}
