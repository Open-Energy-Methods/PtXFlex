"""Independent endpoint checks for F2 inverse heel-pressure screen."""
import pytest
from ptxflex.f2_thermal_working_capacity import ThermalCapacityError, screen_thermal_working_capacity
from ptxflex.f2_thermal_pressure_limit import solve_maximum_heel_pressure

BASE = dict(free_volume_m3=1.8, maximum_pressure_bar_absolute=200.,
    minimum_search_pressure_bar_absolute=20., reference_temperature_k=313.,
    cold_temperature_k=293., hot_temperature_k=333.)

def solve(target, **changes):
    return solve_maximum_heel_pressure(target_usable_kg=target, **(BASE | changes))

def forward(p):
    return screen_thermal_working_capacity(free_volume_m3=1.8,
        maximum_pressure_bar_absolute=200.,
        minimum_withdrawal_pressure_bar_absolute=p,
        reference_temperature_k=313., cold_temperature_k=293.,
        hot_temperature_k=333.).conservative_usable_kg

@pytest.mark.parametrize("heel", [20., 30., 50., 100.])
def test_forward_inverse_round_trip(heel):
    target = forward(heel)
    result = solve(target)
    assert result.maximum_permissible_heel_bar_absolute == pytest.approx(heel, abs=2e-5)
    assert result.usable_kg_at_limit >= target - 1e-8
    assert not result.equipment_qualified
    assert not result.compressor_and_bop_included
    assert not result.native_lca_complete

def test_unattainable_target_rejected():
    with pytest.raises(ThermalCapacityError, match="infeasible"):
        solve(forward(20.) * 1.01)

def test_larger_requested_capacity_reduces_permissible_heel():
    assert solve(forward(40.)).maximum_permissible_heel_bar_absolute < solve(forward(80.)).maximum_permissible_heel_bar_absolute

@pytest.mark.parametrize("change", [
    {"target_usable_kg": float("nan")}, {"target_usable_kg": -1.},
    {"free_volume_m3": 0.}, {"pressure_tolerance_bar": 0.},
    {"maximum_pressure_bar_absolute": 20.},
    {"cold_temperature_k": 340.},
])
def test_bad_inputs_rejected(change):
    args = BASE | {"target_usable_kg": 1.} | change
    with pytest.raises(ThermalCapacityError):
        solve_maximum_heel_pressure(**args)
