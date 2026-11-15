"""ERA5 monthly sharded retrieval and byte-traceable annual assembly.

Critical remediation: ERA5 CDS monthly requests can take 60-100+ minutes.
A serial 12-month 340-minute GitHub Action was cancelled after April 2023
despite four valid API retrievals. Use one job per month, preserving exact
raw provider bytes and never claiming an accepted 2023 calibration unless
the *entire* 8760h wind SHA matches the frozen PyNEXUS benchmark.

Secrets and original NetCDF are NEVER printed or committed; download
artifacts remain private and short-lived, not durable storage.
"""
from __future__ import annotations

import argparse
import calendar
import csv
from datetime import datetime,timezone,timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

from .f3d_live_era5 import (
    YEARS,EXPECTED_2023_WIND_F64_SHA,REFERENCE_LAT,REFERENCE_LON,
    FARM_LIMIT_MW,EXPECTED_2023_WIND_MICROMW_SHA,request_for,load_original_month,f64sha,micro_mw_source_sha
)

SOURCE="Copernicus ERA5 reanalysis-era5-single-levels"
MONTHLY_SCHEMA="ptxflex.f3d_era5_original_month_job.v1"
ANNUAL_SCHEMA="ptxflex.f3d_era5_100m_120m_native_original_monthly_source.v1"


def require(ok,msg):
    if not ok:raise ValueError("ERA5 monthly recovery: "+msg)


def filehash(p):
    digest=hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()


def original_filename(year,month):
    require(year in YEARS and type(month) is int and 1<=month<=12,
            "unsupported original ERA5 calendar")
    return f"era5_{year}_{month:02d}_u10_v10_u100_v100.nc"


def verified_month_from_bytes(path,year,month):
    """Verified 10/100m hourly NetCDF; no relabelling of a synthetic year."""
    wind,details=load_original_month(path,year,month)
    expected_hours=calendar.monthrange(year,month)[1]*24
    require(len(wind)==expected_hours,"original ERA5 monthly calendar mismatch")
    return {
        "filename":original_filename(year,month),
        "sha256":filehash(path),
        "bytes":Path(path).stat().st_size,
        "cds_request":request_for(year,month),
        **details
    },wind


def acquire_month(year,month,output):
    """One network retrieval, one independently checkable original artifact."""
    output=Path(output).resolve()
    require(not output.exists(),"do not overwrite a provider original month")
    key=os.getenv("ERA5_API_KEY","").strip()
    require(len(key)>10,"ERA5_API_KEY secret not available")
    root=output/"original_monthly_netcdf"
    root.mkdir(parents=True,exist_ok=False)
    target=root/original_filename(year,month)
    report={
        "schema_version":MONTHLY_SCHEMA,
        "year":year,"month":month,
        "status":"SOURCE_REQUESTED_NOT_YET_VERIFIED",
        "raw_source":"reanalysis-era5-single-levels",
        "provider":"Copernicus Climate Data Store",
        "source_month_original_files":[],
        "original_provider_licence_and_redistribution_require_review":True,
        "annual_2023_wind_calibration_certified":False,
        "v1_0_source_release_certified":False,
    }
    begin=time.monotonic()
    try:
        import cdsapi
        print(f"CDS_API_CALL_START year={year} month={month:02d} dataset=reanalysis-era5-single-levels "
              "request=original_10m_100m_four_variables; SECRET_NOT_LOGGED",flush=True)
        try:
            client=cdsapi.Client(url="https://cds.climate.copernicus.eu/api",
                                 key=key,quiet=True,progress=False)
            client.retrieve("reanalysis-era5-single-levels",request_for(year,month),str(target))
        except Exception as exc:
            # CDS errors and URLs can accidentally expose bearer authentication.
            raise RuntimeError(f"CDS provider request did not complete for {year}-{month:02d}"
                               f" ({type(exc).__name__}); credential details suppressed") from None
        entry,values=verified_month_from_bytes(target,year,month)
        report["source_month_original_files"]=[entry]
        report["status"]="MONTH_NATIVE_NETCDF_AND_UTC_CALENDAR_VERIFIED_NOT_YEAR"
        report["verified_hour_count"]=len(values)
        report["original_month_f64_wind_sha256"]=f64sha(values)
        report["elapsed_seconds"]=round(time.monotonic()-begin,1)
        print(f"CDS_API_CALL_AND_SOURCE_VERIFIED year={year} month={month:02d}"
              f" hours={len(values)} bytes={entry['bytes']} sha256={entry['sha256']}"
              f" elapsed_seconds={report['elapsed_seconds']}",flush=True)
        return report
    finally:
        # Cancellation or runner timeout may prevent this block; raw NetCDF is
        # still uploaded if present, but remains UNVERIFIED without source metadata.
        (output/"month_provenance.json").write_text(
            json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n",
            encoding="utf-8")


