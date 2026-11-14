"""Independent F2 algebraic tests; synthetic densities, NOT observed hydrogen."""
import pytest
from ptxflex.f2_independent_bank_audit import BankAuditError, independent_bank_audit


def run(**changes):
    x = dict(target_kg=100, free_volume_m3=2,
             density_at_max_kg_m3=10, density_at_min_kg_m3=2,
             capacity_semantics="max_inventory", reported_vessel_count=5)
    x.update(changes)
    return independent_bank_audit(**x)


def test_gross_vs_usable_differ_and_conserve_mass():
    gross = run()
    usable = run(capacity_semantics="usable_service", reported_vessel_count=7)
    assert gross.minimum_vessels == 5
    assert usable.minimum_vessels == 7
    assert gross.total_gross_kg == gross.total_heel_kg + gross.total_working_kg
    assert usable.total_working_kg >= 100
    assert not usable.source_pressure_basis_confirmed
    assert not usable.installed_equipment_complete
    assert not usable.industrial_design_validated


@pytest.mark.parametrize("change", [
    dict(reported_vessel_count=4),
    dict(reported_vessel_count=6),
    dict(reported_vessel_count=True),
    dict(reported_vessel_count=5.0),
    dict(capacity_semantics="unspecified"),
    dict(target_kg=0),
    dict(target_kg=float("nan")),
    dict(free_volume_m3=0),
    dict(density_at_max_kg_m3=2),
    dict(density_at_min_kg_m3=0),
    dict(density_at_max_kg_m3=float("inf")),
])
def test_reject_invalid_or_nonminimal_bank(change):
    with pytest.raises(BankAuditError):
        run(**change)


def test_integer_rounding_above_exact_boundary():
    with pytest.raises(BankAuditError):
        run(target_kg=100.000001)
    assert run(target_kg=100.000001, reported_vessel_count=6).minimum_vessels == 6
