"""Independent source-ledger invariants and adversarial mutation checks."""
import copy
import json
from pathlib import Path
import pytest
from ptxflex.f2l1_reference_consistency import verify_reference_ledger

LEDGER = Path(__file__).resolve().parents[1] / "data/results/F2_L1_2023_source_incremental_20t_to_40t_stationary_typeI_200bar_BOM_SCOPE_NOT_complete_native_LCI.json"

@pytest.fixture
def ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))

def test_real_source_reference_and_unresolved_scope(ledger):
    result = verify_reference_ledger(ledger)
    assert result["full_v1_gate_passed"] is False
    assert result["modes"]["max_inventory"]["reference_vessel_count"] == 802
    assert result["modes"]["usable_service"]["reference_vessel_count"] == 902
    for mode in result["modes"].values():
        assert len(mode["unknown_equipment_line_ids"]) >= 18
        assert mode["native_BAFU_LCA"] is False
        assert mode["certified_installed_station"] is False

@pytest.mark.parametrize("mutation", [
    "fractional", "nan", "infinite", "bool", "mass", "case_mass",
    "sensitivity_count", "sensitivity_mass", "negative_quote",
    "missing_category", "falsified_certification", "falsified_lci",
])
def test_reject_inconsistent_or_fabricated_evidence(ledger, mutation):
    case = ledger["modes"]["max_inventory"]
    rows = case["required_incremental_system_foreground_BOM"]
    vessel = next(x for x in rows if x["line_id"] == "typeI_200bar_bare_reference_vessels")
    if mutation == "fractional":
        vessel["quantity"] = 802.5
    elif mutation == "nan":
        vessel["empty_mass_kg"] = float("nan")
    elif mutation == "infinite":
        vessel["empty_mass_kg"] = float("inf")
    elif mutation == "bool":
        vessel["quantity"] = True
    elif mutation == "mass":
        vessel["empty_mass_kg"] += 1
    elif mutation == "case_mass":
        case["known_empty_reference_vessel_hardware_only_kg"] += 1
    elif mutation == "sensitivity_count":
        case["incremental_only_research_sensitivity"]["net_additional_published_reference_vessel_count"] += 1
    elif mutation == "sensitivity_mass":
        case["incremental_only_research_sensitivity"]["net_additional_published_empty_vessel_equipment_mass_kg"] += 1
    elif mutation == "negative_quote":
        vessel["manufacturer_quote_eur"] = -1
    elif mutation == "missing_category":
        rows.pop()
    elif mutation == "falsified_certification":
        case["complete_manufacturer_warrantied_typeI_bank_BOM"] = True
    else:
        case["BAFU2026_v11_standalone_typeI_native_LCI_created"] = True
    with pytest.raises(ValueError):
        verify_reference_ledger(ledger)
