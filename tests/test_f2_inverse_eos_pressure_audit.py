"""F2 inverse-EOS pressure audit: model-state semantics, not certified duty.

Uses CoolProp's independent Dmass->P property call to challenge the
forward P->Dmass vessel screen at endpoint and intermediate inventories.
This tests thermodynamic round-trip consistency at a single assumed 313 K;
it is not independent experimental validation of CoolProp or a vessel design.
"""
import pytest
from CoolProp.CoolProp import PropsSI

from ptxflex.hydrogen_physics import HydrogenPropertyError
from ptxflex.pressure_storage_duty import (
    audit_gas_pressure_boundaries, build_screened_pressure_duty,
)
from ptxflex.storage_reference_vessels import PUBLISHED_VESSELS


@pytest.mark.parametrize("vessel_id", sorted(PUBLISHED_VESSELS))
@pytest.mark.parametrize("semantics", ["max_inventory", "usable_service"])
def test_inverse_eos_at_heel_midpoint_and_full_bank(vessel_id, semantics):
    duty = build_screened_pressure_duty(
        vessel_id, 20_000, capacity_semantics=semantics,
        delivery_min_bar_absolute=20, temperature_k=313,
    )
    heel = duty.gas_heel_kg
    full = duty.bank_gas_at_reference_max_kg
    # Gross physical stock maps to a model stock differently in each mode.
    physical_states = [heel, (heel + full) / 2, full]
    offset = heel if semantics == "usable_service" else 0
    model_states = [mass - offset for mass in physical_states]
    result = audit_gas_pressure_boundaries(duty, model_states)
    assert result["real_gas_minimum_dispatched_pressure_bar_absolute"] == pytest.approx(
        duty.gas_minimum_absolute_bar, rel=2e-7, abs=2e-5
    )
    assert result["real_gas_maximum_dispatched_pressure_bar_absolute"] == pytest.approx(
        duty.gas_maximum_absolute_bar, rel=2e-7, abs=2e-5
    )
    pressures = [
        PropsSI("P", "Dmass", mass / duty.bank_free_volume_m3,
                "T", duty.temperature_k, "Hydrogen") / 1e5
        for mass in physical_states
    ]
    assert pressures[0] < pressures[1] < pressures[2]
    assert pressures[0] == pytest.approx(duty.gas_minimum_absolute_bar, rel=2e-7)
    assert pressures[2] == pytest.approx(duty.gas_maximum_absolute_bar, rel=2e-7)
    assert result["EOS_hourly_mass_bounds_imply_pressure_limits"] is True
    assert duty.includes_cooling_electricity is False
    assert duty.includes_compressor_equipment_manufacture is False
    assert duty.includes_vessel_material_fabrication_lca is False


@pytest.mark.parametrize("semantics", ["max_inventory", "usable_service"])
def test_inverse_eos_rejects_pressure_outside_screened_bank(semantics):
    duty = build_screened_pressure_duty(
        "I_200bar", 20_000, capacity_semantics=semantics,
        delivery_min_bar_absolute=20, temperature_k=313,
    )
    offset = duty.gas_heel_kg if semantics == "usable_service" else 0
    for invalid_gross in (
        duty.gas_heel_kg * 0.99,
        duty.bank_gas_at_reference_max_kg * 1.01,
    ):
        with pytest.raises(HydrogenPropertyError, match="pressure out of bounds"):
            audit_gas_pressure_boundaries(duty, [
                invalid_gross - offset,
                (duty.gas_heel_kg + duty.bank_gas_at_reference_max_kg) / 2 - offset,
            ])
