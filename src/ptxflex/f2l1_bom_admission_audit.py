"""Independent F2/L1 BOM admission audit; never computes an LCA.

This gate validates evidence completeness, not engineering design. Missing quantities
are unknown (None), never zero. An empty vessel reference is not a qualified
installed hydrogen station.
"""
from __future__ import annotations
import json
from pathlib import Path

REQUIRED_FIELDS = ("line_id", "quantity", "empty_mass_kg", "manufacturer_quote_eur",
                   "evidence_class", "not_coupled_as_complete_native_BAFU_inventory")

def audit_bom(document: dict) -> dict:
    if not isinstance(document, dict) or not isinstance(document.get("modes"), dict):
        raise ValueError("expected source BOM document with modes")
    findings = {}
    for mode, data in document["modes"].items():
        rows = data.get("required_incremental_system_foreground_BOM")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{mode}: missing BOM ledger")
        ids = [row.get("line_id") for row in rows]
        if any(not isinstance(x, str) or not x for x in ids) or len(set(ids)) != len(ids):
            raise ValueError(f"{mode}: missing or duplicate line identifiers")
        if any(not all(k in row for k in REQUIRED_FIELDS) for row in rows):
            raise ValueError(f"{mode}: missing evidence fields")
        unknown = [row["line_id"] for row in rows if row["quantity"] is None or row["empty_mass_kg"] is None]
        invalid = [row["line_id"] for row in rows if
                   (row["quantity"] is not None and (isinstance(row["quantity"], bool) or not isinstance(row["quantity"], (int, float)) or row["quantity"] < 0))
                   or (row["empty_mass_kg"] is not None and (isinstance(row["empty_mass_kg"], bool) or not isinstance(row["empty_mass_kg"], (int, float)) or row["empty_mass_kg"] < 0))]
        if invalid:
            raise ValueError(f"{mode}: invalid nonnegative mass/quantity: {invalid}")
        qualified = all(row["quantity"] is not None and row["empty_mass_kg"] is not None
                        and row["manufacturer_quote_eur"] is not None
                        and row["not_coupled_as_complete_native_BAFU_inventory"] is False
                        for row in rows)
        # An independent BOM audit cannot establish native BAFU supplier compatibility,
        # physical certification or site acceptance by itself.
        findings[mode] = {
            "line_count": len(rows), "unquantified_line_ids": unknown,
            "all_lines_quantified_and_linked": qualified,
            "complete_native_lca_admitted": False,
            "certified_installed_station_admitted": False,
        }
    return {"schema_version": "oem.ptx.f2l1.bom_admission_audit.v1",
            "source_2023_modelled_h2_is_plant_measurement": False,
            "modes": findings, "full_v1_gate_passed": False}

def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("ledger", type=Path)
    args = p.parse_args()
    print(json.dumps(audit_bom(json.loads(args.ledger.read_text(encoding="utf-8"))), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
