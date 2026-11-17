"""Strict private source admission for real alternative observed historical years.

The 2023 original E/ES PyNEXUS source uses:
  ENTSO-E NL bidding zone A44 observed day-ahead price; local market
  timestamps explicitly converted to complete UTC hourly chronology;
  CDS ERA5 100m u/v wind at (52.5N, 3.5E) offshore resource grid,
  shear exponent 0.11 to 120m, original turbine 15MW×10 cubic curve
  cut-in 3m/s/rated 13m/s/cut-out25m/s; wake 10%, electrical 2%,
  unavailability 5%. 2023 original weather resource NOT a H2 site.

This validator does NOT fetch or publish raw provider datasets; both
ENTSO-E authorization and CDS legal access are external. It checks exact
raw private SHA and source-origin fields and normalized full-year arrays.
2024 MUST contain 8784 UTC hours; source 2023 dispatch MILP only supports
8760 until a separate model-version upgrade. No silent leap-day removal.
A certified observed-year study additionally requires independent 2023
reproduction and reviewer signoff, not just passing a parse-only test.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime,timedelta,timezone
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REGISTER=ROOT/"research/F3_D_ALTERNATIVE_OBSERVED_2022_2024_ENTSOE_ERA5_PRIVATE_SOURCE_ADMISSION_v1.json"
SCHEMA="ptxflex.f3d_private_real_historical_pair_source_date_SHA_admission_candidate.v1"
MANIFEST_SCHEMA="ptxflex.f3d_external_private_provider_original_year_and_reconstructed_2023_sha.v1"
YEARS={2022:8760,2024:8784}
REFERENCE_2023_WIND_SHA="abbfea17224cd92f694ed26b7a179ef7e35fff5a5bb17c6ee060a674c1977717"
REFERENCE_2023_PRICE_SHA="e67f59598079303df0c51a553904d2352a939ed7439af73ccbfb3daab9d667b6"
MAX_WIND_MW=15.*10.*.9*.98*.95
PRICE_PROVIDER="ENTSO-E Transparency Platform A44 day-ahead NL"
WIND_PROVIDER="Copernicus ERA5 reanalysis-era5-single-levels original 100m u/v"


class BadObservedHistoricalSource(ValueError):pass


def req(ok,reason):
    if not ok:raise BadObservedHistoricalSource(reason)


def _hex_sha(value):
    return isinstance(value,str) and len(value)==64 and all(c in "0123456789abcdef" for c in value) and len(set(value))>1


def file_evidence(path,expected_SHA,private_root):
    req(_hex_sha(expected_SHA),"source original raw file SHA256 missing or placeholder")
    p=Path(path).resolve(strict=True)
    root=Path(private_root).resolve(strict=True)
    req(root.is_dir() and root!=ROOT and ROOT not in root.parents and root!=ROOT.parent,
        "provider raw source must live outside public repository tree")
    req(p.is_relative_to(root) and p.is_file() and not Path(path).is_symlink(),
        "original provider raw data must be a private ordinary file, not symlink/alias")
    raw=p.read_bytes()
    req(len(raw)>0 and hashlib.sha256(raw).hexdigest()==expected_SHA,
        "provider raw or hourly normalized source byte fingerprint mismatch")
    return len(raw)


def _hour_string(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_hourly_csv(file_path,year,colname,cap=None,expected_count=None):
    """Only validates local private UTF8 CSV, does not return source arrays."""
    req(year in YEARS,"not an explicitly supported real 2022 or leap-2024 observed year")
    expected=YEARS[year] if expected_count is None else expected_count
    first=datetime(year,1,1,tzinfo=timezone.utc)
    n=0; h=hashlib.sha256(); minimum=math.inf;maximum=-math.inf
    with Path(file_path).open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        req(reader.fieldnames==["timestamp_utc",colname],
            "only UTC hour-start exact CSV fields accepted; no silent local DST conversion")
        for line in reader:
            req(n<expected,"extra source timestamps beyond expected year")
            supplied=line["timestamp_utc"]
            moment=first+timedelta(hours=n)
            req(supplied==_hour_string(moment),
                "source UTC hour missing/duplicate/out of chronological order or leap day removed")
            value=float(line[colname])
            req(math.isfinite(value),"nonfinite source price/wind hour is not admissible")
            if cap is not None:
                req(-1e-10<=value<=cap+1e-8,
                    "source wind farm MW negative or exceeds original rated wake/electrical/availability cap")
            h.update(__import__("struct").pack("<d",value))
            minimum=min(minimum,value);maximum=max(maximum,value)
            n+=1
    req(n==expected,"missing year full UTC hourly coverage: expected "+str(expected))
    return {
      "year":year,"hours":n,
      "first_hour_UTC":_hour_string(first),
      "last_hour_UTC":_hour_string(first+timedelta(hours=n-1)),
      "float64_le_sha256":h.hexdigest(),
      "negative_prices_retained":minimum<0 if cap is None else None,
      "min_value_in_original_units":minimum,
      "max_value_in_original_units":maximum,
      "data_source_new_observed_calendar_not_synthetic_2023_rolling_claimed_by_this_parser":False
    }


def admission(private_manifest_path, private_root):
    ledger=json.loads(REGISTER.read_text(encoding="utf-8"))
    req(ledger.get("schema_version")==
        "oem.ptx.f3d_alternative_observed_2022_2024_entsoe_era5_private_source_admission.v1" and
        ledger.get("current_total_accepted_alternative_year_price_and_wind_pairs")==0 and
        ledger.get("independent_historical_year_source_files_downloaded_and_verified") is False and
        ledger.get("full_F3_and_L3_v1_release_eligible") is False,
        "public source evidence ledger must not fabricate actual observed 2022/2024 values")
    manifest_path=Path(private_manifest_path).resolve(strict=True)
    root=Path(private_root).resolve(strict=True)
    req(manifest_path.is_relative_to(root) and not Path(private_manifest_path).is_symlink(),
        "external year source manifest must remain private outside Git")
    d=json.loads(manifest_path.read_text(encoding="utf-8"))
    year=d.get("year")
    req(year in YEARS and d.get("schema_version")==MANIFEST_SCHEMA,
        "wrong year or unqualified external source")
    p=d.get("price",{});w=d.get("wind",{})
    req(p.get("provider")==PRICE_PROVIDER and p.get("market_domain")=="NL" and
        p.get("document_type")=="A44" and
        p.get("unit")=="EUR/MWh" and
        p.get("UTC_hour_aggregation_method") in ("source_native_60min","duration_weighted_native_15min_or_60min") and
        p.get("negative_source_prices_preserved") is True,
        "wrong country, interval, native ENTSO-E A44 market source or negative-price handling")
    req(w.get("provider")==WIND_PROVIDER and
        w.get("reference_lat_deg_N")==52.5 and w.get("reference_lon_deg_E")==3.5 and
        w.get("original_100m_to_120m_hub_shear_exponent")==.11 and
        w.get("power_curve_model")=="source_PyNEXUS_cubic_wake_0p10_electric_0p02_unavailability_0p05" and
        w.get("site_delivery_is_offshore_weather_grid_only") is True and
        w.get("source_ERA5_monthly_u10_v10_u100_v100_present") is True,
        "ERA5 grid site, physical 100m-to-hub pipeline, curve and source component provenance missing")
    items=[("price",p,"day_ahead_eur_mwh",None),("wind",w,"wind_available_mw",MAX_WIND_MW)]
    out={}
    for name,item,col,cap in items:
        files=item.get("private_raw_provider_files",[])
        req(isinstance(files,list) and len(files)>=12,
            "need source original monthly data, not assumed yearly synthetic series")
        seen=set(); totals=[]
        for row in files:
            req(_hex_sha(row.get("sha256")) and row.get("file") not in seen,
                "missing or duplicate original provider document SHA")
            seen.add(row["file"])
            totals.append(file_evidence(row["file"],row["sha256"],root))
        path=item.get("normalized_full_UTC_hourly_CSV")
        req(isinstance(path,str) and _hex_sha(item.get("normalized_csv_SHA256")),
            "missing original-calendar normalized hourly array source hash")
        file_evidence(path,item["normalized_csv_SHA256"],root)
        checked=validate_hourly_csv(path,year,col,cap=cap)
        req(checked["hours"]==YEARS[year] and _hex_sha(checked["float64_le_sha256"]),
            "bad source full year float64 hourly data")
        out[name]={
          "provider":item["provider"],
          "raw_original_document_count":len(files),
          "raw_original_SHA256":[row["sha256"] for row in files],
          "normalized_hour_CSV_SHA256":item["normalized_csv_SHA256"],
          "normalized_source_numeric_f64_le_SHA256":checked["float64_le_sha256"],
          "hourly_UTC_coverage_checked":checked["hours"],
          "yearly_min_in_source_units":checked["min_value_in_original_units"],
          "yearly_max_in_source_units":checked["max_value_in_original_units"]
        }
    baseline=d.get("source_2023_reproduction",{})
    req(baseline.get("original_2023_price_float64_SHA256")==REFERENCE_2023_PRICE_SHA and
        baseline.get("original_2023_wind_float64_SHA256")==REFERENCE_2023_WIND_SHA and
        baseline.get("independent_2023_raw_ERA5_and_A44_rederivation_verified") is True and
        _hex_sha(baseline.get("source_PyNEXUS_conversion_revision_git_sha256")),
        "must independently rederive and verify 2023 original source chronology prior to another year")
    # Factual data parsing can pass, but provenance/physics/reviewer and
    # exactly matched new year H2 annual service still must be audited.
    return {
      "schema_version":SCHEMA,
      "observed_external_UTC_calendar_year_claimed":year,
      "expected_UTC_hours":YEARS[year],
      "observed_price_and_ERA5_wind_hourly_pair_private_bytes_and_calendar_verified":True,
      "original_PyNEXUS_2023_calibration_manifest_attested_not_independently_peer_reviewed":True,
      "separate_independent_scientific_original_H2_ERA5_and_ENTSOE_data_review_signed":False,
      "source_hourly_model_must_reoptimize_both_E_ES_at_identical_NEW_year_H2_profile":True,
      "source_2024_leap_8784_hours_not_current_2023_source_dispatch_supported":year==2024,
      "original_2023_F3C_hourly_delivered_target_not_automatically_valid_for_new_year":True,
      "real_industrial_H2_customer_siting_service_contract_proven":False,
      "source_modeled_price_and_wind_origin":out,
      "full_manufacturer_BOM_and_native_LCA_or_real_project_economic_preference_allowed":False,
      "whole_programme_v1_0_release_allowed":False,
      "raw_provider_arrays_and_private_file_paths_in_output":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--private-manifest",required=True)
    p.add_argument("--private-source-root",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    outfile=Path(args.output)
    if outfile.exists():raise FileExistsError("do not overwrite original-year private source admission")
    out=admission(args.private_manifest,args.private_source_root)
    outfile.parent.mkdir(parents=True,exist_ok=True)
    outfile.write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Verified calendar/source SHA eligibility for",out["observed_external_UTC_calendar_year_claimed"],
          "with",out["expected_UTC_hours"],"UTC hours, but independent science/site/v1 review remains BLOCKED")
if __name__=="__main__":main()
