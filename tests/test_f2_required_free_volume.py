"""Independent F2 volume-sizing oracle; ideal gas injected in tests only."""
import math
import sys
import types

import pytest

from ptxflex.f2_required_free_volume import solve_required_free_volume
from ptxflex.f2_thermal_working_capacity import (
    ThermalCapacityError, screen_thermal_working_capacity,
)

R = 4124.0


@pytest.fixture
def oracle(monkeypatch):
    package = types.ModuleType("CoolProp")
    sub = types.ModuleType("CoolProp.CoolProp")

    def density(output, k1, pressure, k2, temperature, fluid):
        assert (output, k1, k2, fluid) == ("Dmass", "P", "T", "Hydrogen")
        return pressure / (R * temperature)

    sub.PropsSI = density
    monkeypatch.setitem(sys.modules, "CoolProp", package)
    monkeypatch.setitem(sys.modules, "CoolProp.CoolProp", sub)


def kwargs(heel=20., cold=293., hot=333.):
    return dict(maximum_pressure_bar_absolute=200.,
                minimum_withdrawal_pressure_bar_absolute=heel,
                reference_temperature_k=313.,
                cold_temperature_k=cold, hot_temperature_k=hot)


@pytest.mark.parametrize("target,heel,cold,hot", [
    (1., 20., 293., 333.),
    (100., 30., 293., 333.),
    (20000., 80., 303., 323.),
    (40000., 20., 313., 313.),
])
def test_closed_form_volume_and_forward_consistency(oracle, target, heel, cold, hot):
    settings = kwargs(heel, cold, hot)
    result = solve_required_free_volume(target_usable_kg=target, **settings)
    delta_rho = 1e5 / R * (200. / hot - heel / cold)
    assert result.required_free_volume_m3 == pytest.approx(target / delta_rho, rel=1e-12)
    check = screen_thermal_working_capacity(
        free_volume_m3=result.required_free_volume_m3, **settings)
    assert check.conservative_usable_kg == pytest.approx(target, rel=1e-12)
    assert not result.certified_vessel_count
    assert not result.compressor_and_bop_included
    assert not result.native_lca_complete


def test_pressure_and_temperature_penalty(oracle):
    base = solve_required_free_volume(target_usable_kg=100., **kwargs())
    higher_heel = solve_required_free_volume(target_usable_kg=100., **kwargs(heel=50.))
    wider_thermal = solve_required_free_volume(
        target_usable_kg=100., **kwargs(cold=283., hot=343.))
    assert higher_heel.required_free_volume_m3 > base.required_free_volume_m3
    assert wider_thermal.required_free_volume_m3 > base.required_free_volume_m3


@pytest.mark.parametrize("target", [0., -1., float("nan"), float("inf"), True, "20"])
def test_reject_invalid_service(oracle, target):
    with pytest.raises(ThermalCapacityError, match="target_usable_kg"):
        solve_required_free_volume(target_usable_kg=target, **kwargs())


def test_reject_nonpositive_endpoint_working_capacity(oracle):
    with pytest.raises(ThermalCapacityError, match="no positive withdrawable"):
        solve_required_free_volume(
            target_usable_kg=100., **kwargs(heel=195., cold=273., hot=353.))


def test_no_real_gas_eos_no_result(oracle):
    def broken(*args):
        raise ValueError("unavailable")
    sys.modules["CoolProp.CoolProp"].PropsSI = broken
    with pytest.raises(ThermalCapacityError, match="EOS state unavailable"):
        solve_required_free_volume(target_usable_kg=100., **kwargs())
