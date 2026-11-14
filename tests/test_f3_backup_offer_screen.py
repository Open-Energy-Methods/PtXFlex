"""Synthetic mathematical tests only; no supplier or 2023 observations."""
import hashlib
import json
import numpy as np
import pytest

from ptxflex.f3_backup_offer_screen import (
    certify_fixed_hourly_offer, SupplyQualificationError
)


def synthetic_trace():
    q=np.zeros(8760)
    q[4:8]=[10.,20.,10.,5.]
    raw=(json.dumps({
        "hourly_additional_shortfall_kg":q.tolist(),
        "derived_source_not_original_raw_prices_or_wind":True,
        "source_E_delivered_reference_profile_is_modelled":True
    },sort_keys=True,allow_nan=False,separators=(",",":"))+"\n").encode()
    return q,hashlib.sha256(raw).hexdigest()


def screen(q,s,digest,**overrides):
    args=dict(shortfall_trace_sha256=digest,
      source_provenance="synthetic verification fixture, NOT 2023 data",
      delivery_pressure_bar_absolute=20.,
      minimum_required_pressure_bar_absolute=20.,
      delivered_purity_mole_fraction=.999,
      minimum_required_purity_mole_fraction=.995,
      maximum_offer_ramp_kg_h_per_hour=20.,
      pressure_and_purity_independently_documented=True)
    args.update(overrides)
    return certify_fixed_hourly_offer(q,s,**args)


def test_exact_hourly_offer_math_is_sufficient_but_not_plant_validation():
    q,d=synthetic_trace()
    result=screen(q,q.copy(),d)
    assert result["fixed_trace_supplier_offer_screen_pass"]
    assert result["hourly_mass_service_met"]
    assert result["source_annual_modelled_shortfall_kg"]==45
    assert result["total_unserved_kg"]==0
    assert result["proposed_max_adjacent_hour_ramp_kg_h_per_hour"]==20
    assert not result["real_supplier_or_2023_availability_verified"]
    assert not result["full_plant_science_gate_passed"]


def test_same_annual_mass_wrong_hours_fails():
    q,d=synthetic_trace()
    s=np.roll(q,1)
    result=screen(q,s,d)
    assert np.sum(q)==np.sum(s)
    assert result["total_unserved_kg"]>0
    assert not result["fixed_trace_supplier_offer_screen_pass"]


@pytest.mark.parametrize("changes",[
    {"delivery_pressure_bar_absolute":19.},
    {"delivered_purity_mole_fraction":.99},
    {"maximum_offer_ramp_kg_h_per_hour":19.},
    {"pressure_and_purity_independently_documented":False}
])
def test_delivery_gate_rejections(changes):
    q,d=synthetic_trace()
    result=screen(q,q,d,**changes)
    assert not result["fixed_trace_supplier_offer_screen_pass"]


def test_tampered_source_trace_rejected_even_when_annual_mass_same():
    q,d=synthetic_trace()
    tampered=np.roll(q,1)
    with pytest.raises(SupplyQualificationError,match="SHA mismatch"):
        screen(tampered,tampered,d)


def test_nan_or_wrong_length_or_negative_source_fails_closed():
    q,d=synthetic_trace()
    for bad in (q[:-1],np.full(8760,np.nan),np.full(8760,-1.)):
        with pytest.raises(SupplyQualificationError):
            screen(bad,q,d)


def test_boolean_gate_and_nonnumeric_rejected():
    q,d=synthetic_trace()
    with pytest.raises(SupplyQualificationError):
        screen(q,q,d,delivery_pressure_bar_absolute=True)
    with pytest.raises(SupplyQualificationError):
        screen(q,q,d,maximum_offer_ramp_kg_h_per_hour=float("inf"))


def test_no_implicit_year_boundary_startup():
    q,d=synthetic_trace()
    s=q.copy()
    s[0]=10
    # In-year ramps are computed only for 0->1 ... 8758->8759.
    result=screen(q,s,d)
    assert result["proposed_max_adjacent_hour_ramp_kg_h_per_hour"]==20.
