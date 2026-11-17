"""F3 independent release-admissibility gate: mathematical screening is not supplier evidence.

This module deliberately cannot infer a physically qualified supplier from a
passing 8760-hour offer or from complete documentary metadata.
"""
from __future__ import annotations


class SupplierReleaseError(ValueError):
    pass


REQUIRED_EXTERNAL_REVIEWS = (
    "source_bytes_authenticated",
    "issuer_and_specification_verified",
    "site_and_delivery_node_verified",
    "service_period_and_hourly_availability_verified",
    "pressure_purity_and_peak_flow_verified",
    "transport_compression_and_buffer_verified",
    "upstream_lci_and_installed_bom_verified",
    "independent_reviewer_signed",
)


def assess_supplier_release(offer_screen, documentary_screen, external_reviews):
    """Evaluate evidence classes separately; do not create or assert review evidence.

    External review entries must be explicit booleans, not truthy strings.
    The caller must separately retain auditable source records for each review.
    """
    if not isinstance(offer_screen, dict) or not isinstance(documentary_screen, dict):
        raise SupplierReleaseError("both mathematical and documentary screens required")
    if not isinstance(external_reviews, dict) or set(external_reviews) != set(REQUIRED_EXTERNAL_REVIEWS):
        raise SupplierReleaseError("complete explicit external-review checklist required")
    if any(type(v) is not bool for v in external_reviews.values()):
        raise SupplierReleaseError("review flags must be booleans")
    if offer_screen.get("full_plant_science_gate_passed") is True:
        raise SupplierReleaseError("upstream offer cannot self-certify full plant")
    if documentary_screen.get("qualified_for_lca_tea_or_matched_service") is True:
        raise SupplierReleaseError("documentary metadata cannot self-certify supplier")
    mathematical = offer_screen.get("fixed_trace_supplier_offer_screen_pass") is True
    documentary = documentary_screen.get("documentary_fields_complete") is True
    all_reviewed = all(external_reviews.values())
    return {
        "schema_version": "oem.ptx.f3.release_admissibility.v0.1",
        "mathematical_offer_screen_passed": mathematical,
        "documentary_metadata_complete": documentary,
        "independent_review_flags_complete": all_reviewed,
        "supplier_release_admissible": mathematical and documentary and all_reviewed,
        "review_flags_are_not_source_authentication": True,
        "requires_external_audit_trail_before_release": True,
        "full_programme_v1_gate_passed": False,
    }
