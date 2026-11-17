"""Independent F2/L1 source-ledger consistency checks, not a certification or LCA.

Checks published-reference arithmetic and the two mutually distinct inventory
semantics without assuming that unreported equipment is zero.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label}: expected finite nonnegative number")
    try:
        x = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{label}: invalid decimal") from exc
    if not x.is_finite() or x < 0:
        raise ValueError(f"{label}: nonfinite or negative")
    return x

def verify_reference_ledger(document: dict) -> dict:
    """Reject arithmetic inconsistencies; never authorize native LCI admission."""
    modes = document.get("modes")
    if not isinstance(modes, dict) or set(modes) != {"max_inventory", "usable_service"}:
        raise ValueError("both named capacity semantics required")
    result = {}
    baseline_ids = None
    for mode, case in modes.items():
        rows = case.get("required_incremental_system_foreground_BOM")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{mode}: missing equipment ledger")
        ids = [r.get("line_id") for r in rows]
        if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
            raise ValueError(f"{mode}: duplicate/invalid IDs")
        if baseline_ids is None:
            baseline_ids = set(ids)
        elif set(ids) != baseline_ids:
            raise ValueError("different equipment category boundaries across semantics")
        vessel = [r for r in rows if r["line_id"] == "typeI_200bar_bare_reference_vessels"]
        if len(vessel) != 1:
            raise ValueError(f"{mode}: missing vessel reference")
        vessel = vessel[0]
        count = _number(vessel.get("quantity"), "vessel count")
        if count != count.to_integral_value():
            raise ValueError("fractional vessel count")
        unit_mass = _number(vessel.get("empty_vessel_reference_per_unit_kg"), "unit empty mass")
        total = _number(vessel.get("empty_mass_kg"), "total empty mass")
        if total != count * unit_mass:
            raise ValueError(f"{mode}: vessel count times unit mass mismatch")
        if total != _number(case.get("known_empty_reference_vessel_hardware_only_kg"), "case hardware"):
            raise ValueError(f"{mode}: case hardware inconsistent")
        sensitivity = case.get("incremental_only_research_sensitivity", {})
        if count != _number(sensitivity.get("net_additional_published_reference_vessel_count"), "increment count"):
            raise ValueError(f"{mode}: sensitivity count inconsistent")
        if total != _number(sensitivity.get("net_additional_published_empty_vessel_equipment_mass_kg"), "increment mass"):
            raise ValueError(f"{mode}: sensitivity mass inconsistent")
        unknown = []
        for row in rows:
            label = row["line_id"]
            for field in ("quantity", "empty_mass_kg", "manufacturer_quote_eur"):
                if field not in row:
                    raise ValueError(f"{label}: absent {field}")
                if row[field] is not None:
                    _number(row[field], f"{label}.{field}")
            if row["quantity"] is None or row["empty_mass_kg"] is None:
                unknown.append(label)
        if not unknown:
            raise ValueError("no independently qualified complete equipment BOM evidence")
        if case.get("complete_manufacturer_warrantied_typeI_bank_BOM") is not False:
            raise ValueError("unsupported complete manufacturer claim")
        if case.get("BAFU2026_v11_standalone_typeI_native_LCI_created") is not False:
            raise ValueError("unsupported native LCI claim")
        result[mode] = {"reference_vessel_count": int(count),
                        "reference_empty_hardware_kg": int(total),
                        "unknown_equipment_line_ids": unknown,
                        "certified_installed_station": False,
                        "native_BAFU_LCA": False}
    return {"schema_version": "oem.ptx.f2l1.reference_consistency.v1",
            "modes": result, "full_v1_gate_passed": False}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_reference_ledger(json.loads(args.ledger.read_text(encoding="utf-8"))),
                     indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
