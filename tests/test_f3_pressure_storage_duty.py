"""Source-backed EOS pressure-limited dispatch integration QA.

All 4–6 hour arrays in these tests are synthetic mathematical test vectors;
actual 2023 runs must use original frozen PyNEXUS archives/verified hashes.
Scientific identity: the same real-gas bank admits heel mass and compressor
electricity, with conservative fixed upper-pressure charge work and explicitly
missing cooling/motor part-load/vendor data.
"""
import math
import numpy as np
import pytest
pytest.importorskip("CoolProp")

from ptxflex.hydrogen_physics import HydrogenPropertyError
from ptxflex.pressure_storage_duty import (
  build_screened_pressure_duty,validate_screened_duty,audit_gas_pressure_boundaries,
  RVO_SOURCE,COMPRESSOR_EFFICIENCY,MOTOR_EFFICIENCY
)
from ptxflex.f3_matched_ideal_benchmark import (
  SourceLockedDispatchError,solve_ideal_storage,independently_audit, DIM,
  P,G,C,S,CH,DIS
)


def source_test_params(cap=5000.,loss=0.0001):
    return {
      "capacity_kg":cap,"initial_kg":2500.,"terminal_kg":2500.,
      "charge_max_kg_h":2200.,"discharge_max_kg_h":2200.,
      "loss_fraction_per_hour":loss,"rated_mw":125.,
      "min_load_fraction":.1,"max_load_fraction":1.,
      "ramp_mw_h":50.,"grid_max_mw":50.,
      "h2_coefficient_kg_mwh":20.,
      "delivery_limit_kg_h":7200.,
      "source_bafu_PEM_pressure_bar":30.,
      "source_pipeline_min_delivery_pressure_bar":20.,
    }


def test_real_source_pressure_scenario_and_compression_inputs():
    src=source_test_params()
    d=build_screened_pressure_duty("I_200bar",src["capacity_kg"])
    assert d.capacity_semantics=="max_inventory"
    assert d.vessel_count>=1
    assert 0<d.gas_heel_kg<src["initial_kg"]
    assert d.bank_empty_vessel_mass_kg==d.vessel_count*2400.
    assert d.compressor_electrical_kwh_per_kg_charged>0.
    assert d.compressor_eta_isentropic==COMPRESSOR_EFFICIENCY==0.8
    assert d.motor_eta==MOTOR_EFFICIENCY==0.9
    assert d.source_compressor_assumptions_uri==RVO_SOURCE
    assert validate_screened_duty(d,src)
    assert d.includes_cooling_electricity is False
    assert d.includes_compressor_equipment_manufacture is False
    assert d.includes_vessel_material_fabrication_lca is False


@pytest.mark.parametrize("mode",["max_inventory","usable_service"])
def test_source_based_pressure_constraints_run_in_actual_scipy_milp(mode):
    src=source_test_params()
    d=build_screened_pressure_duty("I_200bar",src["capacity_kg"],capacity_semantics=mode)
    wind=np.array([90.,90.,90.,90.,90.,90.])
    price=np.array([50.,20.,10.,70.,80.,30.])
    service=np.array([1000.]*6)
    out=solve_ideal_storage(wind,price,service,src,pressure_duty=d,time_limit_s=30)
    assert out["solver_optimal"]
    assert out["is_ideal_storage_only"] is False
    assert out["pressure_vessel_eos_screened"] is True
    audit=out["derived_audit"]
    assert audit["hours"]==6
    assert audit["annual_service_h2_kg"]==6000
    assert audit["annual_compression_electricity_mwh"]>0
    assert audit["maximum_compressor_load_MW"]>0
    assert audit["pressure_EOS_bounds"]["EOS_hourly_mass_bounds_imply_pressure_limits"]
    assert audit["pressure_EOS_bounds"]["real_gas_minimum_dispatched_pressure_bar_absolute"]>=20.-1e-5
    assert audit["pressure_EOS_bounds"]["real_gas_maximum_dispatched_pressure_bar_absolute"]<=200.+1e-5
    assert max(audit["independent_max_physical_residuals"].values())<2e-4
    x=np.asarray(out["hourly_solved_states"])
    # Electricity conservation now includes charged-H2 compressor energy.
    alpha=d.compressor_mw_per_kg_h()
    assert np.allclose(wind+x[:,G]-x[:,P]-x[:,CH]*alpha-x[:,C],0,atol=2e-4)
    assert np.all(x[:,S]>=d.min_model_inventory_kg()-1e-6)
    assert audit["wind_to_total_PEM_and_compressor_mwh"]>=0


def test_pressure_duty_energy_is_not_double_counted():
    src=source_test_params()
    wind=np.array([90.,90.,90.,90.])
    price=np.array([10.,20.,30.,40.])
    target=np.array([1000.]*4)
    ideal=solve_ideal_storage(wind,price,target,src,time_limit_s=30)
    d=build_screened_pressure_duty("I_200bar",src["capacity_kg"])
    phys=solve_ideal_storage(wind,price,target,src,pressure_duty=d,time_limit_s=30)
    a=phys["derived_audit"]
    assert a["annual_compression_electricity_mwh"]>=0
    assert math.isclose(a["annual_h2_produced_kg"],sum(target)+a["annual_h2_storage_loss_kg"],abs_tol=.01)
    assert ideal["derived_audit"]["annual_compression_electricity_mwh"]==0


def test_inappropriate_lower_pressure_delivery_gate_is_rejected():
    src=source_test_params()
    d=build_screened_pressure_duty("I_200bar",src["capacity_kg"],
          delivery_min_bar_absolute=15.)
    with pytest.raises(HydrogenPropertyError,match="below source delivery gate"):
        validate_screened_duty(d,src)


def test_original_start_state_below_vessel_heel_fails_closed():
    src=source_test_params()
    d=build_screened_pressure_duty("I_30bar",src["capacity_kg"])
    # Approx 2/3 nominal gas remains at 20bar in low-pressure bank.
    assert d.gas_heel_kg>src["initial_kg"]
    with pytest.raises(HydrogenPropertyError,match="original source initial stock below residual"):
        validate_screened_duty(d,src)


def test_pressure_auditor_rejects_sub_heel_gas_mass():
    d=build_screened_pressure_duty("I_200bar",5000.)
    with pytest.raises(HydrogenPropertyError,match="out of bounds"):
        audit_gas_pressure_boundaries(d,[1.,2500.])


def test_compressor_work_screen_not_claimed_as_measured_plant_performance():
    d=build_screened_pressure_duty("I_200bar",5000.)
    assert d.is_conservative_fixed_upper_pressure_work_screen
    assert d.temperature_k==313.
    assert d.compressor_stages==2
    assert d.source_property_library.startswith("CoolProp==8.0.0")
