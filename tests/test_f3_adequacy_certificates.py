"""Negative tests for independently certified Stage A shortage bounds.

Mathematical fixtures only; do not represent measured or solved 2023 cases.
"""
import copy
import pytest
from ptxflex.f3_adequacy_certificates import (
    certify_stage_a, InvalidAdequacyCertificate, SOURCE_E, SOURCE_ES,
    SOURCE_TARGET_KG, FULL_DEMAND_KG,
)


def fixture():
    target = SOURCE_TARGET_KG
    physical = {"EOS_hourly_mass_bounds_imply_pressure_limits": True}
    checks = {"electrical": 0.0, "H2_delivered": 1e-7, "storage": 1e-7}
    e = {
        "status": "FEASIBLE_INCUMBENT_NOT_PROVEN_MINIMUM",
        "solver_optimal": False, "solver_gap": 0.2,
        "solver_best_bound_unserved_kg": 7000.0,
        "additional_shortfall_kg": 10000.0,
        "achievable_annual_h2_under_screen_kg": target - 10000.0,
        "shortfall_hour_count": 15,
        "audit": {"independent_max_physical_residuals": checks, "pressure_EOS_bounds": physical},
    }
    es = copy.deepcopy(e)
    es.update(status="VERIFIED_STAGE_A_MIN_ADDITIONAL_SOURCE_SHORTFALL",
              solver_optimal=True, solver_gap=0.0, solver_best_bound_unserved_kg=0.0,
              additional_shortfall_kg=0.0, achievable_annual_h2_under_screen_kg=target,
              shortfall_hour_count=0)
    return {
        "source_E_sha256": SOURCE_E, "source_EplusS_sha256": SOURCE_ES,
        "source_electricity_NL_A44_and_wind_ERA5_real_hydrogen_modelled": True,
        "source_hourly_E_delivered_target_kg": target,
        "original_full_2023_H2_demand_kg": FULL_DEMAND_KG,
        "plant_validation": False, "complete_installation_BOM_LCA_and_TEA": False,
        "scenario_results": {"max_inventory": {"E": e, "E_plus_S": es}},
    }


def test_certifies_interval_without_mislabeling_feasible_incumbent():
    out = certify_stage_a(fixture())
    e = out["cases"]["max_inventory"]["E"]
    es = out["cases"]["max_inventory"]["E_plus_S"]
    assert e["status"] == "BOUNDED_INCUMBENT_MINIMUM_UNPROVEN"
    assert e["shortfall_lower_bound_kg"] == 7000
    assert e["shortfall_upper_bound_kg"] == 10000
    assert e["shortfall_optimality_interval_width_kg"] == 3000
    assert e["positive_minimum_shortfall_proven"]
    assert e["full_original_demand_shortfall_upper_bound_kg"] > e["full_original_demand_shortfall_lower_bound_kg"]
    assert es["status"] == "PROVEN_MINIMUM"
    assert es["shortfall_lower_bound_kg"] == es["shortfall_upper_bound_kg"] == 0
    assert out["not_a_matched_service_cost_or_environmental_comparison"]
    assert e["annual_operating_cost_eur"] is None
    assert es["native_full_system_GWP_kgCO2e"] is None


@pytest.mark.parametrize("mutation", [
    lambda d: d.update(source_E_sha256="0"*64),
    lambda d: d.update(source_hourly_E_delivered_target_kg=15_000_000),
    lambda d: d.update(plant_validation=True),
    lambda d: d["scenario_results"]["max_inventory"]["E"].update(additional_shortfall_kg=1),
    lambda d: d["scenario_results"]["max_inventory"]["E"].update(solver_best_bound_unserved_kg=20000),
    lambda d: d["scenario_results"]["max_inventory"]["E"].update(solver_optimal=True),
    lambda d: d["scenario_results"]["max_inventory"]["E"]["audit"]["independent_max_physical_residuals"].update(storage=1.0),
    lambda d: d["scenario_results"]["max_inventory"]["E"]["audit"]["pressure_EOS_bounds"].update(EOS_hourly_mass_bounds_imply_pressure_limits=False),
    lambda d: d["scenario_results"]["max_inventory"]["E"].update(solver_gap=float("nan")),
    lambda d: d["scenario_results"]["max_inventory"]["E"].update(status="VERIFIED_LP_OPTIMISTIC_LOWER_BOUND_NOT_OPERABLE"),
])
def test_invalid_source_physics_or_optimality_cannot_be_certified(mutation):
    case = fixture()
    mutation(case)
    with pytest.raises(InvalidAdequacyCertificate):
        certify_stage_a(case)


def test_missing_solver_dual_does_not_invent_positive_minimum():
    case = fixture()
    case["scenario_results"]["max_inventory"]["E"]["solver_best_bound_unserved_kg"] = None
    e = certify_stage_a(case)["cases"]["max_inventory"]["E"]
    assert e["shortfall_lower_bound_kg"] == 0
    assert not e["positive_minimum_shortfall_proven"]
    assert e["lower_bound_basis"] == "nonnegative_slack_only"


def test_partial_matrix_does_not_invent_unrun_second_scenario():
    case = fixture()
    del case["scenario_results"]["max_inventory"]["E_plus_S"]
    out = certify_stage_a(case)
    assert list(out["cases"]["max_inventory"]) == ["E"]


def test_uncertified_solver_case_does_not_claim_a_shortage_bound():
    case = fixture()
    case["scenario_results"]["max_inventory"]["E"] = {
        "status": "NOT_CERTIFIED", "reason": "No verified feasible Stage A incumbent"}
    e = certify_stage_a(case)["cases"]["max_inventory"]["E"]
    assert e["shortfall_lower_bound_kg"] is None
    assert e["shortfall_upper_bound_kg"] is None
