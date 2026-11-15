"""No-network regression: 8,760h original-year ARCO calibration and 8,784h leap.

Synthetic xarray fixtures test the gate, NOT real Copernicus provider evidence.
The actual source-year 2023 requires frozen original NetCDFs and remote API.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from ptxflex import f3d_era5_arco_year as m


def fake_arco_dataset(year,steps=None,shift_hours=0):
    hours=steps or m.YEARS[year]
    times=pd.date_range(f"{year}-01-01",periods=hours,freq="h")
    if shift_hours:
        times=times+pd.Timedelta(hours=shift_hours)
    coords={"time":times,"latitude":[m.REFERENCE_LAT],
            "longitude":[m.REFERENCE_LON]}
    vals={}
    for name,value in (("u10",6.),("v10",2.),("u100",9.),("v100",1.)):
        original=np.full((hours,1,1),value,dtype=np.float32)
        vals[name]=(("time","latitude","longitude"),original,
                    {"units":"m s**-1"})
    return xr.Dataset(vals,coords=coords)


@pytest.mark.parametrize("year,hours",[(2022,8760),(2023,8760),(2024,8784)])
def test_full_year_arco_has_exact_UTC_and_original_grid(year,hours):
    ds=fake_arco_dataset(year)
    fields,wind,source=m.read_arco_year(ds,year)
    assert len(wind)==hours
    assert source["hours"]==hours
    assert set(fields)=={"u10","v10","u100","v100"}
    assert all(x.dtype==np.dtype("float32") for x in fields.values())
    assert source["field_units"]["u100"]=="m s**-1"


def test_no_missing_hour_or_extra_hour_can_pass():
    with pytest.raises(ValueError,match="every hourly UTC instant"):
        m.read_arco_year(fake_arco_dataset(2024,steps=8783),2024)
    with pytest.raises(ValueError,match="every hourly UTC instant"):
        m.read_arco_year(fake_arco_dataset(2023,shift_hours=1),2023)


def test_2023_whole_year_comparison_requires_all_four_component_vectors_and_1W():
    ds=fake_arco_dataset(2023)
    fields,wind,_=m.read_arco_year(ds,2023)
    exact={name:np.asarray(value).copy() for name,value in fields.items()}
    report=m.compare_2023_year(fields,wind,exact,wind.copy())
    assert report["modelled_wind_1W_identical_hours"]==8760
    assert report["max_absolute_2023_1W_quantum_disagreement"]==0
    assert report["full_8760h_2023_ARCO_matches_CDS_model_at_1W_and_four_component_tolerance"]
    exact["u100"][500]+=np.float32(0.01)
    wrong=m.original_farm_mw_from_u100_v100(exact["u100"],exact["v100"])
    bad=m.compare_2023_year(fields,wind,exact,wrong)
    assert bad["modelled_wind_1W_identical_hours"]<8760
    assert bad["full_8760h_2023_ARCO_matches_CDS_model_at_1W_and_four_component_tolerance"] is False


def test_2023_component_difference_cannot_hide_behind_equal_power():
    ds=fake_arco_dataset(2023)
    fields,wind,_=m.read_arco_year(ds,2023)
    other={name:np.asarray(value).copy() for name,value in fields.items()}
    other["u10"][10]+=np.float32(.5)
    r=m.compare_2023_year(fields,wind,other,wind.copy())
    assert r["modelled_wind_1W_identical_hours"]==8760
    assert r["component_equivalence_within_1e_minus_5_m_per_s"]["u10"] is False
    assert r["full_8760h_2023_ARCO_matches_CDS_model_at_1W_and_four_component_tolerance"] is False


def test_full_ARCO_point_snapshot_is_source_integral_and_leap_preserving(tmp_path):
    fields,wind,_=m.read_arco_year(fake_arco_dataset(2024),2024)
    p=tmp_path/m.ARCO_SNAPSHOT_NAME.format(year=2024)
    digest=m.save_snapshot(p,fields,2024)
    assert digest==m.filehash(p)
    with xr.open_dataset(p) as ds:
        assert ds.sizes["time"]==8784
        assert str(ds.time.values[0]).startswith("2024-01-01T00:00:00")
        assert str(ds.time.values[-1]).startswith("2024-12-31T23:00:00")
        assert ds.attrs["native_CDS_monthly_original"]=="0" or ds.attrs[
            "native_CDS_monthly_original"]==False
    csv=tmp_path/"normalized_UTC_wind.csv"
    m.write_utc_wind_csv(csv,2024,wind)
    text=csv.read_text()
    assert "2024-02-29T12:00:00Z" in text
    assert "2025-01-01T00:00:00Z" not in text


def test_fake_calibration_must_not_admit_2022_2024(monkeypatch,tmp_path):
    monkeypatch.setenv("ERA5_API_KEY","test_local_dummy_secret_only_1234")
    bogus=tmp_path/"fake_2023_ARCO_full_year.json"
    bogus.write_text(json.dumps({"schema_version":m.SCHEMA_CAL,
                                  "status":"JAN2023_1W_CALIBRATION_PASS_ONLY_FULL_YEAR_NOT_YET_VALIDATED"}))
    with pytest.raises(ValueError,match="unverified 2023 full calendar"):
        m.acquire_arco(2022,tmp_path/"2022-provisional",bogus)
    assert not (tmp_path/"2022-provisional").exists()


def test_source_ARCO_year_snapshot_rejects_mutated_raw_floating_vector():
    original=np.array([1.5,2.5,3.5],dtype=np.float32)
    other=original.copy()
    other[1]+=np.float32(.25)
    assert m.sha_array(original)!=m.sha_array(other)
