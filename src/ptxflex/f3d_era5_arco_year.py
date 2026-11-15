"""Source-controlled ERA5 ARCO full-year calibration and alternate yearly point snapshots.

2023 calibration: compare *all 8760* hourly 10/100 m wind vectors and modeled
MW to individually SHA-locked original October 2026 PyNEXUS CDS NetCDFs.
2022/2024: only after passed 2023 calibration, acquire distinct ARCO point
representations, save actual four-component values in PRIVATE NetCDF, and
hash each native component and complete hourly output.

ARCO is a repackaged Copernicus ERA5 dataset, NOT a native month-CDS NetCDF,
never an actual wind farm measurement or independent evidence of profitability.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np

from .f3d_era5_arco_pilot import ARCO_URL, ALIASES, need, select_variable_name
from .f3d_era5_sharded_acquisition import (
    PY_NEXUS_RECOVERED_2023_MONTH_SHA, original_filename, filehash,
)
from .f3d_live_era5 import (
    REFERENCE_LAT, REFERENCE_LON, YEARS, FARM_LIMIT_MW,
    EXPECTED_2023_WIND_MICROMW_SHA,
    original_farm_mw_from_u100_v100, f64sha, micro_mw_source_sha,
    _extract_series, load_original_month,
)

SCHEMA_CAL="ptxflex.f3d_ARCO_2023_full_8760_hour_original_CDS_calibration.v1"
SCHEMA_YEAR="ptxflex.f3d_ARCO_hourly_point_year_reanalysis_snapshot.v1"
ARCO_SNAPSHOT_NAME="ARCO_ERA5_hourly_10m_100m_point_{year}.nc"
ARCO_ACCEPTED_STATUS="ARCO_2023_CALIBRATED_PROVIDER_REPRESENTATION_YEAR_COMPLETE_NOT_CDS_MONTHLY"
CAL_ACCEPTED_STATUS="ARCO_FULL_2023_8760H_CDS_NUMERICALLY_EQUIVALENT_1W"
# A plausible but numerically different ARCO 10m/100m series is NOT enough.
# Never hide a revised ERA5 field behind a successful yearly power hash.
COMPONENT_TOLERANCE_MS=1e-5


def sha_array(values):
    arr=np.asarray(values)
    need(arr.dtype.kind=="f" and arr.dtype.itemsize in (4,8),
         "ARCO provider native wind array must retain float32 or float64")
    dtype="<f4" if arr.dtype.itemsize==4 else "<f8"
    return hashlib.sha256(np.asarray(arr,dtype=dtype).tobytes()).hexdigest()


def require_exact_calendar(times,year):
    import pandas as pd
    expected=pd.date_range(f"{year}-01-01T00:00:00Z",
                           periods=YEARS[year],freq="h",tz="UTC")
    observed=pd.to_datetime(times,utc=True)
    need(observed.equals(expected),
         "ARCO source must have every hourly UTC instant in original full calendar")
    return expected


def read_arco_year(ds,year):
    """Only select one original offshore grid cell and exact UTC year."""
    need(year in YEARS,"unsupported historical ARCO source year")
    lat="latitude" if "latitude" in ds.coords else "lat"
    lon="longitude" if "longitude" in ds.coords else "lon"
    need(lat in ds.coords and lon in ds.coords,
         "ARCO longitude/latitude coordinate missing")
    point=ds.sel({lat:REFERENCE_LAT,lon:REFERENCE_LON},method="nearest")
    at_lat=float(np.asarray(point[lat].values).item())
    at_lon=float(np.asarray(point[lon].values).item())
    need(abs(at_lat-REFERENCE_LAT)<1e-8 and abs(at_lon-REFERENCE_LON)<1e-8,
         "ARCO source grid not exact original 52.5N, 3.5E")
    time_key="time" if "time" in point.coords else "valid_time"
    need(time_key in point.coords,"ARCO hourly original time coordinate absent")
    year_data=point.sel({time_key:slice(f"{year}-01-01T00:00:00",
                                        f"{year}-12-31T23:00:00")})
    require_exact_calendar(year_data[time_key].values,year)
    vectors={}
    names={}
    units={}
    for key in ALIASES:
        name=select_variable_name(year_data,key)
        da=year_data[name]
        need(da.ndim==1 and time_key in da.dims,
             "ARCO must provide one scalar grid point per UTC hour: "+key)
        unit=str(da.attrs.get("units",""))
        # A unitless ARCO field cannot be mistaken for m/s without review.
        need(unit.replace(" ","").casefold() in
             ("ms**-1","ms-1","m/s","metrespersecond","meterspersecond"),
             "ARCO variable units not confirmed to be wind velocity in m/s: "+key)
        arr=np.asarray(da.compute().values)
        need(arr.shape==(YEARS[year],) and arr.dtype.kind=="f" and
             arr.dtype.itemsize in (4,8) and np.isfinite(arr).all(),
             "ARCO year vector missing or nonfinite: "+key)
        vectors[key]=arr
        names[key]=name
        units[key]=unit
    wind=original_farm_mw_from_u100_v100(vectors["u100"],vectors["v100"])
    need(wind.shape==(YEARS[year],) and np.isfinite(wind).all() and
         np.min(wind)>=0 and np.max(wind)<=FARM_LIMIT_MW+1e-9,
         "ARCO original wind model violates 120m turbine source bounds")
    return vectors,wind,{"latitude":at_lat,"longitude":at_lon,
                         "field_names":names,"field_units":units,
                         "hours":YEARS[year]}


def original_2023_reference(folder):
    """Independently reread exact original twelve PyNEXUS CDS NetCDFs."""
    from .f3d_era5_sharded_acquisition import PY_NEXUS_RECOVERED_2023_MONTH_SHA
    import calendar
    import xarray as xr
    folder=Path(folder)
    need(folder.is_dir() and not folder.is_symlink(),
         "private original 2023 CDS NetCDF directory missing")
    require_set={original_filename(2023,month) for month in range(1,13)}
    need({p.name for p in folder.iterdir()}==require_set,
         "original 2023 CDS source must contain exactly twelve months")
    total={k:[] for k in ALIASES}
    annual=[]
    originals={}
    for month in range(1,13):
        p=folder/original_filename(2023,month)
        need(p.is_file() and not p.is_symlink() and
             filehash(p)==PY_NEXUS_RECOVERED_2023_MONTH_SHA[month],
             "2023 authentic PyNEXUS October CDS original monthly SHA changed")
        wind,meta=load_original_month(p,2023,month)
        hours=calendar.monthrange(2023,month)[1]*24
        with xr.open_dataset(p) as ds:
            point=ds.sel(latitude=REFERENCE_LAT,longitude=REFERENCE_LON,
                         method="nearest")
            for name in ALIASES:
                arr=_extract_series(point,name)
                need(arr.shape==(hours,),"original CDS component hours invalid")
                total[name].append(arr.copy())
        annual.extend(wind.tolist())
        originals[str(month)]={"sha256":filehash(p),"hours":hours}
    vectors={name:np.concatenate(parts) for name,parts in total.items()}
    original=np.asarray(annual,dtype="<f8")
    need(len(original)==8760 and
         micro_mw_source_sha(original)==EXPECTED_2023_WIND_MICROMW_SHA,
         "source-verified original 2023 must reproduce original E wind 1W SHA")
    return vectors,original,originals


def compare_2023_year(vectors,wind,original_vectors,original_wind):
    need(len(wind)==len(original_wind)==8760,
         "2023 8760 original/ARCO wind values missing")
    component_errors={}
    component_equivalence={}
    for name in ALIASES:
        a=np.asarray(vectors[name],dtype=np.float64)
        b=np.asarray(original_vectors[name],dtype=np.float64)
        need(a.shape==b.shape==(8760,), "source original component calendar differs")
        mx=float(np.max(np.abs(a-b)))
        component_errors[name]=mx
        component_equivalence[name]=bool(mx<=COMPONENT_TOLERANCE_MS)
    error=np.abs(np.asarray(wind)-np.asarray(original_wind))
    first=np.rint(np.asarray(original_wind)*1e6).astype("<i8")
    second=np.rint(np.asarray(wind)*1e6).astype("<i8")
    n_match=int(np.count_nonzero(first==second))
    all_match=n_match==8760
    passed=bool(all_match and all(component_equivalence.values()))
    return {
        "original_CDS_2023_1W_frozen_model_SHA256":EXPECTED_2023_WIND_MICROMW_SHA,
        "original_2023_1W_sha256_from_source_months":micro_mw_source_sha(original_wind),
        "ARCO_2023_1W_sha256":micro_mw_source_sha(wind),
        "original_2023_CDS_float64_model_SHA256":f64sha(original_wind),
        "ARCO_2023_float64_model_SHA256":f64sha(wind),
        "modelled_wind_1W_identical_hours":n_match,
        "max_absolute_2023_1W_quantum_disagreement":int(np.max(np.abs(first-second))),
        "maximum_original_CDS_vs_ARCO_modelled_wind_difference_MW":float(np.max(error)),
        "mean_original_CDS_vs_ARCO_modelled_wind_difference_MW":float(np.mean(error)),
        "max_abs_original_CDS_vs_ARCO_wind_component_diff_m_s":component_errors,
        "component_equivalence_within_1e_minus_5_m_per_s":component_equivalence,
        "full_8760h_2023_ARCO_matches_CDS_model_at_1W_and_four_component_tolerance":passed,
        "all_f64_wind_array_bytes_bitwise_identical":bool(
            f64sha(original_wind)==f64sha(wind)),
        "actual_wind_farm_independent_field_validation":False,
    }


def authenticated_arco_year(year,secret):
    import xarray as xr
    need(year in YEARS and isinstance(secret,str) and len(secret)>10,
         "authenticated original Copernicus CDS ARCO access required")
    print(f"OFFICIAL_ARCO_FULL_YEAR_SOURCE_START year={year} 52.5N_3.5E "
          "four_wind_components SECRET_NOT_LOGGED",flush=True)
    try:
        with xr.open_zarr(ARCO_URL,consolidated=True,
                          storage_options={"headers":{"Authorization":"Bearer "+secret}}) as ds:
            return read_arco_year(ds,year)
    except Exception as error:
        # HTTP error content or backend URL must not leak user secrets.
        raise RuntimeError(f"Official ARCO source-year read failed for {year} "
                           f"({type(error).__name__}); source authentication details suppressed") from None


def save_snapshot(target,vectors,year):
    import pandas as pd
    import xarray as xr
    need(not target.exists(),"cannot overwrite original ARCO annual point snapshot")
    coords={"time":pd.date_range(f"{year}-01-01",periods=YEARS[year],freq="h")}
    # NetCDF is a saved ARCO *extraction*, not a native CDS monthly download.
    data={name:(("time",),values,{"units":"m s**-1"})
          for name,values in vectors.items()}
    ds=xr.Dataset(data_vars=data,coords=coords,
                  attrs={"origin":"Copernicus ERA5 ARCO geo-chunked Zarr point extraction",
                         "source_URL":ARCO_URL,
                         "lat":REFERENCE_LAT,"lon":REFERENCE_LON,
                         "native_CDS_monthly_original":False})
    ds.to_netcdf(target)
    with xr.open_dataset(target) as check_ds:
        require_exact_calendar(check_ds.time.values,year)
        need(all(sha_array(np.asarray(check_ds[name].values))==sha_array(vectors[name])
                 for name in ALIASES),
             "saved ARCO original point values changed in NetCDF write/read")
    return filehash(target)


def write_utc_wind_csv(path,year,wind):
    import csv
    need(not path.exists(),"cannot overwrite normalized ARCO wind hours")
    start=datetime(year,1,1,tzinfo=timezone.utc)
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.writer(f)
        writer.writerow(["timestamp_utc","wind_available_mw"])
        for hour,v in enumerate(wind):
            writer.writerow([(start+timedelta(hours=hour)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                             format(float(v),".17g")])
    return filehash(path)


def acquire_arco(year,output,calibration,reference_months=None):
    """Only 2023 gets full direct source proof; others require it first."""
    start=time.monotonic()
    target=Path(output)
    need(year in YEARS and not target.exists(),"ARCO original extraction output already exists")
    token=os.getenv("ERA5_API_KEY","").strip()
    need(len(token)>10,"CDS access token required, never stored in results")
    cal=None
    if year==2023:
        need(reference_months is not None,
             "2023 source comparison requires exact original twelve PyNEXUS CDS months")
    else:
        need(calibration is not None and Path(calibration).is_file(),
             "2022/2024 ARCO requires completed 2023 annual calibration")
        cal=json.loads(Path(calibration).read_text(encoding="utf-8"))
        need(cal.get("schema_version")==SCHEMA_CAL and
             cal.get("status")==CAL_ACCEPTED_STATUS and
             cal.get("year")==2023 and
             cal.get("source_url")==ARCO_URL and
             cal.get("original_2023_1W_sha256_from_source_months")==EXPECTED_2023_WIND_MICROMW_SHA and
             cal.get("full_8760h_2023_ARCO_matches_CDS_model_at_1W_and_four_component_tolerance") is True and
             cal.get("modelled_wind_1W_identical_hours")==8760,
             "unverified 2023 full calendar ARCO calibration, NO alternative-year admission")
    vectors,wind,source=authenticated_arco_year(year,token)
    report={
        "schema_version":SCHEMA_CAL if year==2023 else SCHEMA_YEAR,
        "year":year,
        "source":"Copernicus ERA5 ARCO geo-chunked original point extraction",
        "source_url":ARCO_URL,
        "source_CDS_netCDF_monthly_original":False,
        "source_ERA5_single_level_ARCO_repackaged_product":True,
        "original_PyNEXUS_source_grid":{"latitude":REFERENCE_LAT,"longitude":REFERENCE_LON},
        "original_source_calendar_UTC_hours":len(wind),
        "original_CDS_API_SECRET_or_raw_hourly_values_committed":False,
        "complete_industrial_site_validation":False,
        "whole_plant_LCA_TEA_or_methanol_economic_release_allowed":False,
        "source_raw_ARCO_point_component_sha256":{
            k:sha_array(v) for k,v in vectors.items()},
        "source_raw_ARCO_point_component_dtype":{
            k:str(v.dtype) for k,v in vectors.items()},
        "source_raw_ARCO_point_component_count":len(vectors),
        "source_coordinates_and_variables":source,
        "normalized_wind_float64_SHA256":f64sha(wind),
        "normalized_wind_1W_quantized_SHA256":micro_mw_source_sha(wind),
        "annual_UTC_hours":len(wind),
        "full_UTC_calendar_year_no_gaps":True,
        "status":"UNVERIFIED",
        "read_elapsed_seconds":round(time.monotonic()-start,1),
        "source_point_netCDF_snapshot_SHA256":None,
        "normalized_csv_SHA256":None,
        "source_2023_full_calibration_file_SHA256":filehash(calibration) if cal else None,
        "source_2023_full_calibration_status":cal.get("status") if cal else None,
    }
    if year==2023:
        original_vectors,original_wind,originals=original_2023_reference(reference_months)
        evidence=compare_2023_year(vectors,wind,original_vectors,original_wind)
        report.update(evidence)
        report["original_2023_PyNEXUS_monthly_CDS_SHA256"]=originals
        report["status"]=(CAL_ACCEPTED_STATUS if
                          evidence["full_8760h_2023_ARCO_matches_CDS_model_at_1W_and_four_component_tolerance"]
                          else "2023_ARCO_FULL_YEAR_NOT_EQUIVALENT_STOP")
    else:
        report["status"]=ARCO_ACCEPTED_STATUS
        report["2023_frozen_CDS_wind_1W_sha256"]=EXPECTED_2023_WIND_MICROMW_SHA
        report["2022_2024_source_equivalence_is_reanalysis_not_site_validation"]=True
    target.mkdir(parents=True,exist_ok=False)
    if report["status"] in (ARCO_ACCEPTED_STATUS,CAL_ACCEPTED_STATUS):
        report["source_point_netCDF_snapshot_SHA256"]=save_snapshot(
            target/ARCO_SNAPSHOT_NAME.format(year=year),vectors,year)
        report["normalized_csv_SHA256"]=write_utc_wind_csv(
            target/"normalized_UTC_wind.csv",year,wind)
    (target/"provenance.json").write_text(
        json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n",
        encoding="utf-8")
    print(f"OFFICIAL_ARCO_YEAR_RESULT year={year} status={report['status']} "
          f"hours={len(wind)} read_s={report['read_elapsed_seconds']}",
          flush=True)
    if year==2023:
        print("ORIGINAL_CDS_TO_ARCO_2023_FULL_HOUR_1W_MATCH",
              evidence["modelled_wind_1W_identical_hours"],
              "/8760; max_MW_difference=",
              evidence["maximum_original_CDS_vs_ARCO_modelled_wind_difference_MW"],
              flush=True)
    need(report["status"] in (ARCO_ACCEPTED_STATUS,CAL_ACCEPTED_STATUS),
         "ARCO whole-year source model calibration failed; no year source vectors promoted")
    return report


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--year",type=int,required=True,choices=sorted(YEARS))
    p.add_argument("--reference-original-2023-netcdf-folder")
    p.add_argument("--verified-2023-ARCO-calibration")
    p.add_argument("--output",required=True)
    a=p.parse_args(argv)
    acquire_arco(a.year,a.output,a.verified_2023_ARCO_calibration,
                 reference_months=a.reference_original_2023_netcdf_folder)


if __name__=="__main__":
    main()
