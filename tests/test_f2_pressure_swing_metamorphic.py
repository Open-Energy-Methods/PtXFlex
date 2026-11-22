"""F2 metamorphic pressure-swing checks; numerical screening, not vessel approval.

CoolProp supplies densities in both compared calls: these tests establish
monotonic bookkeeping and inventory semantics, NOT independent EOS accuracy.
"""
import pytest

from ptxflex.storage_reference_vessels import PUBLISHED_VESSELS, screen_vessel_bank


@pytest.mark.parametrize("vessel_id", sorted(PUBLISHED_VESSELS))
@pytest.mark.parametrize("semantics", ["max_inventory", "usable_service"])
def test_higher_delivery_pressure_reduces_working_inventory(vessel_id, semantics):
    # All published reference maximum pressures exceed 25 bar(a).
    low = screen_vessel_bank(vessel_id, 20_000, 20, 313,
                             capacity_semantics=semantics)
    high = screen_vessel_bank(vessel_id, 20_000, 25, 313,
                              capacity_semantics=semantics)
    assert high.withdrawable_hydrogen_between_pressures_kg < low.withdrawable_hydrogen_between_pressures_kg if semantics == "max_inventory" else (
        high.number_of_reference_vessels >= low.number_of_reference_vessels
    )
    assert high.residual_heel_hydrogen_at_min_pressure_kg > low.residual_heel_hydrogen_at_min_pressure_kg if semantics == "max_inventory" else (
        high.withdrawable_hydrogen_between_pressures_kg >= 20_000
    )
    if semantics == "max_inventory":
        assert high.number_of_reference_vessels == low.number_of_reference_vessels
        assert high.gross_hydrogen_at_max_pressure_kg == pytest.approx(
            low.gross_hydrogen_at_max_pressure_kg)
    else:
        assert high.number_of_reference_vessels >= low.number_of_reference_vessels
    for case in (low, high):
        assert case.gross_hydrogen_at_max_pressure_kg == pytest.approx(
            case.residual_heel_hydrogen_at_min_pressure_kg
            + case.withdrawable_hydrogen_between_pressures_kg)
        assert not case.native_manufacturing_lca_calculated
        assert not case.vessels_are_certified_for_this_duty
        assert not case.supports_and_compressor_mass_known


@pytest.mark.parametrize("vessel_id", sorted(PUBLISHED_VESSELS))
def test_usable_semantics_never_requires_fewer_vessels(vessel_id):
    gross = screen_vessel_bank(vessel_id, 40_000, 20, 313,
                               capacity_semantics="max_inventory")
    usable = screen_vessel_bank(vessel_id, 40_000, 20, 313,
                                capacity_semantics="usable_service")
    assert usable.number_of_reference_vessels >= gross.number_of_reference_vessels
    assert usable.withdrawable_hydrogen_between_pressures_kg >= 40_000
    assert gross.gross_hydrogen_at_max_pressure_kg >= 40_000
