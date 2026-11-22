"""Standard-library-only independent F2 numerical certificate tests."""
from decimal import Decimal
import pytest
from ptxflex.f2_bank_count_independent import independent_bank_count


def test_exact_integer_boundary_and_one_vessel_minimality():
    a = independent_bank_count(target_kg='180', vessel_volume_m3='1.8',
        rho_upper_kg_m3='100', rho_lower_kg_m3='10',
        empty_vessel_mass_kg='2400', semantics='max_inventory')
    assert a.actual_vessels == 1
    assert a.capacity_margin_kg == 0
    assert a.preceding_bank_shortfall_kg == Decimal('180')
    assert a.withdrawable_mass_kg == Decimal('162')
    assert a.empty_vessel_hardware_kg == Decimal('2400')
    assert a.installed_station_mass_kg is None
    assert a.native_manufacturing_gwp_kg_co2e is None
    assert a.certified_design is False


def test_heel_changes_service_and_ceiling_count():
    args = dict(target_kg='180', vessel_volume_m3='1.8',
                rho_upper_kg_m3='100', rho_lower_kg_m3='10',
                empty_vessel_mass_kg='2400')
    gross = independent_bank_count(**args, semantics='max_inventory')
    usable = independent_bank_count(**args, semantics='usable_service')
    assert gross.actual_vessels == 1
    assert usable.actual_vessels == 2
    assert usable.capacity_margin_kg == Decimal('144')
    assert usable.preceding_bank_shortfall_kg == Decimal('18')
    assert usable.heel_mass_kg == Decimal('36')
    assert usable.empty_vessel_hardware_kg == Decimal('4800')


@pytest.mark.parametrize('field,value', [
    ('target_kg', 0), ('target_kg', -1), ('target_kg', True),
    ('target_kg', 'NaN'), ('target_kg', 'Infinity'),
    ('vessel_volume_m3', 0), ('rho_upper_kg_m3', 'nan'),
    ('rho_lower_kg_m3', -2), ('empty_vessel_mass_kg', None),
])
def test_reject_invalid_numeric_inputs(field, value):
    args = dict(target_kg=180, vessel_volume_m3=1.8,
        rho_upper_kg_m3=100, rho_lower_kg_m3=10,
        empty_vessel_mass_kg=2400, semantics='usable_service')
    args[field] = value
    with pytest.raises(ValueError):
        independent_bank_count(**args)


def test_reject_inverted_density_and_undefined_semantics():
    args = dict(target_kg=180, vessel_volume_m3=1.8,
        rho_upper_kg_m3=100, rho_lower_kg_m3=100,
        empty_vessel_mass_kg=2400, semantics='usable_service')
    with pytest.raises(ValueError):
        independent_bank_count(**args)
    args['rho_lower_kg_m3'] = 10
    args['semantics'] = 'kg_steel_equals_kg_h2'
    with pytest.raises(ValueError):
        independent_bank_count(**args)
