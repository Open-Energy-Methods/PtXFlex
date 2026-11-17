"""Fail-closed F2/L1 supplier-to-native-provider evidence screening.

A review-ready record is NOT a certified design, accepted LCA or complete BOM.
No private inventory, impact factor, plant measurement or cost is supplied.
"""
import math
from collections.abc import Mapping

REQUIRED = ("manufacturer", "product_model", "document_url", "document_revision",
 "document_date", "equipment_scope", "pressure_basis", "rated_pressure_bar",
 "hydrogen_service", "quantity", "quantity_unit", "material_grade",
 "manufacturing_process", "manufacturing_geography", "provider_database",
 "provider_version", "provider_process", "provider_reference_unit",
 "provider_reference_flow", "provider_mapping_rationale", "reviewer")

def audit_supplier_record(record):
    if not isinstance(record, Mapping):
        raise TypeError("record must be a mapping")
    missing = sorted(k for k in REQUIRED if k not in record or record[k] is None
                     or isinstance(record[k], str) and not record[k].strip())
    reasons = []
    if record.get("pressure_basis") not in ("absolute", "gauge"):
        reasons.append("pressure_basis_not_explicit")
    for key in ("rated_pressure_bar", "quantity"):
        value = record.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            reasons.append(key + "_not_positive_finite")
    if record.get("provider_database") == "BAFU:2026" and record.get("provider_version") != "v1.1":
        reasons.append("BAFU_version_mismatch")
    if record.get("equipment_scope") == "stationary_typeI_steel_vessel":
        if record.get("provider_reference_unit") == "kg_H2_capacity":
            reasons.append("hydrogen_capacity_not_steel_manufacturing_mass")
        if "composite" in str(record.get("provider_process", "")).lower():
            reasons.append("vehicle_composite_not_stationary_typeI_steel")
    if record.get("document_url") and not str(record["document_url"]).startswith("https://"):
        reasons.append("source_url_not_https")
    return {"review_ready": not (missing or reasons), "missing_fields": missing,
            "rejection_reasons": sorted(reasons), "certified_design": False,
            "native_lca_accepted": False, "complete_station_bom": False}
