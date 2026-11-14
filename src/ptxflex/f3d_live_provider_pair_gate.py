"""Private provider artifacts: strict full-year pair admission candidate gate.

Never promotes 2022/2024 to scientific observations if 2023 reproduction fails,
and never exposes licensed hourly arrays via GitHub commits or console output.
This is a provider-source and calendar gate, NOT H2 optimization review.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone,timedelta
import csv
import math
import struct
import hashlib
import json
from pathlib import Path

from .f3d_external_observed_year_private_intake import (
    validate_hourly_csv,MAX_WIND_MW,YEARS,
    REFERENCE_2023_WIND_SHA,REFERENCE_2023_PRICE_SHA
)
from .f3d_live_entsoe import FROZEN_2023_PRICE_F64_SHA, months_bracketing_year


def check(ok,reason):
    if not ok:raise ValueError("F3D provider pair source gate: "+reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_2023_csv(path,metric,cap=None):
    """Independent calibration of frozen 2023 f64 SHA; intake gate excludes 2023."""
    start=datetime(2023,1,1,tzinfo=timezone.utc)
    digest=hashlib.sha256()
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        check(r.fieldnames==["timestamp_utc",metric],"2023 normalized source fields invalid")
        count=0
        for row in r:
            check(count<8760,"2023 source has excess hours")
            expected=(start+timedelta(hours=count)).strftime("%Y-%m-%dT%H:%M:%SZ")
            check(row["timestamp_utc"]==expected,"2023 source has missing/repeated UTC hours")
            v=float(row[metric])
            check(math.isfinite(v) and (cap is None or 0<=v<=cap+1e-8),
                  "2023 source has unphysical or missing price/wind")
            digest.update(struct.pack("<d",v))
            count+=1
    check(count==8760,"2023 source missing hours")
    return {"hours":count,"float64_le_sha256":digest.hexdigest()}


def verify_one(folder,year,kind):
    folder=Path(folder)
    path=folder/"provenance.json"
    data=json.loads(path.read_text())
    check(data.get("year")==year,kind+" provider year mismatch")
    if kind=="price":
        check(data.get("schema_version")=="ptxflex.f3d_entsoe_native_monthly_price_source.v1", "wrong original A44 price source")
        docs=data.get("raw_monthly_documents")
        check(len(docs)==14,"A44 must have all 14 original bracketing months")
        expected=["NL_A44_"+str(y)+str(m).zfill(2)+".xml" for y,m in months_bracketing_year(year)]
        check([x["filename"] for x in docs]==expected,"unexpected A44 original month sequence")
        provider_dir=folder/"original_xml"
        normalized=folder/"normalized_UTC_price.csv"
        metric="day_ahead_eur_mwh"
        cap=None
        recorded=data.get("float64_little_endian_SHA256")
        check(data.get("status")=="UTC_SOURCE_RECONSTRUCTED_NOT_EXTERNALLY_REVIEWED","original XML source incomplete")
        if year==2023:
            check(data.get("original_2023_float64_reference_match") is True and recorded==REFERENCE_2023_PRICE_SHA==FROZEN_2023_PRICE_F64_SHA,
                  "original 2023 Dutch A44 calendar not calibrated")
    else:
        check(data.get("schema_version")=="ptxflex.f3d_era5_100m_120m_native_original_monthly_source.v1",
              "wrong native ERA5 wind source")
        docs=data.get("source_monthly_files")
        check(len(docs)==12,"ERA5 must have 12 original NetCDF months")
        expected=[f"era5_{year}_{m:02d}_u10_v10_u100_v100.nc" for m in range(1,13)]
        check([x["filename"] for x in docs]==expected,"ERA5 source month sequence not registered")
        provider_dir=folder/"original_monthly_netcdf"
        normalized=folder/"normalized_UTC_wind.csv"
        metric="wind_available_mw"
        cap=MAX_WIND_MW
        recorded=data.get("normalized_wind_float64_SHA256")
        check(data.get("status")=="SOURCE_RECONSTRUCTED_NOT_EXTERNALLY_REVIEWED",
              "native ERA5 source incomplete")
        if year==2023:
            check(data.get("original_2023_wind_float64_reference_match") is True and recorded==REFERENCE_2023_WIND_SHA,
                  "ERA5 2023 wind-to-power source pipeline not calibrated")
    for item in docs:
        p=provider_dir/item["filename"]
        check(p.is_file() and not p.is_symlink() and sha(p)==item["sha256"] and
              p.stat().st_size==item["bytes"],kind+" provider original SHA/size mismatch")
    check(sha(normalized)==data["normalized_csv_SHA256"],kind+" normalized CSV SHA mismatch")
    validated=(validate_2023_csv(normalized,metric,cap=cap) if year==2023 else
               validate_hourly_csv(normalized,year,metric,cap=cap))
    check(validated["hours"]==(8760 if year==2023 else YEARS[year]),
          kind+" invalid original year hours")
    check(validated["float64_le_sha256"]==recorded,
          kind+" normalized CSV floats differ from original A44/ERA5 provenance")
    return {"original_documents_count":len(docs),
            "normalized_float64_sha256":recorded,
            "original_file_sha256":[x["sha256"] for x in docs],
            "full_UTC_hours":validated["hours"],
            "normalized_csv_sha256":data["normalized_csv_SHA256"]}


def verify_pair(year,price_root,wind_root,reference_price_root,reference_wind_root):
    check(year in YEARS,"unsupported external source year")
    baseline_price=verify_one(reference_price_root,2023,"price")
    baseline_wind=verify_one(reference_wind_root,2023,"wind")
    price=verify_one(price_root,year,"price")
    wind=verify_one(wind_root,year,"wind")
    check(price["full_UTC_hours"]==wind["full_UTC_hours"] and
          price["full_UTC_hours"]==YEARS[year],
          "missing or unequal provider UTC hours")
    return {
        "schema_version":"oem.ptx.f3d_native_provider_price_wind_source_pair_candidate.v1",
        "year":year,
        "expected_full_UTC_hours":YEARS[year],
        "actual_2023_original_price_reproduction":baseline_price["normalized_float64_sha256"]==REFERENCE_2023_PRICE_SHA,
        "actual_2023_original_wind_reproduction":baseline_wind["normalized_float64_sha256"]==REFERENCE_2023_WIND_SHA,
        "year_price":price,
        "year_wind":wind,
        "source_price_and_weather_calendar_and_original_hashes_verified":True,
        "private_original_provider_files_retained_in_ephemeral_runner_not_durable_escrow":True,
        "actual_industrial_plant_hydrogen_measurements_present":False,
        "full_original_H2_customer_delivery_service_model_verified":False,
        "matched_year_E_vs_ES_reoptimization_with_primal_and_dual_bounds_completed":False,
        "independent_external_source_and_physical_reviewer_signed":False,
        "modelled_wholesale_advantage_permitted_from_source_retrieval_alone":False,
        "full_LCA_TEA_v1_0_release_allowed":False,
        "no_original_hourly_price_or_wind_array_in_public_certificate":True,
    }


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--year",type=int,required=True)
    ap.add_argument("--price-root",required=True)
    ap.add_argument("--wind-root",required=True)
    ap.add_argument("--reference-price-root",required=True)
    ap.add_argument("--reference-wind-root",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args(argv)
    dest=Path(a.output)
    check(not dest.exists(),"source certificate already exists")
    result=verify_pair(a.year,a.price_root,a.wind_root,a.reference_price_root,a.reference_wind_root)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("SOURCE CALENDAR/HASH VERIFIED:",result["year"],result["expected_full_UTC_hours"],
          "hours; no H2 matched-service or v1 certification")


if __name__=="__main__":
    main()
