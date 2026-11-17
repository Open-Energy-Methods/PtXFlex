"""Source-locked F3-D counterfactual annual H2 service and market/wind integrity.

Prevents declaring rearranged 2023 prices or scaled 2023 ERA5 availability as
observed 2022, 2024 or a forecast of 2027+ real-market conditions.
"""
import hashlib
import json

import numpy as np
import pytest

from ptxflex.f3d_2023_source_hourly_counterfactuals import (
    SUPPORTED,STAGEA,SRC_E,SRC_ES,SCHEMA,derive_scenario,
    sha_float64,protocol,YEARS
)
from ptxflex.f3_matched_ideal_benchmark import SourceLockedDispatchError


@pytest.fixture
def observed():
    rng=np.arange(YEARS,dtype=float)
    price=42. + 20.*np.sin(2*np.pi*rng/8760)+35.*np.sin(2*np.pi*rng/24)
    price[::73]=-4.5
    wind=72.+32.*np.sin(2*np.pi*rng/(24*19.))+15.*np.cos(2*np.pi*rng/24)
    assert wind.min()>=0
    return price,wind


def test_original_external_years_and_hourly_input_stageA_protocol_fail_closed():
    x=protocol()
    assert x["source_year"]==2023
    assert not x["independently_observed_new_price_or_wind_year_available"]
    assert not x["alternative_2022_2024_provider_files_independently_fetched_and_sha_verified"]
    assert x["derived_source_hourly_arrays_not_committed"]
    assert x["E_ES_require_same_adjusted_2023_market_and_wind_each_hour"]
    assert x["full_economic_plant_GWP_or_LCOH_releasable"] is False
    assert x["source_zip_E_sha256"]==SRC_E
    assert x["source_zip_EplusS_sha256"]==SRC_ES
    assert list(v["common_hourly_H2_float64_sha256"] for v in x["stageA_modelled_h2_deficits"].values())==[STAGEA[m][1] for m in STAGEA]
    assert tuple(x["scenario_catalog"][i]["id"] for i in range(4))==SUPPORTED
    assert all(t["weather_year_as_actual_other_year"] is False for t in x["scenario_catalog"])


@pytest.mark.parametrize("scenario",SUPPORTED)
def test_four_hourly_stresses_are_deterministic_source_verified_transformations(observed,scenario):
    price,wind=observed
    p0,w0=price.copy(),wind.copy()
    a=derive_scenario(price,wind,scenario)
    b=derive_scenario(price,wind,scenario)
    assert np.array_equal(price,p0) and np.array_equal(wind,w0)
    assert a["source_price_2023_float64_sha256"]==sha_float64(price)
    assert a["source_wind_2023_float64_sha256"]==sha_float64(wind)
    assert a["scenario_price_float64_sha256"]==b["scenario_price_float64_sha256"]
    assert a["scenario_wind_float64_sha256"]==b["scenario_wind_float64_sha256"]
    assert a["market_price_2023_redistributed"] is False
    assert a["is_alternative_observed_price_or_wind_year"] is False
    p,w=a["price_eur_per_mwh"],a["wind_available_mw"]
    assert p.shape==w.shape==(8760,)
    assert np.isfinite(p).all() and np.isfinite(w).all() and w.min()>=0.
    if scenario=="price_circular_168h":
        assert np.array_equal(p,np.roll(price,168)) and np.array_equal(np.sort(p),np.sort(price))
        assert np.array_equal(w,wind)
    if scenario=="price_centered_spread_150":
        assert np.allclose(p,np.median(price)+1.5*(price-np.median(price)))
        assert np.array_equal(w,wind)
        assert p.min()<price.min()
    if scenario=="wind_090_multiplier":
        assert np.array_equal(p,price)
        assert np.allclose(w,0.9*wind)
        assert a["counterfactual_wind_annual_mwh"]==pytest.approx(.9*wind.sum(),rel=1e-12)
    if scenario=="wind_110_multiplier":
        assert np.array_equal(p,price)
        assert np.allclose(w,1.1*wind)
        assert a["counterfactual_wind_annual_mwh"]==pytest.approx(1.1*wind.sum(),rel=1e-12)


def test_2023_source_hourly_input_rejected_if_bad_shape_nonfinite_negative_wind(observed):
    p,w=observed
    with pytest.raises(SourceLockedDispatchError):
        sha_float64(p[:8759])
    with pytest.raises(SourceLockedDispatchError):
        derive_scenario(p,w[:100],"wind_090_multiplier")
    with pytest.raises(SourceLockedDispatchError):
        derive_scenario(p,np.full(YEARS,-1.),"wind_090_multiplier")
    with pytest.raises(SourceLockedDispatchError):
        derive_scenario(p,np.full(YEARS,np.inf),"price_circular_168h")
    with pytest.raises(SourceLockedDispatchError):
        derive_scenario(p,w,"fictitious_2024_observed_prices")
    with pytest.raises(SourceLockedDispatchError):
        derive_scenario(p,w,"random_normal_annual_draw_not_source_based")


def test_source_price_shift_is_NOT_percent_change_in_genuine_new_year(observed):
    price,wind=observed
    x=derive_scenario(price,wind,"price_circular_168h")
    assert x["price_mean_2023_eur_per_mwh"]==pytest.approx(x["price_mean_scenario_eur_per_mwh"],abs=1e-12)
    assert x["counterfactual_wind_annual_mwh"]==pytest.approx(x["source_wind_annual_mwh"],abs=1e-8)
    assert x["scenario_price_float64_sha256"]!=x["source_price_2023_float64_sha256"]
    assert x["scenario_wind_float64_sha256"]==x["source_wind_2023_float64_sha256"]


def test_2023_source_wind_derate_changes_resource_not_H2_load_or_market(observed):
    p,w=observed
    x=derive_scenario(p,w,"wind_090_multiplier")
    y=derive_scenario(p,w,"wind_110_multiplier")
    assert x["scenario_price_float64_sha256"]==y["scenario_price_float64_sha256"]==sha_float64(p)
    assert x["scenario_wind_float64_sha256"]!=y["scenario_wind_float64_sha256"]
    assert np.isclose(x["source_wind_annual_mwh"],y["source_wind_annual_mwh"])


@pytest.mark.parametrize("mutate",[
 lambda d:d.update(independently_observed_new_price_or_wind_year_available=True),
 lambda d:d.update(source_year=2024),
 lambda d:d.update(full_economic_plant_GWP_or_LCOH_releasable=True),
 lambda d:d["scenario_catalog"][0].update(weather_year_as_actual_other_year=True),
 lambda d:d["scenario_catalog"][0].update(id="2024_empirical"),
 lambda d:d["stageA_modelled_h2_deficits"]["usable_service"].update(common_hourly_H2_float64_sha256="a"*64),
])
def test_any_2024_or_plant_claim_or_original_H2_reference_revision_is_rejected(monkeypatch,tmp_path,mutate):
    import ptxflex.f3d_2023_source_hourly_counterfactuals as m
    d=protocol()
    mutate(d)
    p=tmp_path/"fake.json";p.write_text(json.dumps(d))
    monkeypatch.setattr(m,"MANIFEST",p)
    with pytest.raises(SourceLockedDispatchError):
        m.protocol()
