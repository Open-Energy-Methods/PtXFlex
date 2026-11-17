import hashlib
import json
from pathlib import Path
import pytest

from ptxflex.model import (solve, validate, audit_solution,
                            H2_PER_KG_MEOH, CO2_PER_KG_MEOH)

CASE = Path(__file__).resolve().parents[1] / "examples" / "illustrative_methanol.json"

@pytest.fixture
def scenario():
    return json.loads(CASE.read_text(encoding="utf-8"))

def test_stoichiometry():
    assert H2_PER_KG_MEOH == pytest.approx(0.18876, rel=.001)
    assert CO2_PER_KG_MEOH == pytest.approx(1.3736, rel=.001)

def test_solution_feasible_and_mass_energy_checked(scenario):
    out = solve(scenario)
    assert audit_solution(scenario, out)
    assert out["methanol_total_kg"] == pytest.approx(400, abs=1e-5)
    assert out["solver_status"] == 0
    assert out["operational_gwp_kgco2e"] >= 0
    assert sum(row["h2_to_methanol_kg"] for row in out["hours"]) == pytest.approx(400*H2_PER_KG_MEOH)

def test_emissions_limit_changes_dispatch(scenario):
    base = solve(scenario)
    capped = solve(scenario, emissions_cap_kgco2e=200)
    assert audit_solution(scenario, capped)
    assert capped["operational_gwp_kgco2e"] <= 200 + 1e-5
    assert capped["operational_gwp_kgco2e"] < base["operational_gwp_kgco2e"]
    assert sum(h["grid_used_mwh"] for h in capped["hours"]) < sum(h["grid_used_mwh"] for h in base["hours"])

def test_infeasible_impact_limit_is_reported(scenario):
    with pytest.raises(ValueError, match="MILP failed"):
        solve(scenario, emissions_cap_kgco2e=0)

def test_invalid_data_rejected(scenario):
    scenario["hours"][0]["wind_available_mwh"] = -1
    with pytest.raises(ValueError):
        validate(scenario)

def test_non_synthetic_not_misrepresented(scenario):
    scenario["evidence"]["kind"] = "pynexus_frozen"
    with pytest.raises(ValueError):
        solve(scenario)

def test_footprint_is_not_a_lca(scenario):
    assert "NOT process/LCA validation" in solve(scenario)["claim"]


def test_solver_result_has_reproducible_input_hash(scenario):
    expected = hashlib.sha256(json.dumps(scenario, sort_keys=True).encode()).hexdigest()
    first = solve(scenario)
    assert first["input_sha256"] == expected
    assert solve(scenario)["input_sha256"] == first["input_sha256"]
