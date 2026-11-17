"""Cross-check published-reference F2 bank screens with independent Decimal arithmetic.

This test uses the same CoolProp EOS input values, so it verifies arithmetic,
not an independent EOS or pressure-vessel certification. No private data.
"""
from decimal import Decimal

import pytest

from ptxflex.f2_bank_count_independent import independent_bank_count
from ptxflex.hydrogen_physics import hydrogen_density_kg_m3
from ptxflex.storage_reference_vessels import PUBLISHED_VESSELS, screen_vessel_bank


@pytest.mark.parametrize("vessel_id", sorted(PUBLISHED_VESSELS))
@pytest.mark.parametrize("target_kg", [20_000, 40_000])
@pytest.mark.parametrize("semantics", ["max_inventory", "usable_service"])
def test_eos_fed_independent_decimal_bank_certificate(vessel_id, target_kg, semantics):
    vessel = PUBLISHED_VESSELS[vessel_id]
    temperature_k = 313.0
    lower_bar_absolute = 20.0
    upper = hydrogen_density_kg_m3(vessel.max_reference_pressure_bar, temperature_k)
    lower = hydrogen_density_kg_m3(lower_bar_absolute, temperature_k)
    audit = independent_bank_count(
        target_kg=target_kg,
        vessel_volume_m3=vessel.internal_volume_m3,
        rho_upper_kg_m3=upper,
        rho_lower_kg_m3=lower,
        empty_vessel_mass_kg=vessel.empty_vessel_mass_kg,
        semantics=semantics,
    )
    screened = screen_vessel_bank(
        vessel_id, target_kg, lower_bar_absolute, temperature_k,
        capacity_semantics=semantics,
    )
    assert audit.actual_vessels == screened.number_of_reference_vessels
    assert audit.lower_bound_vessels == screened.number_of_reference_vessels
    assert audit.capacity_margin_kg >= 0
    assert audit.preceding_bank_shortfall_kg > 0
    assert float(audit.gross_mass_kg) == pytest.approx(
        screened.gross_hydrogen_at_max_pressure_kg, rel=1e-12)
    assert float(audit.heel_mass_kg) == pytest.approx(
        screened.residual_heel_hydrogen_at_min_pressure_kg, rel=1e-12)
    assert float(audit.withdrawable_mass_kg) == pytest.approx(
        screened.withdrawable_hydrogen_between_pressures_kg, rel=1e-12)
    assert float(audit.empty_vessel_hardware_kg) == pytest.approx(
        screened.empty_reference_vessels_total_kg, rel=1e-12)
    assert audit.installed_station_mass_kg is None
    assert audit.native_manufacturing_gwp_kg_co2e is None
    assert audit.certified_design is False
    assert screened.supports_and_compressor_mass_known is False
    assert screened.vessels_are_certified_for_this_duty is False
    assert screened.native_manufacturing_lca_calculated is False


def test_semantics_cannot_be_conflated_at_same_source_conditions():
    vessel = PUBLISHED_VESSELS["I_200bar"]
    hi = hydrogen_density_kg_m3(200.0, 313.0)
    lo = hydrogen_density_kg_m3(20.0, 313.0)
    gross = independent_bank_count(
        target_kg=20_000, vessel_volume_m3=vessel.internal_volume_m3,
        rho_upper_kg_m3=hi, rho_lower_kg_m3=lo,
        empty_vessel_mass_kg=vessel.empty_vessel_mass_kg,
        semantics="max_inventory")
    usable = independent_bank_count(
        target_kg=20_000, vessel_volume_m3=vessel.internal_volume_m3,
        rho_upper_kg_m3=hi, rho_lower_kg_m3=lo,
        empty_vessel_mass_kg=vessel.empty_vessel_mass_kg,
        semantics="usable_service")
    assert usable.actual_vessels > gross.actual_vessels
    assert gross.withdrawable_mass_kg < Decimal("20000")
    assert usable.withdrawable_mass_kg >= Decimal("20000")
