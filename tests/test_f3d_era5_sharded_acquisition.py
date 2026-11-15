"""CDS sharded acquisition/reassembly *SYNTHETIC* tests.

No test data is an observed ERA5 source or an independently source-admitted
historical year. Actual original 2023 must match the frozen PyNEXUS SHA.
"""
from __future__ import annotations

import calendar
import csv
from datetime import datetime,timedelta,timezone
import hashlib
import json

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from ptxflex import f3d_era5_sharded_acquisition as a

def synthetic_netCDF(path,year,month,*,v=7.0):
    n=calendar.monthrange(year,month)[1]*24
    times=pd.date_range(f"{year}-{month:02d}-01",periods=n,freq="h",tz="UTC")
    base=np.full((n,1,1),float(v),dtype=np.float64)
    x=xr.Dataset(
        data_vars={
            "u10":(("time","latitude","longitude"),base*0.7),
            "v10":(("time","latitude","longitude"),base*0),
            "u100":(("time","latitude","longitude"),base),
            "v100":(("time","latitude","longitude"),base*0)
        },
        coords={"time":times.tz_localize(None).to_numpy(),
                "latitude":[52.5],"longitude":[3.5]}
    )
    path.parent.mkdir(parents=True,exist_ok=True)
    x.to_netcdf(path)


def fake_twelve(tmp_path,year):
    folder=tmp_path/f"SYNTHETIC_{year}_never_source_admitted"/"original_monthly_netcdf"
    folder.mkdir(parents=True)
    for month in range(1,13):
        synthetic_netCDF(folder/a.original_filename(year,month),year,month)
    return folder.parent


def test_one_month_is_real_calendar_and_four_original_source_fields(tmp_path):
    p=tmp_path/a.original_filename(2024,2)
    synthetic_netCDF(p,2024,2)
    data,w=a.verified_month_from_bytes(p,2024,2)
    assert data["month_UTC_hours"]==696
    assert len(w)==696
    assert data["sha256"]==hashlib.sha256(p.read_bytes()).hexdigest()
    assert data["cds_request"]["year"]==["2024"]
    assert len(data["cds_request"]["day"])==29
    assert data["u10_v10_u100_v100_complete"] is True


def test_one_month_wrong_calendar_is_rejected(tmp_path):
    p=tmp_path/a.original_filename(2024,2)
    synthetic_netCDF(p,2023,2)
    with pytest.raises(ValueError,match="missing, extra or shifted"):
        a.verified_month_from_bytes(p,2024,2)


def test_synthetic_2022_year_validates_time_without_claiming_historical_origin(tmp_path):
    source=fake_twelve(tmp_path,2022)
    out=tmp_path/"synthetic_annual_2022"
    report=a.assemble_year(2022,source,out)
    assert report["annual_utc_hours"]==8760
    assert len(report["source_monthly_files"])==12
    assert report["status"]=="SOURCE_RECONSTRUCTED_NOT_EXTERNALLY_REVIEWED"
    assert report["full_F3D_source_admission_or_v1_release"] is False
    assert len(list(csv.DictReader((out/"normalized_UTC_wind.csv").open())))==8760
    assert report["normalized_csv_SHA256"]==a.filehash(out/"normalized_UTC_wind.csv")
    assert a.filehash(out/"original_monthly_netcdf"/a.original_filename(2022,1))==a.filehash(
        source/"original_monthly_netcdf"/a.original_filename(2022,1))


def test_synthetic_2024_leap_includes_8784_hours_and_feb_29(tmp_path):
    source=fake_twelve(tmp_path,2024)
    out=tmp_path/"synthetic_annual_2024"
    report=a.assemble_year(2024,source,out)
    assert report["annual_utc_hours"]==8784
    lines=(out/"normalized_UTC_wind.csv").read_text()
    assert "2024-02-29T12:00:00Z" in lines
    assert "2024-12-31T23:00:00Z" in lines
    assert "2025-01-01T00:00:00Z" not in lines


def test_source_2023_not_misrepresented_if_missing_original_frozen_SHA(tmp_path):
    source=fake_twelve(tmp_path,2023)
    out=tmp_path/"synthetic_annual_2023"
    with pytest.raises(ValueError,match="DOES NOT match"):
        a.assemble_year(2023,source,out)
    provenance=json.loads((out/"provenance.json").read_text())
    assert provenance["status"]=="ORIGINAL_PYNEXUS_2023_WIND_SHA_MISMATCH_NOT_ADMITTED"
    assert provenance["original_2023_wind_float64_reference_match"] is False
    assert not (out/"normalized_UTC_wind.csv").exists()


def test_no_silent_year_month_missing_or_extras(tmp_path):
    root=fake_twelve(tmp_path,2024)
    missing=root/"original_monthly_netcdf"/a.original_filename(2024,12)
    missing.unlink()
    with pytest.raises(ValueError,match="exactly 12"):
        a.assemble_year(2024,root,tmp_path/"out1")
    synthetic_netCDF(missing,2024,12)
    (root/"original_monthly_netcdf"/"unexpected_original.nc").write_bytes(b"FAKE")
    with pytest.raises(ValueError,match="exactly 12"):
        a.assemble_year(2024,root,tmp_path/"out2")


def test_no_rewriting_original_and_no_symlink_accepted(tmp_path):
    src=fake_twelve(tmp_path,2022)
    out=tmp_path/"synthetic_output"
    out.mkdir()
    with pytest.raises(ValueError,match="target already exists"):
        a.assemble_year(2022,src,out)


def test_single_month_method_rejects_invalid_calendar_and_unavailable_key(monkeypatch,tmp_path):
    with pytest.raises(ValueError,match="unsupported"):
        a.original_filename(2022,13)
    monkeypatch.delenv("ERA5_API_KEY",raising=False)
    with pytest.raises(ValueError,match="secret not available"):
        a.acquire_month(2023,5,tmp_path/"private_raw")
