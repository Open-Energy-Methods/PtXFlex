"""F2/L1 independent evidence-role segregation check (offline, content-blind).

Four distinct roles must not be represented by the same file or bytes.
This check is necessary for provenance, never sufficient for authenticity,
equipment certification, manufacturing functional-unit compatibility or LCA.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

REQUIRED_ROLES = frozenset({
    "manufacturer_document", "pressure_conformity",
    "installed_bom", "native_lci_provider",
})


def audit_role_segregation(manifest: Mapping) -> dict:
    """Return deterministic fail-closed findings; never read private content."""
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be a mapping")
    records = manifest.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("nonempty records required")
    by_path, by_digest, by_role = defaultdict(list), defaultdict(list), defaultdict(list)
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise ValueError("each record must be a mapping")
        role, rel, digest = (record.get(k) for k in ("role", "relative_path", "sha256"))
        if role not in REQUIRED_ROLES:
            raise ValueError("unsupported evidence role")
        if not isinstance(rel, str) or not rel.strip():
            raise ValueError("missing evidence path")
        if not isinstance(digest, str) or len(digest) != 64 or any(
            c not in "0123456789abcdef" for c in digest
        ):
            raise ValueError("invalid lowercase sha256")
        # The integrity checker separately rejects traversal and symlinks.
        normalized = Path(rel).as_posix()
        by_path[normalized].append(index)
        by_digest[digest].append(index)
        by_role[role].append(index)
    reused_paths = sorted(k for k, v in by_path.items() if len(v) > 1)
    reused_digests = sorted(k for k, v in by_digest.items() if len(v) > 1)
    duplicate_roles = sorted(k for k, v in by_role.items() if len(v) > 1)
    missing_roles = sorted(REQUIRED_ROLES - by_role.keys())
    reasons = []
    if reused_paths:
        reasons.append("reused_evidence_path")
    if reused_digests:
        reasons.append("reused_evidence_bytes_across_roles")
    if duplicate_roles:
        reasons.append("duplicate_evidence_role")
    if missing_roles:
        reasons.append("missing_evidence_role")
    return {
        "schema_version": "oem.ptx.f2l1.role_segregation.v1",
        "missing_roles": missing_roles,
        "duplicate_roles": duplicate_roles,
        "reused_paths": reused_paths,
        "reused_sha256": reused_digests,
        "rejection_reasons": sorted(reasons),
        "role_segregation_complete": not reasons,
        "manufacturer_authenticated": False,
        "physical_design_certified": False,
        "native_bafu_lca_accepted": False,
        "f2_gate_passed": False,
        "l1_gate_passed": False,
    }
