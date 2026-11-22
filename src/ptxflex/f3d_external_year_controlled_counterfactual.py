"""F3-D source-locked observed-year CONTROLLED counterfactual dispatcher.

Use PRIVATE original historical A44/ERA5 source pair and the already certified
price-neutral E maximum uniform service selected in each year/mode. Never
reselect hydrogen when changing electricity prices or source wind output:
doing so changes the product functional unit and ruins attribution.

Scenarios are analyst counterfactuals, NOT observed prices or wind speed years.
Each source-MILP case writes only to a PRIVATE archive (one original witness per
case, never to public Git); all public publication awaits independent PtXLens
replay, not merely solver status 0. No v1.0 claim is permitted.

This is a method implementation, not proof that every full-year stress case
is computationally tractable, feasible or has been run.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np

from .f3d_year_matched_service import (
    ALLOWED_YEARS,OUTPUT_SCHEMA,E_SHA,ES_SHA,array_sha,
    certify_cost_case,load_private_hourly,load_source_parameters,physical_duty,
)
from .f3d_live_provider_pair_gate import verify_pair
from .f3_matched_ideal_benchmark import solve_ideal_storage,independently_audit,SourceLockedDispatchError,DIM
from .f3d_live_era5 import FARM_LIMIT_MW

SOURCE_BLOB_SHA="ca07f5ef1e381fa157982bc5a68e46ce3022003a"
PRIVATE_SCHEMA="ptxflex.f3d_private_source_year_counterfactual_exact_dispatch.v1"
VARIANTS=("price_roll_168h","price_spread_150pct",
          "wind_power_090","wind_power_110_capped")
MODES=("max_inventory","usable_service")
SOURCE_REFERENCE="F3D_ARCO_2022_2024_PUBLIC_VERIFIED_AGGREGATES_v1.json"
STUDY_DESC={
 "price_roll_168h":"Circularly shift ONLY historical NL A44 hourly EUR/MWh by 168 hours; preserve source wind and H2 demand.",
 "price_spread_150pct":"Multiply historical price deviations from original year's median by 1.5; preserve source wind and H2 demand.",
 "wind_power_090":"Reduce PyNEXUS-derived hourly available wind POWER by 10%; source price and same H2 requirement unchanged; infeasible case must be recorded null.",
 "wind_power_110_capped":"Increase PyNEXUS-derived hourly available wind POWER by 10% with original source PyNEXUS wind conversion limit; price and H2 requirement unchanged.",
}

def need(ok,why):
    if not ok:raise SourceLockedDispatchError("F3-D controlled source-year robustness: "+why)

def original_blob_sha(raw):
    raw=raw.replace(b"\r\n",b"\n")
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def original_four_case_metadata(source_path,year,mode):
    source=Path(source_path)
    need(source.is_file(),"original public source-verified F3-D aggregate missing")
    raw=source.read_bytes()
    need(original_blob_sha(raw)==SOURCE_BLOB_SHA,
         "verified original source aggregate Git blob changed; STOP until reviewed")
    j=json.loads(raw.decode("utf-8-sig"))
    need(j.get("scientific_v1_0_release_allowed") is False and
         j.get("independent_solver_dual_certificates_recomputed") is False and
         j.get("independent_year_mode_full_hourly_primal_E_EplusS_and_EOS_replay_passed") is True,
         "published original independent source/primal validation missing")
    a=[x for x in j.get("cases",[]) if x.get("year")==year and
       x.get("storage_capacity_semantics")==mode]
    need(len(a)==1 and len(j.get("cases",[]))==4,
         "original four-case source record does not uniquely identify requested case")
    case=a[0]
    need(case.get("independent_full_hourly_E_and_EplusS_primal_replay_passed") is True and
         case.get("independent_full_hourly_type_I_20_to_200bar_EOS_replay_passed") is True,
         "reference original E/E+S hourly witness not independently reviewed")
    return case

def transform_inputs(price,wind,variant):
    """No raw original arrays are returned to public results.
    
    These transformations act on *electrical wind availability*, not 100-m
    ERA5 wind speed, and do NOT represent new physical weather years.
    """
    need(variant in VARIANTS,"unsupported pre-registered counterfactual")
    price=np.asarray(price,dtype=np.float64)
    wind=np.asarray(wind,dtype=np.float64)
    need(price.ndim==wind.ndim==1 and len(price)==len(wind) and
         np.isfinite(price).all() and np.isfinite(wind).all() and
         np.min(wind)>=0 and np.max(wind)<=FARM_LIMIT_MW+1e-8,
         "source model hourly input invalid or original wind limit violated")
    p=price.copy();w=wind.copy()
    if variant=="price_roll_168h":
        p=np.roll(p,168)
    elif variant=="price_spread_150pct":
        median=float(np.median(p))
        p=median+1.5*(p-median)
    elif variant=="wind_power_090":
        w=0.9*w
    elif variant=="wind_power_110_capped":
        w=np.minimum(1.1*w,FARM_LIMIT_MW)
    need(len(p)==len(price) and len(w)==len(wind) and
         np.isfinite(p).all() and np.isfinite(w).all() and
         np.min(w)>=0 and np.max(w)<=FARM_LIMIT_MW+1e-8,
         "constructed counterfactual violates physically bounded source arrays")
    return np.asarray(p,dtype=np.float64),np.asarray(w,dtype=np.float64)

def load_verified_research_inputs(year,mode,variant,private_root,source_path):
    need(year in ALLOWED_YEARS and mode in MODES and variant in VARIANTS,
         "wrong real year or storage semantics or preregistered stress")
    private=Path(private_root).resolve(strict=True)
    need(private.is_dir() and private.name=="PtX_PRIVATE_RESEARCH",
         "private original provider archive root not explicitly identified")
    gate=verify_pair(year,private/f"price-{year}",private/f"wind-arco-{year}",
                     private/"price-2023",private/"wind-2023-recovered"/"complete")
    need(gate.get("source_price_and_weather_calendar_and_original_hashes_verified") is True and
         gate.get("actual_2023_original_price_reproduction") is True and
         gate.get("actual_2023_original_wind_reproduction") is True and
         gate.get("year_wind_alternate_ARCO_calibrated_2023_original_8760h") is True,
         "real 2022/2024 historic original source and 2023 anchor cannot be certified")
    p=load_private_hourly(private/f"price-{year}"/"normalized_UTC_price.csv",
                          year,"day_ahead_eur_mwh")
    w=load_private_hourly(private/f"wind-arco-{year}"/"normalized_UTC_wind.csv",
                          year,"wind_available_mw",nonnegative=True)
    published=original_four_case_metadata(source_path,year,mode)
    need(array_sha(p)==gate["year_price"]["normalized_float64_sha256"]==
         published["source_year_price_f64_sha256"] and
         array_sha(w)==gate["year_wind"]["normalized_float64_sha256"]==
         published["source_year_wind_f64_sha256"],
         "original private source arrays mismatch public original four-case SHA")
    original_report=private/"results"/f"F3D_ARCO_{year}_{mode}.json"
    original_witness=private/"results"/f"PRIVATE_F3D_ARCO_{year}_{mode}_primal.json"
    need(original_report.is_file() and original_witness.is_file(),
         "missing source-invariant original full-hourly witness; STOP")
    report=json.loads(original_report.read_text(encoding="utf-8"))
    witness=json.loads(original_witness.read_text(encoding="utf-8"))
    need(report.get("schema_version")==OUTPUT_SCHEMA and
         report.get("year")==year and report.get("capacity_semantics")==mode and
         report.get("v1_0_scientific_release_allowed") is False and
         report.get("source_year_price_f64_sha256")==array_sha(p) and
         report.get("source_year_wind_f64_sha256")==array_sha(w) and
         witness.get("schema_version")=="ptxflex.f3d_PRIVATE_original_source_dispatch_witness.v1" and
         witness.get("year")==year and witness.get("capacity_semantics")==mode and
         witness.get("price_float64_sha256")==array_sha(p) and
         witness.get("wind_float64_sha256")==array_sha(w) and
         witness.get("original_E_SHA256")==E_SHA and
         witness.get("original_ES_SHA256")==ES_SHA and
         witness.get("source_year_prices_and_wind_NOT_duplicated_in_witness") is True,
         "private reference result/witness differs from original source")
    x=np.asarray(witness.get("target_hourly_kg"),dtype=np.float64)
    need(x.shape==(ALLOWED_YEARS[year],) and np.isfinite(x).all() and
         np.min(x)>0 and array_sha(x)==witness.get("target_float64_sha256")==
         published["price_neutral_E_uniform_hydrogen_service"]["hourly_target_f64_sha256"]==
         report["E_price_blind_identical_model_H2_service_selection"]["selected_h2_target_float64_sha256"],
         "original price-neutral selected H2 functional unit is not SHA-locked")
    # Crucial: the price-blind original selector target is NEVER reoptimized
    # in any counterfactual. If wind can no longer serve it, saving is null.
    for name in ("E","E_plus_S"):
        actual=witness["cases"][name]
        params=load_source_parameters()[name]
        need(actual["source_model_parameters"]==params,
             "reference physical case parameters modified")
        states=np.asarray(actual["cost_optimum_hourly_states"],dtype=np.float64)
        need(states.shape==(ALLOWED_YEARS[year],DIM) and
             array_sha(states.reshape(-1))==
             report[name]["source_hourly_dispatch_float64_sha256"]==
             published[name]["private_hourly_primal_sha256"],
             "referenced source primal hours changed since independent replay")
    newp,neww=transform_inputs(p,w,variant)
    return (newp,neww,x,
            {"original_year":year,"mode":mode,"variant":variant,
             "source_original_price_SHA256":array_sha(p),
             "source_original_wind_SHA256":array_sha(w),
             "source_original_selected_H2_SHA256":array_sha(x),
             "counterfactual_price_SHA256":array_sha(newp),
             "counterfactual_wind_SHA256":array_sha(neww),
             "original_public_aggregate_Git_blob_sha1":SOURCE_BLOB_SHA,
             "source_original_baseline_modelled_saving_eur":
                 published["matched_service_annual_operational_savings_nominal_eur"],
             "source_original_service_kg":float(np.sum(x)),
             "source_wind_model_power_limit_mw":float(FARM_LIMIT_MW)})

def result_path(root,year,mode,variant,case):
    return root/f"PRIVATE_F3D_CF_{year}_{mode}_{variant}_{case}.json"

def solve_case(year,mode,variant,case,private_root,source_path,*,limit_s=3600):
    need(case in ("E","E_plus_S"),"counterfactual must explicitly select E or E_plus_S")
    need(type(limit_s) is int and 30<=limit_s<=14400,
         "explicit original MILP limit must be 30..14400 seconds")
    price,wind,target,meta=load_verified_research_inputs(
        year,mode,variant,private_root,source_path)
    private=Path(private_root).resolve(strict=True)
    root=private/"results"/"counterfactuals"
    root.mkdir(parents=True,exist_ok=True)
    need(root.parent==private/"results" and
         root.resolve().is_relative_to(private),
         "counterfactual witness may not be written outside private archive")
    path=result_path(root,year,mode,variant,case)
    model=load_source_parameters()[case]
    duty=physical_duty(model,mode)
    if path.exists():
        saved=json.loads(path.read_text(encoding="utf-8"))
        need(saved.get("schema_version")==PRIVATE_SCHEMA and
             saved.get("metadata")==meta and
             saved.get("scenario")==case and
             saved.get("original_provider_hourly_arrays_NOT_redistributed") is True,
             "existing private counterfactual result changed, cannot overwrite")
        print(f"F3D_CF_REUSED_PRIVATE year={year} mode={mode} variant={variant} case={case} "
              f"status={saved.get('outcome')} -- no reoptimization")
        return saved
    # For wind-power reductions, first require E and E+S to pass a
    # zero-objective LP relaxation, a mathematical *necessary* MILP condition.
    # LP infeasibility is strong evidence of original MODEL infeasibility,
    # but cannot prove site physics or commercial unfeasibility.
    if variant.startswith("wind_"):
        diag=solve_ideal_storage(
            wind,price,target,model,
            diagnostic_only_lp_relaxation=True,pressure_duty=duty,
            source_calendar_year=year,
            external_year_input_class="private_provider_pair_admission_candidate_not_peer_reviewed",
            time_limit_s=limit_s)
        need(diag["solver_status_code"] in (0,2) and
             diag["tested_hours"]==ALLOWED_YEARS[year] and
             diag["all_original_hourly_electricity_H2_storage_pressure_compressor_constraints_preserved"] is True,
             "wind-case LP feasibility inconclusive; do not produce saving")
        if diag["solver_status_code"]==2:
            record={"schema_version":PRIVATE_SCHEMA,"metadata":meta,"scenario":case,
                    "outcome":"LP_RELAXATION_INFEASIBLE_FIXED_H2_NO_COST_RESULT",
                    "LP_zero_objective_infeasible_HiGHS_status_2":True,
                    "LP_model_infeasibility_only_NOT_site":True,
                    "modelled_counterfactual_cost_eur":None,
                    "independent_model_dual_certificate_replayed":False,
                    "native_BAFU_or_vendor_or_v1_release":False,
                    "original_provider_hourly_arrays_NOT_redistributed":True}
            path.write_text(json.dumps(record,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
            print(f"F3D_CF_LP_INFEASIBLE year={year} mode={mode} variant={variant} case={case}; "
                  "same H2 contract cannot be cost compared; result is NULL")
            return record
    try:
        r=solve_ideal_storage(wind,price,target,model,
            source_calendar_year=year,
            external_year_input_class="private_provider_pair_admission_candidate_not_peer_reviewed",
            pressure_duty=duty,time_limit_s=limit_s,mip_rel_gap=1e-6)
        audit=certify_cost_case(r,target,case,year)
    except (SourceLockedDispatchError,MemoryError) as exc:
        print(f"F3D_CF_MODEL_NOT_CERTIFIED year={year} mode={mode} "
              f"variant={variant} case={case}: {type(exc).__name__}; "
              "no file claiming annual economic result was saved")
        raise
    witness=np.asarray(r["hourly_solved_states"],dtype=np.float64)
    record={
        "schema_version":PRIVATE_SCHEMA,"metadata":meta,"scenario":case,
        "outcome":"ORIGINAL_FULL_YEAR_MILP_PRIMAL_SOLVER_BOUND_CERTIFIED_LOCAL_NOT_EXTERNAL_DUAL",
        "source_case_modelled_annual_kg_H2":float(np.sum(target)),
        "modelled_counterfactual_cost_eur":audit["modelled_cost_eur_in_source_calendar_not_inflation_adjusted"],
        "solver_reported_cost_lower_bound_eur":audit["solver_cost_lower_bound_eur"],
        "solver_reported_mip_relative_gap":audit["mip_relative_gap"],
        "source_original_model_8field_primal_witness":witness.tolist(),
        "source_original_primal_f64_sha256":array_sha(witness.reshape(-1)),
        "pressure_and_conservation_original_source_model_audit":audit,
        "original_provider_hourly_arrays_NOT_redistributed":True,
        "independent_model_dual_certificate_replayed":False,
        "native_BAFU_or_vendor_or_v1_release":False,
    }
    # PRIVATE ONLY: this 8760/8784-hour record includes full original states.
    with path.open("x",encoding="utf-8") as handle:
        json.dump(record,handle,sort_keys=True,separators=(",",":"),allow_nan=False)
        handle.write("\n")
    print(f"F3D_CF_CASE_SOLVED year={year} mode={mode} variant={variant} case={case} "
          f"nominal_eur={record['modelled_counterfactual_cost_eur']:.2f}; "
          "independent PtXLens hourly replay STILL REQUIRED")
    return record

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year",type=int,choices=sorted(ALLOWED_YEARS),required=True)
    ap.add_argument("--mode",choices=MODES,required=True)
    ap.add_argument("--variant",choices=VARIANTS,required=True)
    ap.add_argument("--case",choices=("E","E_plus_S"),required=True)
    ap.add_argument("--private-root",type=Path,
                    default=Path.home()/"PtX_PRIVATE_RESEARCH")
    ap.add_argument("--source",type=Path,default=Path(__file__).resolve().parents[2]/
                    "research"/SOURCE_REFERENCE)
    ap.add_argument("--time-limit",type=int,default=3600)
    a=ap.parse_args(argv)
    solve_case(a.year,a.mode,a.variant,a.case,a.private_root,a.source,
               limit_s=a.time_limit)

if __name__=="__main__":
    main()
