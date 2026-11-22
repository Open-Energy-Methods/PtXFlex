"""Synthetic F2 EOS envelope regression tests; no plant measurements."""
import pytest
pytest.importorskip("CoolProp")
from CoolProp.CoolProp import PropsSI
from ptxflex.f2_temperature_envelope_audit import (
    EnvelopeInputError, audit_pressure_temperature_envelope,
)


def fixture(**overrides):
    volume=10.0
    m_lo=PropsSI("Dmass","P",30e5,"T",313,"Hydrogen")*volume
    m_hi=PropsSI("Dmass","P",150e5,"T",313,"Hydrogen")*volume
    args=dict(minimum_total_h2_kg=m_lo,maximum_total_h2_kg=m_hi,
              free_volume_m3=volume,minimum_temperature_k=313,
              maximum_temperature_k=313,minimum_pressure_bar_absolute=20,
              maximum_pressure_bar_absolute=200,grid_points_per_axis=9)
    args.update(overrides)
    return args


def test_independent_eos_reproduces_endpoint_pressure():
    result=audit_pressure_temperature_envelope(**fixture())
    assert abs(result.minimum_sampled_bar_absolute-30)<1e-6
    assert abs(result.maximum_sampled_bar_absolute-150)<1e-6
    assert result.sampled_grid_points==81
    assert result.all_sampled_points_within_bounds
    assert not result.exhaustive_continuous_domain_proof
    assert not result.certified_equipment_design


def test_higher_temperature_changes_pressure_and_can_fail_rating():
    base=audit_pressure_temperature_envelope(**fixture())
    hot=audit_pressure_temperature_envelope(**fixture(maximum_temperature_k=450,
                                                   maximum_pressure_bar_absolute=160))
    assert hot.maximum_sampled_bar_absolute>base.maximum_sampled_bar_absolute
    assert not hot.all_sampled_points_within_bounds


def test_lower_temperature_can_fail_minimum_withdrawal_pressure():
    cold=audit_pressure_temperature_envelope(**fixture(minimum_temperature_k=200,
                                                     minimum_pressure_bar_absolute=25))
    assert not cold.all_sampled_points_within_bounds


@pytest.mark.parametrize("changes",[
    {"minimum_total_h2_kg":-1},
    {"free_volume_m3":0},
    {"minimum_temperature_k":float("nan")},
    {"maximum_temperature_k":float("inf")},
    {"minimum_pressure_bar_absolute":200},
    {"minimum_total_h2_kg":1e9},
    {"grid_points_per_axis":1},
    {"grid_points_per_axis":True},
])
def test_invalid_inputs_or_unsupported_conditions_fail_closed(changes):
    if "minimum_total_h2_kg" in changes and changes["minimum_total_h2_kg"]==1e9:
        with pytest.raises(EnvelopeInputError):
            audit_pressure_temperature_envelope(**fixture(**changes))
    else:
        with pytest.raises(EnvelopeInputError):
            audit_pressure_temperature_envelope(**fixture(**changes))
