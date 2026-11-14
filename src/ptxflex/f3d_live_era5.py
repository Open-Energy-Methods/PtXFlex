"""Retrieve original ERA5 monthly 10m/100m wind fields and reconstruct PyNEXUS.

Credential is supplied as ERA5_API_KEY in private CI (mapped to CDSAPI_KEY).
Data are written only under a PRIVATE, ephemeral runner workspace, never Git.
No external 2022/2024 year is source-admitted before exact 2023 calibration.
"""
from __future__ import annotations
import argparse
import calendar
import csv
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import struct

import numpy as np

YEARS={2022:8760,2023:8760,2024:8784}
EXPECTED_2023_WIND_F64_SHA="abbfea17224cd92f694ed26b7a179ef7e35fff5a5bb17c6ee060a674c1977717"
ERA5_VARIABLES=["10m_u_component_of_wind","10m_v_component_of_wind",
                "100m_u_component_of_wind","100m_v_component_of_wind"]
REFERENCE_LAT=52.5
REFERENCE_LON=3.5
FARM_LIMIT_MW=125.685


def check(condition,description):
    if not condition: raise ValueError(description)


def request_for(year,month):
    check(year in YEARS and 1<=month<=12,"unsupported ERA5 observed calendar")
    return {
        "product_type":["reanalysis"],
        "variable":list(ERA5_VARIABLES),
        "year":[str(year)],
        "month":[f"{month:02d}"],
        "day":[f"{d:02d}" for d in range(1,calendar.monthrange(year,month)[1]+1)],
        "time":[f"{h:02d}:00" for h in range(24)],
        # Explicit original offshore source grid. Never substitute a site.
        "area":[52.75,3.25,52.25,3.75],
        "data_format":"netcdf",
        "download_format":"unarchived",
    }


def original_farm_mw_from_u100_v100(u100,v100):
    """Original 100m-to-120m shear and PyNEXUS cubic ten-turbine curve."""
    u=np.asarray(u100,dtype=np.float64)
    v=np.asarray(v100,dtype=np.float64)
    check(u.shape==v.shape and u.ndim==1 and np.isfinite(u).all()
          and np.isfinite(v).all(),"invalid original 100m wind field")
    hub=np.sqrt(u*u+v*v)*(120.0/100.0)**0.11
    def unit(t):
        if t<3.0 or t>=25.0:return 0.0
        if t>=13.0:return 15.0
        return 15.0*(t**3-3.0**3)/(13.0**3-3.0**3)
    per_turbine=np.fromiter((unit(float(x)) for x in hub),dtype=np.float64,count=len(hub))
    farm=per_turbine*10.0*(1.0-0.10)*(1.0-0.02)*(1.0-0.05)
    check(np.isfinite(farm).all() and np.min(farm)>=0 and np.max(farm)<=FARM_LIMIT_MW+1e-9,
          "ERA5 source turbine MW exceeds physical farm limit")
    return farm


def _extract_series(ds,name):
    """Only one accepted source value per UTC hour; no silent averaging."""
    check(name in ds.data_vars,"ERA5 missing source u/v variable "+name)
    a=ds[name]
    if "expver" in a.dims and a.sizes.get("expver",0)>1:
        # Reanalysis expver=1 and temporary expver=5 may coexist in files.
        # Select the finite single point per timestamp, rejecting ambiguous
        # competing data or missing values (do not fill or interpolate).
        raw=np.asarray(a.transpose("expver",...).values,dtype=np.float64)
        check(raw.ndim==2,"unsupported ERA5 expver-plus-time dimensions")
        valid=np.isfinite(raw)
        check((valid.sum(axis=0)==1).all(),
              "ERA5 expver values ambiguous or missing at an hour")
        vals=np.sum(np.where(valid,raw,0.),axis=0)
    else:
        vals=np.asarray(a.squeeze().values,dtype=np.float64)
    check(vals.ndim==1 and np.isfinite(vals).all(),
          "ERA5 source wind variable missing, ambiguous or non-1D")
    return vals


def load_original_month(path,year,month):
    """Verified NetCDF with correct grid point, UTC hours and original units."""
    import pandas as pd
    import xarray as xr
    check(Path(path).is_file() and Path(path).stat().st_size>100,
          "CDS returned empty source NetCDF")
    with xr.open_dataset(path) as ds:
        lat="latitude" if "latitude" in ds.coords else "lat"
        lon="longitude" if "longitude" in ds.coords else "lon"
        check(lat in ds.coords and lon in ds.coords,"missing ERA5 geographic coordinates")
        point=ds.sel({lat:REFERENCE_LAT,lon:REFERENCE_LON},method="nearest")
        at_lat=float(np.asarray(point[lat]).item())
        at_lon=float(np.asarray(point[lon]).item())
        check(abs(at_lat-REFERENCE_LAT)<1e-8 and abs(at_lon-REFERENCE_LON)<1e-8,
              "ERA5 source grid is not original North Sea reference point")
        axis="valid_time" if "valid_time" in point.coords else "time"
        check(axis in point.coords,"ERA5 source UTC time axis missing")
        moments=pd.to_datetime(point[axis].values,utc=True)
        n=calendar.monthrange(year,month)[1]*24
        expected=pd.date_range(f"{year}-{month:02d}-01",periods=n,freq="h",tz="UTC")
        check(moments.equals(expected),"ERA5 source month has missing, extra or shifted UTC hours")
        u10=_extract_series(point,"u10")
        v10=_extract_series(point,"v10")
        u100=_extract_series(point,"u100")
        v100=_extract_series(point,"v100")
    check(all(len(x)==n for x in (u10,v10,u100,v100)),
          "ERA5 variable year-month length mismatch")
    wind=original_farm_mw_from_u100_v100(u100,v100)
    return wind,{"source_grid_latitude":at_lat,"source_grid_longitude":at_lon,
                 "month_UTC_hours":n,"u10_v10_u100_v100_complete":True}


