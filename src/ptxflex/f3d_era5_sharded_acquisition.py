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
import zipfile
import re

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


# Exact historical recovered provider ZIP from PyNEXUS Oct 2026.
# The 12 NetCDF members are renamed only for normalized local custody; the
# bytes remain untouched and are SHA-checked as each original month.
FROZEN_2023_CDS_RECOVERY_ZIP_SHA = (
    "730a7ae28c450e283f599043452e2fda350ca76f19a68bf62b32dbc0cf00491e"
)


def seed_original_2023_from_pynexus_zip(archive, output_root):
    """Recover original licensed 2023 monthly NetCDFs without CDS calls.

    Strict original SHA, exactly 12 expected source names and source-year
    UTC integrity. Calls assemble_year: original 2023 1-W provenance gate.
    Output is private and contains the complete original source NetCDFs.
    """
    archive=Path(archive).resolve(strict=True)
    root=Path(output_root).resolve()
    require(not root.exists(), "will not overwrite restored source-year original")
    require(archive.is_file() and not archive.is_symlink() and
            filehash(archive)==FROZEN_2023_CDS_RECOVERY_ZIP_SHA,
            "uploaded original PyNEXUS full 2023 monthly ZIP SHA mismatch")
    pattern=re.compile(
        r"^era5_2023-(\d\d)-01_2023-\1-(\d\d)_52\.5_3\.5\.nc$"
    )
    # No zip-slip. Uncompressed original NetCDF each month is bounded.
    orig_parent=root/"_original_months"
    rawdir=orig_parent/"original_monthly_netcdf"
    rawdir.mkdir(parents=True,exist_ok=False)
    try:
        with zipfile.ZipFile(archive) as z:
            files=[p for p in z.infolist() if not p.is_dir()]
            require(len(files)==12,"recovered PyNEXUS annual source lacks exactly 12 original files")
            months={}
            for info in files:
                found=pattern.fullmatch(info.filename)
                require(found is not None and not info.filename.startswith("/"),
                        "unexpected original PyNEXUS ERA5 ZIP member")
                month=int(found.group(1)); last=int(found.group(2))
                require(1<=month<=12 and month not in months and
                        last==calendar.monthrange(2023,month)[1] and
                        100<info.file_size<100_000_000,
                        "original PyNEXUS monthly NetCDF date, size or duplicate invalid")
                dest=rawdir/original_filename(2023,month)
                with z.open(info) as incoming, dest.open("xb") as outgoing:
                    shutil.copyfileobj(incoming,outgoing,1024*1024)
                require(filehash(dest)==hashlib.sha256(dest.read_bytes()).hexdigest(),
                        "recovered monthly source digest failed")
                months[month]=info.filename
            require(set(months)==set(range(1,13)),
                    "original recovered PyNEXUS year missing at least one source month")
        # Create separate completed directory, fail if source vector differs.
        result=assemble_year(2023,orig_parent,root/"complete")
        status={
            "schema_version":"ptxflex.f3d_PyNEXUS_original_2023_recovered_NetCDF_archive.v1",
            "original_PyNEXUS_CDS_artifact_SHA256":FROZEN_2023_CDS_RECOVERY_ZIP_SHA,
            "original_recovered_member_names":{str(k):v for k,v in sorted(months.items())},
            "original_2023_1W_model_calibration":result[
                "original_2023_wind_microMW_reference_match"],
            "original_2023_f64_byte_identity_NOT_claimed":True,
            "source_zip_member_file_bytes_preserved":True,
            "no_new_CDS_api_requests_used":True
        }
        (root/"source_recovery.json").write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
        return result
    except Exception:
        # Never convert invalid partial original into an accepted annual record.
        raise


# Source-archive SHA and per-file original re-delivery hashes are from
# PyNEXUS run 40230838449, artifact 12653508461 and its independent audit.
# A GitHub CLI "run download" extracts original source without preserving ZIP
# container bytes, so these twelve original monthly NetCDF hashes matter.
PY_NEXUS_RECOVERED_2023_MONTH_SHA={
    1:"e0fbd6f67080f1421d50b2d787d9efa7e572d7a2b84c3a1f5b428860096e1d9c",
    2:"2b32ab30219c65ab3285e41b28f235fe1bd272cedaa9bd8ce8e4082b8addd9be",
    3:"a9757eec33d70c0f266c8fa26a850d608a47bdedb567b6babb66cedd65716481",
    4:"b52485f26231edcf02fce05ed9fd77947c5e3e5be14f7a61d27d1a74e31337a8",
    5:"d6291b3f8f7a07460512e33efaf7cdd023bb9850f708e6f48fef1aa9d35a6377",
    6:"a9e0caab5bd574eeac6daea540965cce7400f5968ef94c1aae8b4c2f69d3bd84",
    7:"ae673ac4d66ad8e90216a37f22c456cd6d5e81faabfef790e5ad77c16c5c585d",
    8:"a864f25f67a4e50caac5d6bf84b50fea9771ba414b09ceacd07ce9488847b1a6",
    9:"e6a211b71e58a91130fa12834a8b2949d4cde67df3ba58ab280d31f603cbc80b",
    10:"f1288e0f0eb8d905f1b8605cdd9f6be06984e25404adf721eb0ffdf9e2e7cbe4",
    11:"ed8d644276cdacd8420b68ea949847a448c0a6da98a5d80a7112eb29e0d8f4aa",
    12:"e83ec69c5156e349c632b5e23ec6cb4975452a7b2ed62ae79830f778ef3fc507",
}


