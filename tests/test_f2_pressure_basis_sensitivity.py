"""Pressure-basis ambiguity: numerical consistency and non-promotion controls."""
import pytest
from ptxflex.f2_pressure_basis_sensitivity import pressure_basis_sensitivity
from ptxflex.storage_reference_vessels import PUBLISHED_VESSELS
from ptxflex.storage_reference_vessels import screen_vessel_bank

@pytest.mark.parametrize("semantics", ["max_inventory","usable_service"])
@pytest.mark.parametrize("target", [20_000.,40_000.])
def test_pressure_basis_changes_only_upper_pressure_hypothesis(semantics,target):
    result=pressure_basis_sensitivity(target_kg=target,capacity_semantics=semantics)
    absolute,gauge=result["cases"]
    source=screen_vessel_bank("I_200bar",target,20.,313.,capacity_semantics=semantics)
    assert absolute["vessel_count"]==source.number_of_reference_vessels
    assert absolute["upper_absolute_bar"]==200.
    assert gauge["upper_absolute_bar"]==pytest.approx(201.01325)
    assert gauge["vessel_count"]<=absolute["vessel_count"]
    assert result["delta_gauge_minus_absolute_vessels"]<=0
    for case in (absolute,gauge):
        assert case["gross_hydrogen_kg"]-case["heel_hydrogen_kg"]==pytest.approx(case["withdrawable_hydrogen_kg"])
        assert case["empty_reference_vessel_hardware_kg"]==case["vessel_count"]*2400.
        assert case["certified_design"] is False
        assert case["installed_station_mass_kg"] is None
        assert case["native_manufacturing_gwp_kg_co2e"] is None
    assert result["published_pressure_basis_resolved"] is False
    assert result["complete_lca"] is False

@pytest.mark.parametrize("bad", [0.,-1.,float("nan"),float("inf"),True])
def test_rejects_invalid_ambient(bad):
    with pytest.raises(ValueError):
        pressure_basis_sensitivity(ambient_absolute_bar=bad)

def test_rejects_invalid_gate_and_semantics():
    with pytest.raises(ValueError):
        pressure_basis_sensitivity(lower_absolute_bar=200.)
    with pytest.raises(ValueError):
        pressure_basis_sensitivity(capacity_semantics="unspecified")
