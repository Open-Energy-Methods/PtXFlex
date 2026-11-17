"""F2/L1 cross-evidence admission: completeness and byte integrity are separate checks.

Never promotes supplier metadata, SHA matches, or synthetic fixtures to physical
certification or native BAFU life-cycle acceptance.
"""
from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping

from .f2l1_supplier_admission import audit_supplier_record
from .f2l1_evidence_authentication import audit_evidence_manifest
from .f2l1_role_segregation import audit_role_segregation

REQUIRED_ROLES = frozenset({
    "manufacturer_document", "pressure_conformity",
    "installed_bom", "native_lci_provider",
})


def audit_f2l1_cross_evidence(supplier: Mapping, manifest: dict, private_root: Path) -> dict:
    """Check the two independently maintained ledgers, without trusting either.

    Every evidence record must bind to the same supplier product and revision.
    An identical checksum only proves byte identity; external review remains
    mandatory. This function never accesses network or exports file contents.
    """
    supplier_result = audit_supplier_record(supplier)
    integrity = audit_evidence_manifest(manifest, private_root)
    segregation = audit_role_segregation(manifest)
    records = manifest["records"]
    roles = [r["role"] for r in records]
    missing_roles = sorted(REQUIRED_ROLES - set(roles))
    duplicate_roles = sorted({role for role in roles if roles.count(role) > 1})
    expected_model = supplier.get("product_model")
    expected_revision = supplier.get("document_revision")
    mismatched = []
    for r in records:
        if r.get("product_model") != expected_model or r.get("document_revision") != expected_revision:
            mismatched.append(r["id"])
    reasons = []
    if not supplier_result["review_ready"]:
        reasons.append("supplier_metadata_not_review_ready")
    if not integrity["all_files_hash_verified"]:
        reasons.append("evidence_bytes_not_verified")
    if not segregation["role_segregation_complete"]:
        reasons.extend(segregation["rejection_reasons"])
    if missing_roles:
        reasons.append("missing_evidence_roles")
    if duplicate_roles:
        reasons.append("duplicate_evidence_roles")
    if mismatched:
        reasons.append("evidence_supplier_revision_binding_mismatch")
    return {
        "schema_version": "oem.ptx.f2l1.cross_evidence.v1",
        "metadata_complete": supplier_result["review_ready"],
        "byte_integrity_complete": integrity["all_files_hash_verified"],
        "role_segregation": segregation,
        "missing_roles": missing_roles,
        "duplicate_roles": duplicate_roles,
        "binding_mismatches": mismatched,
        "rejection_reasons": sorted(reasons),
        "ready_for_external_authentication_review": not reasons,
        "manufacturer_authenticated": False,
        "certified_design": False,
        "native_lca_accepted": False,
        "complete_station_bom": False,
        "f2_gate_passed": False,
        "l1_gate_passed": False,
    }
