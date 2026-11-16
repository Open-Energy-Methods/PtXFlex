"""F2/L1 evidence audit: actual ledger plus adversarial synthetic mutations."""
import copy
import json
from pathlib import Path
import pytest
from ptxflex.f2l1_bom_admission_audit import audit_bom

LEDGER = Path(__file__).resolve().parents[1] / "data/results/F2_L1_2023_source_incremental_20t_to_40t_stationary_typeI_200bar_BOM_SCOPE_NOT_complete_native_LCI.json"

@pytest.fixture
def source():
    return json.loads(LEDGER.read_text(encoding="utf-8"))

def test_source_is_not_full_lca(source):
    result = audit_bom(source)
    assert result["full_v1_gate_passed"] is False
    assert set(result["modes"]) == {"max_inventory", "usable_service"}
    for case in result["modes"].values():
        assert case["line_count"] == 19
        assert len(case["unquantified_line_ids"]) >= 18
        assert case["complete_native_lca_admitted"] is False
        assert case["certified_installed_station_admitted"] is False

@pytest.mark.parametrize("fault", ["duplicate", "missing_field", "negative_mass", "negative_count", "bool_count"])
def test_malformed_foreground_rejected(source, fault):
    rows = source["modes"]["max_inventory"]["required_incremental_system_foreground_BOM"]
    if fault == "duplicate":
        rows[1]["line_id"] = rows[0]["line_id"]
    elif fault == "missing_field":
        del rows[1]["evidence_class"]
    elif fault == "negative_mass":
        rows[0]["empty_mass_kg"] = -1
    elif fault == "negative_count":
        rows[0]["quantity"] = -1
    else:
        rows[0]["quantity"] = True
    with pytest.raises(ValueError):
        audit_bom(source)

def test_zero_is_not_unknown_and_not_certification(source):
    rows = source["modes"]["max_inventory"]["required_incremental_system_foreground_BOM"]
    rows[1]["quantity"] = 0
    rows[1]["empty_mass_kg"] = 0
    result = audit_bom(source)["modes"]["max_inventory"]
    assert rows[1]["line_id"] not in result["unquantified_line_ids"]
    assert result["complete_native_lca_admitted"] is False

def test_no_fabricated_completion_even_if_synthetic_rows_filled(source):
    rows = source["modes"]["max_inventory"]["required_incremental_system_foreground_BOM"]
    for row in rows:
        row["quantity"] = 1
        row["empty_mass_kg"] = 1
        row["manufacturer_quote_eur"] = 1
        row["not_coupled_as_complete_native_BAFU_inventory"] = False
    result = audit_bom(source)["modes"]["max_inventory"]
    assert result["all_lines_quantified_and_linked"] is True
    assert result["complete_native_lca_admitted"] is False
    assert result["certified_installed_station_admitted"] is False
