"""F3-D weak-wind solver scientific proof-direction controls.

LP relaxation removes binary restrictions, never original mass/energy/
storage/ramp constraints. LP infeasibility => original MILP infeasible
under precisely same mathematical model/numerical tolerance. LP feasible
is ONLY a necessary (not sufficient) condition for MILP feasibility.
Do not call fractional on/off or simultaneous charge/discharge physical.
Synthetic tiny tests are not source PyNEXUS historical case.
"""
import numpy as np
import pytest

from ptxflex.f3_matched_ideal_benchmark import solve_ideal_storage
from ptxflex.f3d_weak_wind_lp_feasibility import SCHEMA
from ptxflex.f3d_2023_source_hourly_counterfactuals import STAGEA,SUPPORTED


def model():
    return {
        "capacity_kg":10000.,"initial_kg":5000.,"terminal_kg":5000.,
        "charge_max_kg_h":2200.,"discharge_max_kg_h":2200.,
        "loss_fraction_per_hour":0.,
        "rated_mw":125.,"min_load_fraction":.1,"max_load_fraction":1.,
        "ramp_mw_h":50.,"grid_max_mw":50.,
        "h2_coefficient_kg_mwh":20.,"delivery_limit_kg_h":7200.,
        "source_bafu_PEM_pressure_bar":30.,
        "source_pipeline_min_delivery_pressure_bar":20.
    }


def test_costless_relaxed_LP_source_constraints_report_feasible_but_never_MILP_plant():
    r=solve_ideal_storage([100.,100.,100.],[50.,-4.,90.],
                          [1000.,1000.,1000.],model(),time_limit_s=25.,
                          diagnostic_only_lp_relaxation=True)
    assert r["schema_version"]=="ptxflex.f3d_identical_model_binary_relaxed_h2_feasibility_diagnostic.v1"
    assert r["solver_status_code"]==0
    assert r["LP_model_has_accepted_feasible_vector"]
    assert not r["LP_relaxation_infeasible_as_reported_by_HiGHS"]
    assert not r["MILP_infeasibility_supported_if_LP_status_2"]
    assert not r["MILP_feasible_conclusion_permitted_from_LP_status_0"]
    assert r["LP_relaxed_binary_primal_NOT_a_valid_integer_dispatch"]
    assert r["LP_feasibility_objective_zero_ignores_2023_wholesale_cost"]
    assert r["all_original_hourly_electricity_H2_storage_pressure_compressor_constraints_preserved"]
    assert r["source_H2_required_annual_kg"]==3000.
    assert r["source_model_pressure_screened"] is False
    assert not r["actual_site_operational_infeasibility_certified"]


def test_lp_relaxation_infeasible_when_total_source_electricity_far_below_exact_h2_required():
    # Two hours, each maximum 50 MW grid and zero wind, y=20 kg/MWh:
    # total maximum production <=2000 kg. Exactly 4000 kg delivered and
    # initial=final storage, no loss: impossible EVEN with fractional binaries.
    r=solve_ideal_storage([0.,0.],[10.,10.],[2000.,2000.],
                          model(),time_limit_s=25.,
                          diagnostic_only_lp_relaxation=True)
    assert r["schema_version"]=="ptxflex.f3d_identical_model_binary_relaxed_h2_feasibility_diagnostic.v1"
    assert r["solver_status_code"]==2, r["solver_status_message"]
    assert r["LP_model_has_accepted_feasible_vector"] is False
    assert r["LP_relaxation_infeasible_as_reported_by_HiGHS"]
    assert r["MILP_infeasibility_supported_if_LP_status_2"]
    assert not r["MILP_feasible_conclusion_permitted_from_LP_status_0"]
    assert r["source_H2_required_annual_kg"]==4000.
    assert r["actual_site_operational_infeasibility_certified"] is False


def test_lp_zero_objective_cannot_change_original_costed_integer_solution():
    a=solve_ideal_storage([95.]*4,[100.,20.,-5.,80.],[1000.]*4,
                          model(),time_limit_s=30.)
    b=solve_ideal_storage([95.]*4,[100.,20.,-5.,80.],[1000.]*4,
                          model(),time_limit_s=30.,
                          diagnostic_only_lp_relaxation=True)
    assert a["solver_optimal"] is True
    assert a["derived_audit"]["annual_service_h2_kg"]==4000.
    assert a["hourly_solved_states"]!=b
    assert b["LP_model_has_accepted_feasible_vector"]
    assert "derived_audit" not in b
    assert "hourly_solved_states" not in b


def test_original_2023_f3d_weak_wind_only_is_targeted_not_actual_other_year():
    assert "wind_090_multiplier" in SUPPORTED
    assert set(STAGEA)=={"max_inventory","usable_service"}
    assert all(len(values[0])==len(values[1])==64 for values in STAGEA.values())
