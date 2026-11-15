"""Pilot only: direct official Copernicus ERA5 ARCO geo-chunked point access.

ARCO is an alternative *representation* of ERA5, not automatically the
byte-identical original CDS NetCDF source. This command has NO authority to
admit 2022/2024 annual source years, generate private monthly archives, or
alter a completed original source. It compares Jan 2023 at 52.5N 3.5E
against an independently recovered original PyNEXUS CDS month (SHA checked)
before authorizing any research on replacing slow CDS month-by-month calls.

Official PUG: https://confluence.ecmwf.int/spaces/CKB/pages/505390919/
Repackaged ARCO is not an industrial weather measurement.
"""
from __future__ import annotations
import argparse
import calendar
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np

from .f3d_live_era5 import (
    REFERENCE_LAT, REFERENCE_LON,
    original_farm_mw_from_u100_v100, micro_mw_source_sha,
)
from .f3d_era5_sharded_acquisition import (
    PY_NEXUS_RECOVERED_2023_MONTH_SHA, filehash,
)

ARCO_URL = (
    "https://arco.datastores.ecmwf.int/cadl-arco-geo-002/arco/"
    "reanalysis_era5_single_levels/sfc/geoChunked.zarr"
)
SCHEMA = "oem.ptx.f3d_official_CDS_ARCO_original_2023_month_point_equality_pilot.v1"
ALIASES = {
    "u10": ("u10","10m_u_component_of_wind"),
    "v10": ("v10","10m_v_component_of_wind"),
    "u100": ("u100","100m_u_component_of_wind"),
    "v100": ("v100","100m_v_component_of_wind"),
}


def need(cond,reason):
    if not cond:
        raise ValueError("ARCO source calibration: "+reason)


def select_variable_name(ds,role):
    options=[n for n in ALIASES[role] if n in ds.data_vars]
    need(len(options)==1,
         "source must expose exactly one recognized "+role+
         " data variable (available variable names may have changed)")
    return options[0]


def read_original_vectors(path):
    import pandas as pd
    import xarray as xr
    original=Path(path)
    need(original.is_file() and not original.is_symlink() and
         filehash(original)==PY_NEXUS_RECOVERED_2023_MONTH_SHA[1],
         "2023 January original PyNEXUS CDS NetCDF SHA256 is not the frozen reference")
    with xr.open_dataset(original) as ds:
        point=ds.sel(latitude=REFERENCE_LAT,longitude=REFERENCE_LON,method="nearest")
        time_name="valid_time" if "valid_time" in point.coords else "time"
        times=pd.to_datetime(point[time_name].values,utc=True)
        expected=pd.date_range("2023-01-01T00:00:00Z",
                                periods=744,freq="h",tz="UTC")
        need(times.equals(expected),"original CDS January 2023 UTC calendar does not match")
        vec={}
        for role in ALIASES:
            arr=np.asarray(point[role].squeeze().values)
            need(arr.shape==(744,) and np.issubdtype(arr.dtype,np.floating) and
                 np.isfinite(arr).all(),"original CDS vectors are missing or not hourly")
            vec[role]=arr.copy()
    return vec


def interpret_arco_point(ds):
    """Accept only original 52.5 N, 3.5 E, 2023-01 full UTC native fields."""
    import pandas as pd
    lat="latitude" if "latitude" in ds.coords else "lat"
    lon="longitude" if "longitude" in ds.coords else "lon"
    need(lat in ds.coords and lon in ds.coords,
         "official ARCO latitude/longitude coordinate fields missing")
    point=ds.sel({lat:REFERENCE_LAT,lon:REFERENCE_LON},method="nearest")
    loc_lat=float(np.asarray(point[lat].values).item())
    loc_lon=float(np.asarray(point[lon].values).item())
    need(abs(loc_lat-REFERENCE_LAT)<1e-8 and abs(loc_lon-REFERENCE_LON)<1e-8,
         "ARCO grid cell not EXACTLY original PyNEXUS 0.25 degree cell")
    time_name="time" if "time" in point.coords else "valid_time"
    need(time_name in point.coords,"ARCO missing native UTC time coordinate")
    jan=point.sel({time_name:slice("2023-01-01","2023-01-31T23:00:00")})
    moments=pd.to_datetime(jan[time_name].values,utc=True)
    expected=pd.date_range("2023-01-01T00:00:00Z",
                            periods=744,freq="h",tz="UTC")
    need(moments.equals(expected),
         "ARCO January 2023 must be complete and UTC aligned to original source")
    vectors={}
    role_names={}
    for role in ALIASES:
        name=select_variable_name(jan,role)
        values=np.asarray(jan[name].compute().squeeze().values)
        need(values.shape==(744,) and np.issubdtype(values.dtype,np.floating)
             and np.isfinite(values).all(),
             "ARCO native "+role+" monthly vector missing/invalid")
        vectors[role]=values
        role_names[role]=name
    return vectors,role_names,{"latitude":loc_lat,"longitude":loc_lon}


