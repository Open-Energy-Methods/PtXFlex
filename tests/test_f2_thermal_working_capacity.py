"""F2 temperature endpoint pressure-storage checks: hypothetical, not plant data."""
import math
import pytest

from ptxflex.f2_thermal_working_capacity import (
    ThermalCapacityError, screen_thermal_working_capacity,
)

BASE = dict(
    free_volume_m3=1.8, maximum_pressure_bar_absolute=200.0,
    minimum_withdrawal_pressure_bar_absolute=20.0,
    reference_temperature_k=313.0, cold_temperature_k=293.0,
    hot_temperature_k=333.0,
)


def test_hot_fill_and_cold_heel_reduce_working_capacity():
    result = screen_thermal_working_capacity(**BASE)
    assert 0 < result.conservative_usable_kg < result.reference_usable_kg
    assert result.loss_vs_isothermal_kg == pytest.approx(
        result.reference_usable_kg - result.conservative_usable_kg)
    assert 0 < result.loss_fraction < 1
    assert result.endpoint_equilibrium_only
    assert not result.transient_validated
    assert not result.compressor_included
    assert not result.certified_station
    assert not result.native_lca_complete


def test_zero_temperature_spread_is_isothermal():
    result = screen_thermal_working_capacity(**{
        **BASE, "cold_temperature_k": 313.0, "hot_temperature_k": 313.0})
    assert result.conservative_usable_kg == pytest.approx(result.reference_usable_kg)
    assert result.loss_fraction == pytest.approx(0, abs=1e-12)


def test_more_extreme_thermal_envelope_cannot_increase_capacity():
    moderate = screen_thermal_working_capacity(**BASE)
    wide = screen_thermal_working_capacity(**{
        **BASE, "cold_temperature_k": 283.0, "hot_temperature_k": 343.0})
    assert wide.conservative_usable_kg < moderate.conservative_usable_kg
    assert wide.loss_fraction > moderate.loss_fraction


def test_inventory_scales_linearly_with_assumed_free_volume():
    a = screen_thermal_working_capacity(**BASE)
    b = screen_thermal_working_capacity(**{**BASE, "free_volume_m3": 3.6})
    assert b.reference_usable_kg == pytest.approx(2 * a.reference_usable_kg)
    assert b.conservative_usable_kg == pytest.approx(2 * a.conservative_usable_kg)
    assert b.loss_fraction == pytest.approx(a.loss_fraction)


@pytest.mark.parametrize("key,value", [
    ("free_volume_m3", 0.0), ("free_volume_m3", float("nan")),
    ("maximum_pressure_bar_absolute", float("inf")),
    ("minimum_withdrawal_pressure_bar_absolute", -1.0),
    ("cold_temperature_k", 340.0), ("hot_temperature_k", 300.0),
    ("reference_temperature_k", 400.0), ("free_volume_m3", True),
])
def test_invalid_inputs_fail_closed(key, value):
    with pytest.raises(ThermalCapacityError):
        screen_thermal_working_capacity(**{**BASE, key: value})


def test_pressure_order_fails_closed():
    with pytest.raises(ThermalCapacityError):
        screen_thermal_working_capacity(**{
            **BASE, "minimum_withdrawal_pressure_bar_absolute": 200.0})
