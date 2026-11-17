"""F2/L1 fail-closed engineering handoff: evidence is not equipment qualification.

This checker only establishes whether a *candidate* BOM is sufficiently
specified for independent engineering review. It never approves a design,
conformity, site, native LCA, or v1.0 release.
"""
from __future__ import annotations

import hashlib
import math
import re

COMPONENTS = (
    "pressure_vessels", "compressor", "aftercooler", "manifold_piping",
    "isolation_and_control_valves", "pressure_relief_and_vent",
    "instrumentation", "supports_and_foundations",
    "electrical_and_motor", "hydrogen_leak_detection",
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REVIEW_STATES = {"unreviewed", "reviewed_with_reservations", "independently_accepted"}


class HandoffError(ValueError):
    pass


def _positive_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HandoffError(f"{name}: numeric value required")
    if not math.isfinite(value) or value <= 0:
        raise HandoffError(f"{name}: positive finite value required")
    return float(value)


def _source(record, name):
    if not isinstance(record, dict):
        raise HandoffError(f"{name}: source record missing")
    if not isinstance(record.get("locator"), str) or not record["locator"].strip():
        raise HandoffError(f"{name}: source locator missing")
    if not isinstance(record.get("sha256"), str) or not SHA256.fullmatch(record["sha256"]):
        raise HandoffError(f"{name}: source SHA-256 missing/invalid")
    if record.get("bytes_authenticated") is not True:
        raise HandoffError(f"{name}: referenced source bytes not independently authenticated")
    if record.get("review_state") not in REVIEW_STATES:
        raise HandoffError(f"{name}: review state invalid")
    return record["review_state"] == "independently_accepted"


def screen_f2_l1_handoff(record):
    """Return explicit review readiness, not physical approval.

    Every mandatory component must have mass, quantity, pressure boundary
    and source. Manufacturer traceability is required for a *review-ready*
    handoff. Screening data and published representative vessel values are
    not manufacturer certificates. A missing component is never zero mass.
    """
    if not isinstance(record, dict):
        raise HandoffError("handoff must be an object")
    if record.get("capacity_semantics") not in ("max_inventory", "usable_service"):
        raise HandoffError("capacity semantics missing")
    if record.get("pressure_basis") != "absolute":
        raise HandoffError("pressure basis must explicitly be absolute")
    pmin = _positive_number(record.get("minimum_delivery_bar_absolute"), "minimum pressure")
    pmax = _positive_number(record.get("maximum_storage_bar_absolute"), "maximum pressure")
    if pmin >= pmax:
        raise HandoffError("pressure window invalid")
    _positive_number(record.get("gas_temperature_min_k"), "temperature min")
    _positive_number(record.get("gas_temperature_max_k"), "temperature max")
    if record["gas_temperature_min_k"] > record["gas_temperature_max_k"]:
        raise HandoffError("temperature window inverted")
    _positive_number(record.get("withdrawable_h2_kg"), "working hydrogen")
    components = record.get("components")
    if not isinstance(components, dict):
        raise HandoffError("component inventory missing")
    if set(components) != set(COMPONENTS):
        raise HandoffError("component inventory incomplete or unknown components")
    total = 0.0
    outstanding = []
    for key in COMPONENTS:
        item = components[key]
        if not isinstance(item, dict):
            raise HandoffError(f"{key}: component record missing")
        quantity = _positive_number(item.get("quantity"), f"{key} quantity")
        if not quantity.is_integer():
            raise HandoffError(f"{key}: count must be an integer")
        mass = _positive_number(item.get("unit_empty_mass_kg"), f"{key} mass")
        rated = _positive_number(item.get("rated_pressure_bar_absolute"), f"{key} pressure")
        # Storage vessel MAWP must bound the stated maximum gas pressure.
        # Other equipment may occupy independently regulated lower-pressure sections;
        # their segment design pressures require a separate P&ID review.
        if key == "pressure_vessels" and rated < pmax:
            raise HandoffError("pressure_vessels: rated pressure below maximum storage pressure")
        if not isinstance(item.get("manufacturer_part"), str) or not item["manufacturer_part"].strip():
            outstanding.append(f"{key}: manufacturer part not identified")
        if not _source(item.get("source"), key):
            outstanding.append(f"{key}: independent source review outstanding")
        total += quantity * mass
    if not math.isfinite(total):
        raise HandoffError("aggregate mass overflow")
    if not _source(record.get("site_pressure_and_delivery_source"), "site pressure"):
        outstanding.append("site pressure and delivery: independent review outstanding")
    if record.get("cooling_duty_kwh_per_kg") is None:
        outstanding.append("cooling electricity unquantified")
    else:
        value = record["cooling_duty_kwh_per_kg"]
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
            raise HandoffError("cooling duty must be finite and nonnegative")
    for field in ("fatigue_and_embrittlement_review", "relief_and_hazard_review",
                  "site_layout_review", "vendor_compressor_map_review"):
        if record.get(field) is not True:
            outstanding.append(field + " outstanding")
    return {
        "schema": "oem.ptx.f2_l1_review_readiness.v1",
        "equipment_mass_kg_from_explicit_items": total,
        "component_count": len(COMPONENTS),
        "review_ready": not outstanding,
        "outstanding": outstanding,
        "design_certified": False,
        "native_bafu_lcia_complete": False,
        "industrial_validation": False,
        "v1_release_approved": False,
    }
