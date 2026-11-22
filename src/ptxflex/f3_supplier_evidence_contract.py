"""F3 independent documentary evidence contract (NOT a supplier certificate).

A syntactically complete evidence bundle is only ready for human verification.
It cannot establish 2023 availability, industrial performance, or LCA eligibility.
No licensed evidence documents are embedded or redistributed.
"""
from __future__ import annotations

import hashlib
import re
from datetime import date
from urllib.parse import urlparse

FIELDS = ("supplier_legal_name", "facility_or_delivery_node", "document_title",
          "issuer", "publication_date", "source_url", "source_sha256",
          "page_or_table_locator", "pressure_basis", "pressure_bar_absolute",
          "hydrogen_purity_mole_fraction", "capacity_kg_per_hour",
          "ramp_kg_per_hour_per_hour", "valid_from", "valid_until",
          "geographic_scope", "delivery_mode", "license_or_access_basis")
SHA = re.compile(r"^[0-9a-f]{64}$")


class EvidenceContractError(ValueError):
    """Evidence cannot be accepted as even a review-ready documentary record."""


def check_documentary_bundle(bundle):
    """Check completeness, ranges, date ordering, and provenance; NEVER certify supplier."""
    if not isinstance(bundle, dict) or set(bundle) != set(FIELDS):
        raise EvidenceContractError("missing or unexpected evidence fields")
    for k in FIELDS:
        if k not in ("pressure_bar_absolute", "hydrogen_purity_mole_fraction",
                     "capacity_kg_per_hour", "ramp_kg_per_hour_per_hour"):
            if not isinstance(bundle[k], str) or not bundle[k].strip():
                raise EvidenceContractError("missing documentary field: " + k)
    if not SHA.fullmatch(bundle["source_sha256"]):
        raise EvidenceContractError("source SHA-256 must be lowercase hexadecimal")
    u = urlparse(bundle["source_url"])
    if u.scheme != "https" or not u.netloc or u.username or u.password:
        raise EvidenceContractError("source must have a resolvable HTTPS locator")
    if bundle["pressure_basis"] != "absolute_bar":
        raise EvidenceContractError("pressure gauge/absolute ambiguity")
    for k in ("pressure_bar_absolute", "hydrogen_purity_mole_fraction",
              "capacity_kg_per_hour", "ramp_kg_per_hour_per_hour"):
        v = bundle[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise EvidenceContractError("invalid numeric evidence: " + k)
        import math
        if not math.isfinite(v):
            raise EvidenceContractError("nonfinite evidence: " + k)
    if bundle["pressure_bar_absolute"] <= 0 or bundle["capacity_kg_per_hour"] <= 0:
        raise EvidenceContractError("invalid pressure or capacity")
    if not 0 < bundle["hydrogen_purity_mole_fraction"] <= 1:
        raise EvidenceContractError("invalid purity")
    if bundle["ramp_kg_per_hour_per_hour"] < 0:
        raise EvidenceContractError("invalid ramp")
    try:
        published = date.fromisoformat(bundle["publication_date"])
        start = date.fromisoformat(bundle["valid_from"])
        end = date.fromisoformat(bundle["valid_until"])
    except ValueError as e:
        raise EvidenceContractError("invalid ISO calendar date") from e
    if not start <= end or published > end:
        raise EvidenceContractError("inconsistent document and service dates")
    return {
        "schema_version": "oem.ptx.f3.supplier_evidence_review.v0.1",
        "documentary_fields_complete": True,
        "source_hash_format_valid_only": True,
        "source_bytes_independently_authenticated": False,
        "issuer_and_specification_independently_verified": False,
        "hourly_2023_availability_verified": False,
        "pressure_purity_delivery_physically_verified": False,
        "installed_transport_and_compression_verified": False,
        "qualified_for_lca_tea_or_matched_service": False,
        "human_review_required": True,
        "document_sha256_claim": bundle["source_sha256"],
        "document_title": bundle["document_title"],
        "service_period": [start.isoformat(), end.isoformat()],
    }
