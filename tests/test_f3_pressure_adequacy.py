"""F3 adequacy Stage A negative and conservation tests.

Test fixtures are deliberately synthetic mathematical small vectors; no test
output enters genuine 2023 scenario evidence.
"""
import math
import numpy as np
import pytest
pytest.importorskip("CoolProp")

from ptxflex.f3_pressure_adequacy import minimum_new_shortfall
from ptxflex.pressure_storage_duty import build_screened_pressure_duty
from ptxflex.f3_matched_ideal_benchmark import SourceLockedDispatchError


def params():
    return {
      "capacity_kg":5000.,"initial_kg":2500.,"terminal_kg":2500.,
      "charge_max_kg_h":2200.,"discharge_max_kg_h":2200.,
      "loss_fraction_per_hour":0.0001,"rated_mw":125.,
      "min_load_fraction":0.1,"max_load_fraction":1.,
      "ramp_mw_h":50.,"grid_max_mw":50.,
      "h2_coefficient_kg_mwh":20.,"delivery_limit_kg_h":7200.,
      "source_bafu_PEM_pressure_bar":30.,
      "source_pipeline_min_delivery_pressure_bar":20.
    }


def test_additional_adequacy_is_quantified_not_declared_equal_delivery():
    p=params()
    duty=build_screened_pressure_duty("I_200bar",5000.)
    target=np.array([2000.,2000.,2000.,2000.])
    wind=np.zeros(4)
    result=minimum_new_shortfall(wind,np.array([20.,20.,20.,20.]),target,p,duty,limit_seconds=30)
    assert result["solver_optimal"]
    assert result["additional_shortfall_kg"]>=3999.
    assert result["achievable_annual_h2_under_screen_kg"]<target.sum()
    assert result["shortfall_hour_count"]>=1
    assert math.isclose(
      result["achievable_annual_h2_under_screen_kg"]+result["additional_shortfall_kg"],
      result["original_E_delivered_reference_target_kg"],abs_tol=1e-5)
    assert result["audit"]["pressure_EOS_bounds"]["EOS_hourly_mass_bounds_imply_pressure_limits"]
    assert max(result["audit"]["independent_max_physical_residuals"].values())<2e-4
    assert result["screening_only_no_full_contract_or_LCA"]


def test_adequacy_zero_deficit_possible_when_capacity_sufficient():
    p=params()
    duty=build_screened_pressure_duty("I_200bar",5000.)
    result=minimum_new_shortfall(
        np.full(4,100.),
        np.full(4,10.),
        np.full(4,1000.),
        p,duty,limit_seconds=30)
    assert result["additional_shortfall_kg"]<0.01
    assert result["solver_gap"]<=1e-6


def test_unphysical_hourly_target_rejected_in_shortfall_stage():
    p=params()
    duty=build_screened_pressure_duty("I_200bar",5000.)
    with pytest.raises(SourceLockedDispatchError,match="invalid source"):
        minimum_new_shortfall([10,10],[10,10],[100,-1],p,duty)