def assemble_year(year,input_root,output_root):
    """Exact 12 ORIGINAL monthly NetCDF files -> paired-data-compatible year."""
    require(year in YEARS,"unregistered original ERA5 year")
    input_root=Path(input_root).resolve(strict=True)
    output_root=Path(output_root).resolve()
    require(input_root.is_dir() and not output_root.exists(),"source folder invalid or target already exists")
    require(not output_root.is_relative_to(input_root) and
            not input_root.is_relative_to(output_root),
            "original inputs and annual output must not contain one another")
    raw=input_root/"original_monthly_netcdf"
    require(raw.is_dir() and not raw.is_symlink(),"original monthly NetCDF directory absent")
    expected={original_filename(year,m) for m in range(1,13)}
    actual={x.name for x in raw.iterdir()}
    require(actual==expected,
            "year-original ERA5 raw month set must be exactly 12; absent/extra months rejected")
    report={
        "schema_version":ANNUAL_SCHEMA,
        "source":SOURCE,
        "reference_lat":REFERENCE_LAT,"reference_lon":REFERENCE_LON,
        "source_monthly_files":[],
        "year":year,"status":"INCOMPLETE_ORIGINAL_ERA5_SOURCE_COLLECTION",
        "original_2023_wind_float64_reference_match":None,
        "original_2023_wind_microMW_reference_match":None,
        "original_2023_frozen_PyNEXUS_float64_SHA256":EXPECTED_2023_WIND_F64_SHA,
        "complete_industrial_site_validation":False,
        "native_ERA5_is_weather_reanalysis_not_plant_measurement":True,
        "original_PyNEXUS_100m_to_120m_alpha":0.11,
        "source_turbine_max_usable_mw":FARM_LIMIT_MW,
        "full_F3D_source_admission_or_v1_release":False,
        "origin":"MONTH_SHARDED_AUTHENTIC_CDS_ORIGINALS_WITH_INDEPENDENT_RAW_SHA_AND_UTC_REASSEMBLY",
        "source_ACQUIRED_NOT_equivalent_to_industrial_H2_data":True
    }
    rawout=output_root/"original_monthly_netcdf"
    rawout.mkdir(parents=True,exist_ok=False)
    values=[]
    try:
        for month in range(1,13):
            filename=original_filename(year,month)
            item=raw/filename
            require(item.is_file() and not item.is_symlink() and item.stat().st_size>100,
                    "source original month is missing, invalid or symlinked")
            entry,part=verified_month_from_bytes(item,year,month)
            # Keep source-original bytes unchanged; no re-export, interpolation or averaging.
            dest=rawout/filename
            shutil.copyfile(item,dest,follow_symlinks=False)
            require(filehash(dest)==entry["sha256"],"copied original monthly NetCDF hash changed")
            report["source_monthly_files"].append(entry)
            values.extend(part.tolist())
            print(f"YEAR_SOURCE_RAW_MONTH_VERIFIED year={year} month={month:02d}"
                  f" hours={len(part)} sha256={entry['sha256']}",flush=True)
        require(len(values)==YEARS[year],"year UTC hours missing or leap day truncated")
        digest=f64sha(values)
        micro_digest=micro_mw_source_sha(values)
        exact_f64=(digest==EXPECTED_2023_WIND_F64_SHA if year==2023 else None)
        same_1W=(micro_digest==EXPECTED_2023_WIND_MICROMW_SHA if year==2023 else None)
        report.update({
            "annual_utc_hours":len(values),
            "normalized_wind_float64_SHA256":digest,
            "normalized_wind_1W_quantized_SHA256":micro_digest,
            "original_2023_wind_float64_reference_match":exact_f64,
            "original_2023_wind_microMW_reference_match":same_1W,
            "full_UTC_calendar_year_no_gaps":True,
            "status":"SOURCE_RECONSTRUCTED_NOT_EXTERNALLY_REVIEWED"
        })
        if year==2023 and not same_1W:
            report["status"]="2023_ORIGINAL_SOURCE_WIND_NUMERICAL_REPRODUCTION_FAILED"
            raise ValueError("2023 original ERA5 source does NOT reproduce original "
                             "PyNEXUS source to 1W quantized resolution; do not promote external years")
        with (output_root/"normalized_UTC_wind.csv").open("w",encoding="utf-8",newline="") as f:
            writer=csv.writer(f)
            writer.writerow(["timestamp_utc","wind_available_mw"])
            first=datetime(year,1,1,tzinfo=timezone.utc)
            for i,v in enumerate(values):
                writer.writerow([(first+timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                 format(v,".17g")])
        report["normalized_csv_SHA256"]=filehash(output_root/"normalized_UTC_wind.csv")
        print(f"ERA5_UTC_YEAR_ASSEMBLED year={year} hours={len(values)}"
              f" original_2023_1W_reference_match={same_1W} source_f64_sha256={digest}",flush=True)
        return report
    finally:
        (output_root/"provenance.json").write_text(
            json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n",
            encoding="utf-8")


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year",required=True,type=int,choices=sorted(YEARS))
    sub=ap.add_mutually_exclusive_group(required=True)
    sub.add_argument("--month",type=int,help="Retrieve ONE genuine CDS NetCDF month")
    sub.add_argument("--assemble-input",help="Verify 12 original NetCDF months, build complete UTC year")
    ap.add_argument("--output",required=True)
    a=ap.parse_args(argv)
    if a.month is not None:
        report=acquire_month(a.year,a.month,a.output)
    else:
        report=assemble_year(a.year,a.assemble_input,a.output)
    print("ERA5 month-sharded status:",report["status"],"year",a.year)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
