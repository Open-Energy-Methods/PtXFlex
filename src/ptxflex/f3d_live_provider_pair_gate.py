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
from .f3d_live_era5 import EXPECTED_2023_WIND_MICROMW_SHA


def check(ok,reason):
    if not ok:raise ValueError("F3D provider pair source gate: "+reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_2023_csv(path,metric,cap=None):
    """Independent calibration of frozen 2023 f64 SHA; intake gate excludes 2023."""
    start=datetime(2023,1,1,tzinfo=timezone.utc)
    digest=hashlib.sha256()
    micro_wind_digest=hashlib.sha256()
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
            if metric=="wind_available_mw":
                micro_wind_digest.update(struct.pack("<q",round(v*1000000.0)))
            count+=1
    check(count==8760,"2023 source missing hours")
    return {"hours":count,"float64_le_sha256":digest.hexdigest(),
            "wind_1W_quantized_sha256":micro_wind_digest.hexdigest() if metric=="wind_available_mw" else None}


def verify_arco_alternate_year(folder,year,manifest):
    """Independently rehash actual ARCO 4-wind-field private annual snapshot.

    A real ARCO geo-chunked original source representation is NOT a 12-NC
    monthly CDS download. The original 2023 CDS reference must have passed
    independently, and its 8760-hour ARCO equivalence receipt is replayed
    as a separate, privately stored, SHA-verified proof, not merely a flag.
    """
    import numpy as np
    import xarray as xr
    from .f3d_era5_arco_year import (
        SCHEMA_YEAR,SCHEMA_CAL,CAL_ACCEPTED_STATUS,ARCO_ACCEPTED_STATUS,
        ARCO_SNAPSHOT_NAME,ARCO_URL,sha_array,require_exact_calendar,
        original_farm_mw_from_u100_v100,f64sha,micro_mw_source_sha,
    )
    from .f3d_era5_sharded_acquisition import PY_NEXUS_RECOVERED_2023_MONTH_SHA
    folder=Path(folder)
    check(year in (2022,2024) and
          manifest.get("schema_version")==SCHEMA_YEAR and
          manifest.get("status")==ARCO_ACCEPTED_STATUS and
          manifest.get("year")==year and
          manifest.get("source_url")==ARCO_URL and
          manifest.get("source_CDS_netCDF_monthly_original") is False and
          manifest.get("source_ERA5_single_level_ARCO_repackaged_product") is True and
          manifest.get("full_UTC_calendar_year_no_gaps") is True and
          manifest.get("annual_UTC_hours")==YEARS[year] and
          manifest.get("original_source_calendar_UTC_hours")==YEARS[year] and
          manifest.get("complete_industrial_site_validation") is False and
          manifest.get("whole_plant_LCA_TEA_or_methanol_economic_release_allowed") is False,
          "ARCO annual original provider classification, scope or UTC hours invalid")

    original_cal=folder/"ARCO_2023_original_CDS_calibration_receipt.json"
    check(original_cal.is_file() and not original_cal.is_symlink() and
          sha(original_cal)==manifest.get("source_2023_full_calibration_file_SHA256"),
          "actual original 2023 CDS-to-ARCO full calibration receipt SHA missing")
    cal=json.loads(original_cal.read_text(encoding="utf-8"))
    check(cal.get("schema_version")==SCHEMA_CAL and
          cal.get("status")==CAL_ACCEPTED_STATUS and
          cal.get("year")==2023 and
          cal.get("source_url")==ARCO_URL and
          cal.get("original_2023_1W_sha256_from_source_months")==EXPECTED_2023_WIND_MICROMW_SHA and
          cal.get("ARCO_2023_1W_sha256")==EXPECTED_2023_WIND_MICROMW_SHA and
          cal.get("modelled_wind_1W_identical_hours")==8760 and
          cal.get("full_8760h_2023_ARCO_matches_CDS_model_at_1W_and_four_component_tolerance") is True and
          cal.get("original_source_calendar_UTC_hours")==8760 and
          all(v is True for v in cal.get("component_equivalence_within_1e_minus_5_m_per_s",{}).values()) and
          len(cal.get("component_equivalence_within_1e_minus_5_m_per_s",{}))==4,
          "full 2023 source reanalysis from original CDS monthly fields to ARCO is not certified")
    originals=cal.get("original_2023_PyNEXUS_monthly_CDS_SHA256",{})
    check(set(originals)=={str(i) for i in range(1,13)} and
          all(originals[str(i)].get("sha256")==PY_NEXUS_RECOVERED_2023_MONTH_SHA[i]
              for i in range(1,13)),
          "2023 ARCO proof lacks exact twelve frozen CDS original monthly SHA anchors")

    snapshot=folder/ARCO_SNAPSHOT_NAME.format(year=year)
    check(snapshot.is_file() and not snapshot.is_symlink() and
          sha(snapshot)==manifest.get("source_point_netCDF_snapshot_SHA256"),
          "actual ARCO provider point NetCDF snapshot bytes changed")
    src=manifest.get("source_coordinates_and_variables",{})
    check(src.get("latitude")==52.5 and src.get("longitude")==3.5 and
          set(src.get("field_names",{}))=={"u10","v10","u100","v100"} and
          set(manifest.get("source_raw_ARCO_point_component_sha256",{}))==
          {"u10","v10","u100","v100"},
          "ARCO source point/field audit not identical to original PyNEXUS site representation")
    with xr.open_dataset(snapshot) as ds:
        check(set(ds.data_vars)=={"u10","v10","u100","v100"} and
              ds.attrs.get("source_URL")==ARCO_URL and
              float(ds.attrs.get("lat",0))==52.5 and
              float(ds.attrs.get("lon",0))==3.5 and
              ds.attrs.get("native_CDS_monthly_original")=="false",
              "ARCO source snapshot not original reanalysis point extraction")
        require_exact_calendar(ds["time"].values,year)
        arrays={name:np.asarray(ds[name].values) for name in
                ("u10","v10","u100","v100")}
    for name,arr in arrays.items():
        check(arr.shape==(YEARS[year],) and np.isfinite(arr).all() and
              sha_array(arr)==manifest["source_raw_ARCO_point_component_sha256"][name] and
              str(arr.dtype)==manifest["source_raw_ARCO_point_component_dtype"][name],
              "ARCO "+name+" native-component SHA/dtype/UTC hours inconsistent")
    wind=original_farm_mw_from_u100_v100(arrays["u100"],arrays["v100"])
    check(f64sha(wind)==manifest.get("normalized_wind_float64_SHA256") and
          micro_mw_source_sha(wind)==manifest.get("normalized_wind_1W_quantized_SHA256"),
          "independent ARCO 120m model from original 100m wind vectors differs from annual source")
    normalized=folder/"normalized_UTC_wind.csv"
    check(normalized.is_file() and not normalized.is_symlink() and
          sha(normalized)==manifest.get("normalized_csv_SHA256"),
          "ARCO normalized year hourly source CSV SHA changed")
    independently=validate_hourly_csv(normalized,year,"wind_available_mw",cap=MAX_WIND_MW)
    check(independently["hours"]==YEARS[year] and
          independently["float64_le_sha256"]==f64sha(wind),
          "ARCO reconstructed 2022/2024 hourly source CSV differs from archived NetCDF")
    return {
        "original_documents_count":1,
        "normalized_float64_sha256":manifest["normalized_wind_float64_SHA256"],
        "original_file_sha256":[manifest["source_point_netCDF_snapshot_SHA256"]],
        "full_UTC_hours":YEARS[year],
        "normalized_csv_sha256":manifest["normalized_csv_SHA256"],
        "wind_provider_representation":"OFFICIAL_CDS_ARCO_GEOCHUNKED_REPACKAGED_ERA5_POINT_NOT_MONTHLY_CDS_NETCDF",
        "full_2023_original_CDS_to_ARCO_8760h_calibration_receipt_sha256":
            manifest["source_2023_full_calibration_file_SHA256"],
        "actual_original_2022_2024_ARCO_historical_hourly_source_snapshot_verified":True,
        "original_2023_CDS_is_separate_from_alternative_2022_2024_ARCO_product":True,
    }


def verify_one(folder,year,kind):
    folder=Path(folder)
    path=folder/"provenance.json"
    data=json.loads(path.read_text())
    check(data.get("year")==year,kind+" provider year mismatch")
    # ARCO is an explicitly different product representation and must be
    # independently reverified, not mislabelled as 12 native monthly CDS NCs.
    if kind=="wind" and data.get("schema_version")==(
        "ptxflex.f3d_ARCO_hourly_point_year_reanalysis_snapshot.v1"):
        return verify_arco_alternate_year(folder,year,data)
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
            check(data.get("original_2023_wind_microMW_reference_match") is True and
                  data.get("normalized_wind_1W_quantized_SHA256")==EXPECTED_2023_WIND_MICROMW_SHA and
                  data.get("original_2023_frozen_PyNEXUS_float64_SHA256")==REFERENCE_2023_WIND_SHA,
                  "ERA5 2023 source wind does not reproduce original model to 1W precision")
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
    if kind=="wind" and year==2023:
        check(validated["wind_1W_quantized_sha256"]==EXPECTED_2023_WIND_MICROMW_SHA,
              "independent 2023 wind CSV does not match original PyNEXUS 1W SHA")
    return {"original_documents_count":len(docs),
            "normalized_float64_sha256":recorded,
            "original_2023_wind_1W_quantized_SHA256":(
                validated["wind_1W_quantized_sha256"] if kind=="wind" and year==2023 else None),
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
        "actual_2023_original_wind_reproduction":baseline_wind["original_2023_wind_1W_quantized_SHA256"]==EXPECTED_2023_WIND_MICROMW_SHA,
        "2023_original_model_float64_source_sha256":REFERENCE_2023_WIND_SHA,
        "2023_provider_reconstruction_not_asserted_bitwise_equal_to_original":
            baseline_wind["normalized_float64_sha256"]!=REFERENCE_2023_WIND_SHA,
        "2023_source_equivalence_verified_at_1W_quantized_MW_resolution_only":True,
        "year_price":price,
        "year_wind":wind,
        "year_wind_provider_representation":wind.get(
            "wind_provider_representation","ORIGINAL_MONTHLY_CDS_ERA5_NETCDF"),
        "year_wind_alternate_ARCO_calibrated_2023_original_8760h":
            wind.get("actual_original_2022_2024_ARCO_historical_hourly_source_snapshot_verified",False),
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