def compare_original_and_arco(original,arco):
    need(set(arco)==set(original)==set(ALIASES),"four original wind vector roles missing")
    delta={}
    for name in ALIASES:
        left=np.asarray(original[name],dtype=np.float64)
        right=np.asarray(arco[name],dtype=np.float64)
        need(left.shape==(744,) and right.shape==(744,),"vector original UTC sample count changed")
        delta[name]=float(np.max(np.abs(left-right)))
    left_power=original_farm_mw_from_u100_v100(original["u100"],original["v100"])
    right_power=original_farm_mw_from_u100_v100(arco["u100"],arco["v100"])
    difference=np.abs(left_power-right_power)
    quantized_equal=np.array_equal(
        np.rint(left_power*1e6).astype("<i8"),
        np.rint(right_power*1e6).astype("<i8")
    )
    return {
        "utc_hour_count":744,
        "all_four_ARCO_native_wind_vector_max_abs_diff_ms":delta,
        "max_abs_modelled_wind_farm_difference_MW":float(difference.max()),
        "mean_abs_modelled_wind_farm_difference_MW":float(difference.mean()),
        "ARCO_Jan2023_wind_1W_quantized_matches_original_CDS_for_every_hour":
            bool(quantized_equal),
        "Jan2023_original_model_wind_1W_SHA256":micro_mw_source_sha(left_power),
        "Jan2023_ARCO_model_wind_1W_SHA256":micro_mw_source_sha(right_power),
        "ARCO_2022_2024_years_independently_admitted":False,
        "original_2023_full_annual_source_replaced":False,
        "actual_industrial_plant_measured_weather":False,
    }


def run_pilot(original_jan,output):
    target=Path(output)
    need(not target.exists(),"cannot overwrite original ARCO pilot evidence")
    token=os.getenv("ERA5_API_KEY","").strip()
    need(len(token)>10,"CDS API key required as private ERA5_API_KEY environment variable")
    original=read_original_vectors(original_jan)
    print("OFFICIAL_ARCO_GEO_POINT_SOURCE_START 2023-01 52.5N 3.5E; SECRET_NOT_LOGGED",
          flush=True)
    begin=time.monotonic()
    # Original authentication method, Copernicus ARCO PUG Aug 2026.
    import xarray as xr
    try:
        with xr.open_zarr(
            ARCO_URL,consolidated=True,
            storage_options={"headers":{"Authorization":"Bearer "+token}},
        ) as ds:
            source,roles,grid=interpret_arco_point(ds)
    except Exception as exc:
        # Never report provider URLs with request Authorization header or tokens.
        raise RuntimeError(
            "official authenticated ARCO Zarr point could not be read "
            f"({type(exc).__name__}); credentials and provider exception suppressed"
        ) from None
    result=compare_original_and_arco(original,source)
    result.update({
        "schema_version":SCHEMA,
        "year":2023,"month":1,
        "original_source_month_netCDF_SHA256":filehash(original_jan),
        "source_dataset":"Copernicus ERA5 ARCO single-levels 0.25 degree geo-chunked",
        "source_url":ARCO_URL,
        "official_source_metadata":"Copernicus ARCO PUG updated 2026-08-05",
        "ARCO_raw_variable_identifiers":roles,
        "ARCO_selected_grid_point":grid,
        "elapsed_seconds":round(time.monotonic()-begin,1),
        "full_original_year_provider_equivalence_ESTABLISHED":False,
        "replacing_CDS_originals_without_annual_2023_replay_permitted":False,
    })
    result["status"]=(
        "JAN2023_1W_CALIBRATION_PASS_ONLY_FULL_YEAR_NOT_YET_VALIDATED"
        if result["ARCO_Jan2023_wind_1W_quantized_matches_original_CDS_for_every_hour"]
        else "JAN2023_ARCO_VS_ORIGINAL_CDS_NUMERICALLY_DIFFERENT_STOP"
    )
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",
                      encoding="utf-8")
    print("ARCO_2023_JAN_COMPARISON",result["status"],
          "hours=744",
          "max_abs_farm_delta_MW="+str(result["max_abs_modelled_wind_farm_difference_MW"]),
          "elapsed_seconds="+str(result["elapsed_seconds"]),flush=True)
    return result


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--original-jan",required=True,help="original protected October 2026 2023-01 PyNEXUS CDS monthly NetCDF")
    ap.add_argument("--output",required=True,help="new private provenance report, no hourly arrays")
    args=ap.parse_args(argv)
    result=run_pilot(args.original_jan,args.output)
    if not result["ARCO_Jan2023_wind_1W_quantized_matches_original_CDS_for_every_hour"]:
        raise SystemExit(2)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
