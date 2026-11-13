"""Negative/scientific lower-bound interpretation for F3 source LP.

Relaxing all original hourly binary decisions can only REDUCE the minimum
additional hydrogen shortfall; it cannot prove a plant is operationally
feasible. Genuine 2023 results must still use immutable original source.
"""
import pytest
pytest.importorskip("CoolProp")
from ptxflex.f3_pressure_adequacy import minimum_new_shortfall
from ptxflex.pressure_storage_duty import build_screened_pressure_duty


def params():
    return {
      "capacity_kg":5000.,"initial_kg":2500.,"terminal_kg":2500.,
      "charge_max_kg_h":2200.,"discharge_max_kg_h":2200.,
      "loss_fraction_per_hour":.0001,"rated_mw":125.,
      "min_load_fraction":.1,"max_load_fraction":1.,
      "ramp_mw_h":50.,"grid_max_mw":50.,
      "h2_coefficient_kg_mwh":20.,"delivery_limit_kg_h":7200.,
      "source_bafu_PEM_pressure_bar":30.,
      "source_pipeline_min_delivery_pressure_bar":20.
    }


def test_lp_is_only_a_mathematical_lower_bound_on_integer_physical_shortfall():
    p=params()
    duty=build_screened_pressure_duty("I_200bar",5000.)
    common=dict(wind=[0,0,0,0],price=[10,20,15,10],target=[2000]*4,
                params=p,duty=duty,limit_seconds=30)
    LP=minimum_new_shortfall(**common,continuous_relaxation_only=True)
    MILP=minimum_new_shortfall(**common)
    assert LP["LP_relaxation_of_integer_min_shortfall"]
    assert LP["integer_commitment_and_storage_exclusivity_not_enforced"]
    assert LP["not_a_physically_executable_dispatch_solution"]
    assert LP["lower_bound_on_true_MILP_additional_shortfall_kg"]<=MILP["additional_shortfall_kg"]+1e-5
    assert LP["solver_optimal"]
    assert LP["LP_pressure_EOS_bounds"]["EOS_hourly_mass_bounds_imply_pressure_limits"]
    assert max(LP["LP_source_equation_residuals"].values())<2e-4
    assert MILP["solver_optimal"]


def test_source_bounded_LP_cannot_claim_a_full_site_GWP_or_service():
    p=params()
    duty=build_screened_pressure_duty("I_200bar",5000.)
    r=minimum_new_shortfall([100,100],[10,10],[1000,1000],
                            p,duty,continuous_relaxation_only=True)
    assert r["screening_only_no_full_contract_or_LCA"]
    assert r["LP_relaxation_of_integer_min_shortfall"]
    assert r["not_a_physically_executable_dispatch_solution"]
