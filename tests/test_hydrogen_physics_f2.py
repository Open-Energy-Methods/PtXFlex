"""Numerical F2 EOS verification; all pressures here are test-only DUTY CASES.

We have NOT approved any particular vessel design or pressure. Checks confirm
thermodynamic monotonicity and physical consistency; they are not calibration
against a manufacturer's installation or validation of tank manufacturing mass.
"""
import math
import pytest

pytest.importorskip("CoolProp",reason="install optional official CoolProp==8.0.0 via [physics]")

from ptxflex.hydrogen_physics import (
    HydrogenPropertyError,
    R_UNIVERSAL_J_PER_MOL_K, HYDROGEN_MOLAR_MASS_KG_PER_MOL,
    compression_work, conservation_residual_kg, hydrogen_density_kg_m3,
    ideal_gas_density_kg_m3, require_coolprop, usable_storage_volume,
)


def test_external_real_gas_source_and_low_pressure_ideal_limit():
    assert require_coolprop()=="8.0.0"
    actual=hydrogen_density_kg_m3(1.0,298.15)
    ideal=ideal_gas_density_kg_m3(1.0,298.15)
    # Pure hydrogen at 1bar is close to the independently derived ideal EOS.
    assert math.isclose(actual,ideal,rel_tol=0.02)
    assert actual>0


def test_working_volume_uses_pressure_swing_and_does_not_invent_tank_mass():
    a=usable_storage_volume(20000.0,30.0,200.0,298.15)
    b=usable_storage_volume(40000.0,30.0,200.0,298.15)
    assert a.density_maximum_kg_m3>a.density_minimum_kg_m3
    assert a.required_free_gas_volume_m3>0
    assert math.isclose(b.required_free_gas_volume_m3,2*a.required_free_gas_volume_m3,rel_tol=1e-12)
    assert math.isclose(
        a.initial_hydrogen_capacity_at_max_pressure_kg-
        a.residual_hydrogen_capacity_at_min_pressure_kg,
        a.useful_hydrogen_kg,rel_tol=1e-12)
    assert a.equipment_manufacturing_lca_complete is False
    assert a.hardware_mass_kg is None
    # 20,000kg H2 is NOT assumed to be 20,000kg equipment.


def test_compression_enthalpy_source_with_explicit_intercooling_assumption():
    one=compression_work(30,200,298.15,0.75,0.94,1)
    two=compression_work(30,200,298.15,0.75,0.94,2)
    assert one.total_electrical_kwh_per_kg_hydrogen>0
    assert two.total_electrical_kwh_per_kg_hydrogen>0
    assert two.total_electrical_kwh_per_kg_hydrogen<one.total_electrical_kwh_per_kg_hydrogen
    assert len(two.stage_diagnostics)==2
    assert all(s.discharge_temperature_k>298.15 for s in two.stage_diagnostics)
    assert two.intercooler_power_and_hardware_included is False


def test_electrical_energy_increases_when_motor_efficiency_falls():
    high=compression_work(30,200,298.15,0.75,0.96,2)
    low=compression_work(30,200,298.15,0.75,0.80,2)
    assert low.total_electrical_kwh_per_kg_hydrogen>high.total_electrical_kwh_per_kg_hydrogen


def test_no_pressure_increase_requires_no_compression_energy():
    result=compression_work(30,30,298.15,0.8,0.9,2)
    assert result.total_electrical_kwh_per_kg_hydrogen==0
    assert result.total_shaft_energy_kwh_per_kg_hydrogen==0
    assert result.stage_diagnostics==()


@pytest.mark.parametrize("args",[
    (20_000,200,30,298.15), # reverse pressure
    (20_000,30,200,-5),     # invalid thermodynamic gas temperature
    (20_000,30,701,298.15),# outside declared research screening envelope
    (0,30,200,298.15),     # zero/invalid inventory
])
def test_invalid_storage_boundary_rejected(args):
    with pytest.raises(HydrogenPropertyError):
        usable_storage_volume(*args)


@pytest.mark.parametrize("args",[
    (200,30,298.15,.8,.95,2),
    (30,200,298.15,1.2,.95,2),
    (30,200,298.15,.8,0,2),
    (30,200,298.15,.8,.9,0),
    (30,200,298.15,.8,.9,2.5),
])
def test_invalid_compressor_operating_input_rejected(args):
    with pytest.raises(HydrogenPropertyError):
        compression_work(*args)


def test_source_independent_inventory_balance_residual():
    assert conservation_residual_kg(50,20,30,39,1,.0)==0
    assert math.isclose(conservation_residual_kg(50,20,30,40,1,0),-1)
    with pytest.raises(HydrogenPropertyError):
        conservation_residual_kg(10,0,11,-1,0,0)
