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
    with pytest.raises(ValueError,match="does NOT reproduce original PyNEXUS source to 1W quantized resolution"):
        a.assemble_year(2023,source,out)
    provenance=json.loads((out/"provenance.json").read_text())
    assert provenance["status"]=="2023_ORIGINAL_SOURCE_WIND_NUMERICAL_REPRODUCTION_FAILED"
    assert provenance["original_2023_wind_float64_reference_match"] is False
    assert provenance["original_2023_wind_microMW_reference_match"] is False
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


def test_source_original_2023_downloaded_from_gh_has_all_12_frozen_month_hashes():
    assert len(a.PY_NEXUS_RECOVERED_2023_MONTH_SHA)==12
    assert set(a.PY_NEXUS_RECOVERED_2023_MONTH_SHA)==set(range(1,13))
    assert a.PY_NEXUS_RECOVERED_2023_MONTH_SHA[1]=="e0fbd6f67080f1421d50b2d787d9efa7e572d7a2b84c3a1f5b428860096e1d9c"
    assert a.PY_NEXUS_RECOVERED_2023_MONTH_SHA[12]=="e83ec69c5156e349c632b5e23ec6cb4975452a7b2ed62ae79830f778ef3fc507"
    assert a.FROZEN_2023_CDS_RECOVERY_ZIP_SHA=="730a7ae28c450e283f599043452e2fda350ca76f19a68bf62b32dbc0cf00491e"


def test_local_2023_zip_import_rejects_fake_source_without_CDS(tmp_path):
    import zipfile
    fake=tmp_path/"fake_2023_ERA5.zip"
    with zipfile.ZipFile(fake,"w") as z:
        z.writestr("era5_2023-01-01_2023-01-31_52.5_3.5.nc",b"not original")
    with pytest.raises(ValueError,match="original PyNEXUS full 2023 monthly ZIP SHA mismatch"):
        a.seed_original_2023_from_pynexus_zip(fake,tmp_path/"new_2023")


def test_local_2023_folder_import_rejects_missing_or_wrong_source_months(tmp_path):
    original=tmp_path/"original_12_months"
    original.mkdir()
    with pytest.raises(ValueError,match="exactly 12 original"):
        a.seed_original_2023_from_pynexus_folder(original,tmp_path/"recovered")
    # A fake timestamp-correct NetCDF still cannot replace the byte-frozen
    # original 26 Oct 2026 PyNEXUS CDS source.
    for month in range(1,13):
        last=calendar.monthrange(2023,month)[1]
        filename=f"era5_2023-{month:02d}-01_2023-{month:02d}-{last:02d}_52.5_3.5.nc"
        synthetic_netCDF(original/filename,2023,month)
    with pytest.raises(ValueError,match="does not match 2026-10-26 PyNEXUS audit"):
        a.seed_original_2023_from_pynexus_folder(original,tmp_path/"recovered")