def f64sha(values):
    return hashlib.sha256(np.asarray(values,dtype="<f8").tobytes()).hexdigest()


def acquire(year,output_root):
    check(year in YEARS,"unregistered source observed year")
    key=os.environ.get("ERA5_API_KEY","").strip()
    check(key and len(key)>10,"ERA5_API_KEY organization secret unavailable to this repository")
    output_root=Path(output_root).resolve()
    check(not output_root.exists(),"do not overwrite original ERA5 dataset")
    rawdir=output_root/"original_monthly_netcdf"
    rawdir.mkdir(parents=True,exist_ok=False)
    report={
        "schema_version":"ptxflex.f3d_era5_100m_120m_native_original_monthly_source.v1",
        "source":"Copernicus ERA5 reanalysis-era5-single-levels",
        "reference_lat":REFERENCE_LAT,"reference_lon":REFERENCE_LON,
        "source_monthly_files":[],
        "year":year,"status":"INCOMPLETE_ORIGINAL_ERA5_SOURCE_COLLECTION",
        "original_2023_wind_float64_reference_match":None,
        "complete_industrial_site_validation":False,
        "native_ERA5_is_weather_reanalysis_not_plant_measurement":True,
        "original_PyNEXUS_100m_to_120m_alpha":0.11,
        "source_turbine_max_usable_mw":FARM_LIMIT_MW,
        "full_F3D_source_admission_or_v1_release":False
    }
    try:
        import cdsapi
        # Hide network/credential exception messages: cdsapi may embed URLs.
        client=cdsapi.Client(url="https://cds.climate.copernicus.eu/api",
                             key=key,quiet=True,progress=False)
        output=[]
        for month in range(1,13):
            request=request_for(year,month)
            target=rawdir/f"era5_{year}_{month:02d}_u10_v10_u100_v100.nc"
            try:
                client.retrieve("reanalysis-era5-single-levels",request,str(target))
            except Exception as exc:
                raise RuntimeError(f"CDS ERA5 fetch unavailable for {year}-{month:02d} "+
                                   f"({type(exc).__name__}); original provider details suppressed") from None
            wind,details=load_original_month(target,year,month)
            report["source_monthly_files"].append({
                "filename":target.name,"sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
                "bytes":target.stat().st_size,"cds_request":request,**details
            })
            output.extend(wind.tolist())
            print("Verified ERA5 raw month",year,month,len(wind),"hours",flush=True)
        check(len(output)==YEARS[year],"ERA5 annual hourly coverage invalid")
        sha=f64sha(output)
        match=sha==EXPECTED_2023_WIND_F64_SHA if year==2023 else None
        report.update({
            "annual_utc_hours":len(output),"normalized_wind_float64_SHA256":sha,
            "original_2023_wind_float64_reference_match":match,
            "status":"SOURCE_RECONSTRUCTED_NOT_EXTERNALLY_REVIEWED",
            "full_UTC_calendar_year_no_gaps":True,
        })
        if year==2023:
            check(match,"2023 ERA5 source wind does NOT match frozen PyNEXUS source SHA; investigate provider revision, variable, grid and power curve")
        with (output_root/"normalized_UTC_wind.csv").open("w",encoding="utf-8",newline="") as f:
            writer=csv.writer(f)
            writer.writerow(["timestamp_utc","wind_available_mw"])
            first=datetime(year,1,1,tzinfo=timezone.utc)
            for hour,v in enumerate(output):
                writer.writerow([(first+timedelta(hours=hour)).strftime("%Y-%m-%dT%H:%M:%SZ"),format(v,".17g")])
        report["normalized_csv_SHA256"]=hashlib.sha256(
            (output_root/"normalized_UTC_wind.csv").read_bytes()).hexdigest()
        return report
    finally:
        (output_root/"provenance.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--year",type=int,required=True,choices=sorted(YEARS))
    ap.add_argument("--output",required=True)
    args=ap.parse_args(argv)
    report=acquire(args.year,args.output)
    print(json.dumps({k:v for k,v in report.items() if k!="source_monthly_files"},
                     indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
