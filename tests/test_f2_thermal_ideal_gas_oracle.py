"""Independent analytic limiting-oracle tests for F2 thermal pressure screens.

An injected ideal-gas density is used ONLY as a mathematical oracle for tests.
Production remains CoolProp-only; these tests do not validate a physical plant.
"""
import math
import sys
import types

import pytest

from ptxflex.f2_thermal_working_capacity import (
    ThermalCapacityError, screen_thermal_working_capacity,
)
from ptxflex.f2_thermal_pressure_limit import solve_maximum_heel_pressure

R_H2 = 4124.0  # J/(kg K), synthetic constant used only in oracle
V = 1.8
PMAX = 200.0
TCOLD = 293.0
THOT = 333.0


@pytest.fixture
def ideal_density(monkeypatch):
    pkg = types.ModuleType("CoolProp")
    sub = types.ModuleType("CoolProp.CoolProp")

    def propssi(output, key1, pressure, key2, temperature, fluid):
        assert (output, key1, key2, fluid) == (
            "Dmass", "P", "T", "Hydrogen"
        )
        return pressure / (R_H2 * temperature)

    sub.PropsSI = propssi
    monkeypatch.setitem(sys.modules, "CoolProp", pkg)
    monkeypatch.setitem(sys.modules, "CoolProp.CoolProp", sub)


def analytic_capacity(heel_bar, volume=V):
    return volume * 1e5 / R_H2 * (PMAX / THOT - heel_bar / TCOLD)


@pytest.mark.parametrize("heel", [20.0, 30.0, 60.0, 120.0])
def test_forward_against_independent_closed_form(ideal_density, heel):
    actual = screen_thermal_working_capacity(
        free_volume_m3=V,
        maximum_pressure_bar_absolute=PMAX,
        minimum_withdrawal_pressure_bar_absolute=heel,
        reference_temperature_k=313.0,
        cold_temperature_k=TCOLD,
        hot_temperature_k=THOT,
    )
    assert actual.conservative_usable_kg == pytest.approx(
        analytic_capacity(heel), rel=1e-12
    )
    assert actual.reference_usable_kg == pytest.approx(
        V * 1e5 / R_H2 * (PMAX - heel) / 313.0, rel=1e-12
    )
    assert actual.loss_vs_isothermal_kg >= 0
    assert not actual.transient_validated
    assert not actual.native_lca_complete


@pytest.mark.parametrize("heel", [20.0, 35.0, 75.0, 150.0])
def test_inverse_against_independent_closed_form(ideal_density, heel):
    target = analytic_capacity(heel)
    assert target > 0
    result = solve_maximum_heel_pressure(
        target_usable_kg=target,
        free_volume_m3=V,
        maximum_pressure_bar_absolute=PMAX,
        minimum_search_pressure_bar_absolute=20.0,
        reference_temperature_k=313.0,
        cold_temperature_k=TCOLD,
        hot_temperature_k=THOT,
        pressure_tolerance_bar=1e-6,
    )
    expected_heel = TCOLD * (PMAX / THOT - target * R_H2 / (V * 1e5))
    assert result.maximum_permissible_heel_bar_absolute == pytest.approx(
        expected_heel, abs=2e-6
    )
    assert result.usable_kg_at_limit >= target - 1e-8
    assert not result.equipment_qualified
    assert not result.compressor_and_bop_included


def test_volume_scaling_and_infeasible_target(ideal_density):
    baseline = analytic_capacity(20.0)
    scaled = screen_thermal_working_capacity(
        free_volume_m3=2 * V,
        maximum_pressure_bar_absolute=PMAX,
        minimum_withdrawal_pressure_bar_absolute=20.0,
        reference_temperature_k=313.0,
        cold_temperature_k=TCOLD,
        hot_temperature_k=THOT,
    )
    assert scaled.conservative_usable_kg == pytest.approx(2 * baseline)
    with pytest.raises(ThermalCapacityError, match="infeasible"):
        solve_maximum_heel_pressure(
            target_usable_kg=baseline * 1.01,
            free_volume_m3=V,
            maximum_pressure_bar_absolute=PMAX,
            minimum_search_pressure_bar_absolute=20.0,
            reference_temperature_k=313.0,
            cold_temperature_k=TCOLD,
            hot_temperature_k=THOT,
        )


def test_no_ideal_gas_fallback_in_production(ideal_density, monkeypatch):
    def unavailable(*args):
        raise ValueError("EOS unavailable")

    sys.modules["CoolProp.CoolProp"].PropsSI = unavailable
    with pytest.raises(ThermalCapacityError, match="EOS state unavailable"):
        screen_thermal_working_capacity(
            free_volume_m3=V,
            maximum_pressure_bar_absolute=PMAX,
            minimum_withdrawal_pressure_bar_absolute=20.0,
            reference_temperature_k=313.0,
            cold_temperature_k=TCOLD,
            hot_temperature_k=THOT,
        )


def test_inverse_rejects_marginally_infeasible_target_at_lower_boundary(ideal_density):
    """No numerical allowance may misclassify a deficient bank as service-feasible."""
    attainable = analytic_capacity(20.0)
    # Smaller than the former 1e-10 relative feasibility allowance.
    target = attainable * (1.0 + 5e-11)
    with pytest.raises(ThermalCapacityError, match="infeasible"):
        solve_maximum_heel_pressure(
            target_usable_kg=target,
            free_volume_m3=V,
            maximum_pressure_bar_absolute=PMAX,
            minimum_search_pressure_bar_absolute=20.0,
            reference_temperature_k=313.0,
            cold_temperature_k=TCOLD,
            hot_temperature_k=THOT,
        )


def test_inverse_exact_lower_boundary_remains_feasible(ideal_density):
    """The exact limiting heel pressure must not be rejected as infeasible."""
    target = analytic_capacity(20.0)
    result = solve_maximum_heel_pressure(
        target_usable_kg=target,
        free_volume_m3=V,
        maximum_pressure_bar_absolute=PMAX,
        minimum_search_pressure_bar_absolute=20.0,
        reference_temperature_k=313.0,
        cold_temperature_k=TCOLD,
        hot_temperature_k=THOT,
    )
    assert result.maximum_permissible_heel_bar_absolute == pytest.approx(20.0)
    assert result.usable_kg_at_limit >= target
