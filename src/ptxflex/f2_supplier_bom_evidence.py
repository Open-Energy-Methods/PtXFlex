"""Conservative admission of supplier evidence for F2/L1 station completeness.

This is an evidence gate, NOT a pressure-vessel design, procurement approval or LCA.
No external supplier data are bundled.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from math import isfinite
from urllib.parse import urlparse
from ptxflex.f2_supplier_provenance import check_supplier_provenance

REQUIRED_CATEGORIES = frozenset({
    "pressure_vessels", "vessel_supports", "manifolds", "isolation_valves",
    "pressure_relief", "instrumentation", "compressor", "compressor_motor",
    "intercooling", "aftercooling", "gas_drying_purity", "pipework",
    "electrical_controls", "safety_detection", "venting", "civil_foundations",
    "installation", "maintenance_replacements", "end_of_life",
})

def audit_supplier_bom(records: Mapping[str, Mapping], *, site_id: str,
                       design_basis_id: str) -> dict:
    """Return fail-closed findings. A nonempty findings list blocks full F2/L1.

    Each category requires traceable dated supplier evidence, quantities, units,
    design-basis compatibility and installed cost. Manufacturing inventory is
    separately gated and never inferred from empty hardware mass.
    """
    findings = []
    if not site_id.strip() or not design_basis_id.strip():
        findings.append("missing named site or design basis")
    for name in sorted(REQUIRED_CATEGORIES):
        row = records.get(name)
        if not isinstance(row, Mapping):
            findings.append(f"{name}: missing supplier record")
            continue
        if row.get("site_id") != site_id or row.get("design_basis_id") != design_basis_id:
            findings.append(f"{name}: incompatible site/design basis")
        findings.extend(f"{name}: {issue}" for issue in check_supplier_provenance(row))
        source = row.get("supplier_source_url")
        parsed = urlparse(source) if isinstance(source, str) else None
        if not parsed or parsed.scheme != "https" or not parsed.netloc:
            findings.append(f"{name}: missing HTTPS supplier source")
        try:
            date.fromisoformat(row["source_date"])
        except (KeyError, TypeError, ValueError):
            findings.append(f"{name}: invalid/missing source date")
        for field in ("quantity", "installed_cost"):
            value = row.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value <= 0:
                findings.append(f"{name}: unknown/nonpositive {field}")
        if not isinstance(row.get("quantity_unit"), str) or not row["quantity_unit"].strip():
            findings.append(f"{name}: missing quantity unit")
        if not isinstance(row.get("cost_currency_year"), str) or not row["cost_currency_year"].strip():
            findings.append(f"{name}: missing cost currency/year")
        if row.get("pressure_qualified") is not True:
            findings.append(f"{name}: pressure/service qualification unverified")
        if row.get("manufacturing_inventory_verified") is not True:
            findings.append(f"{name}: native compatible manufacturing inventory unverified")
        if row.get("independent_review") is not True:
            findings.append(f"{name}: independent review missing")
    extra = set(records) - REQUIRED_CATEGORIES
    if extra:
        findings.append("unrecognized categories: " + ", ".join(sorted(extra)))
    return {"gate": "F2_L1_SUPPLIER_EVIDENCE_SCREEN",
            "passed": not findings, "findings": findings,
            "categories_required": len(REQUIRED_CATEGORIES),
            "claim_scope": "documentary completeness only; no certification, plant validation or LCIA"}