def seed_original_2023_from_pynexus_folder(monthly_folder,output_root):
    """Admit byte-exact extracted PyNEXUS original 12 months from GitHub CLI.

    Not a network request. Cross-check EACH actual NetCDF against the source
    archive's independent audit and recompute all 8760 hours. Reject
    incomplete, renamed, mixed or tampered 2023 source months.
    """
    folder=Path(monthly_folder).resolve(strict=True)
    out=Path(output_root).resolve()
    require(folder.is_dir() and not folder.is_symlink() and not out.exists(),
            "source folder must exist; annual output may not overwrite originals")
    require(not out.is_relative_to(folder) and not folder.is_relative_to(out),
            "source and output cannot contain each other")
    original_files={p.name:p for p in folder.iterdir()}
    names={}
    for month in range(1,13):
        last=calendar.monthrange(2023,month)[1]
        original_name=f"era5_2023-{month:02d}-01_2023-{month:02d}-{last:02d}_52.5_3.5.nc"
        names[month]=original_name
    require(set(original_files)==set(names.values()),
            "original PyNEXUS 2023 recovered folder needs exactly 12 original NetCDF filenames")
    rawdir=out/"_original_months"/"original_monthly_netcdf"
    rawdir.mkdir(parents=True,exist_ok=False)
    original_sha={}
    for month in range(1,13):
        p=original_files[names[month]]
        require(p.is_file() and not p.is_symlink() and
                filehash(p)==PY_NEXUS_RECOVERED_2023_MONTH_SHA[month],
                f"source original month 2023-{month:02d} does not match 2026-10-26 PyNEXUS audit")
        target=rawdir/original_filename(2023,month)
        shutil.copyfile(p,target)
        require(filehash(target)==PY_NEXUS_RECOVERED_2023_MONTH_SHA[month],
                "copied original month changed SHA256")
        original_sha[str(month)]=filehash(p)
    result=assemble_year(2023,rawdir.parent,out/"complete")
    record={
       "schema_version":"ptxflex.f3d_2023_exact_PyNEXUS_original_CDS_12_month_GitHub_extraction.v1",
       "original_github_run":40230838449,
       "original_github_artifact":12653508461,
       "original_source_monthly_sha256":original_sha,
       "original_2023_1W_model_reconstruction_PASSED":result["original_2023_wind_microMW_reference_match"],
       "full_original_2023_binary_float64_identity_not_claimed":True,
       "no_fresh_CDS_requests_made":True,
    }
    (out/"source_recovery.json").write_text(
        json.dumps(record,indent=2,sort_keys=True)+"\n",encoding="utf-8"
    )
    return result


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
    sub.add_argument("--seed-original-2023-zip",
                     help="Import exact SHA-frozen 12-month PyNEXUS Oct 2026 original source ZIP; no CDS calls")
    sub.add_argument("--seed-original-2023-folder",
                     help="Import 12 exact original PyNEXUS Oct 2026 NetCDFs extracted by gh run download")
    ap.add_argument("--output",required=True)
    a=ap.parse_args(argv)
    if a.month is not None:
        report=acquire_month(a.year,a.month,a.output)
    elif a.seed_original_2023_zip is not None:
        require(a.year==2023,"frozen original source ZIP only contains 2023")
        report=seed_original_2023_from_pynexus_zip(a.seed_original_2023_zip,a.output)
    elif a.seed_original_2023_folder is not None:
        require(a.year==2023,"original source folder only contains 2023")
        report=seed_original_2023_from_pynexus_folder(a.seed_original_2023_folder,a.output)
    else:
        report=assemble_year(a.year,a.assemble_input,a.output)
    print("ERA5 month-sharded status:",report["status"],"year",a.year)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
