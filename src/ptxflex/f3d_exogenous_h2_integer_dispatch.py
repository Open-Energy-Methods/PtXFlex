"""F3-D source-locked EXOGENOUS H2 contract original E/E+S annual MILPs.

Prespecified study target: 30 t/day *independently of E's maximal deliverable*
and 0.90 of original 2022 modelled wind ELECTRICAL POWER, under EXACT original
2022 NL A44 price, 2022 ERA5 ARCO wind, physical equipment and Type I
20–200bar pressure screen. Both E20t and E+S40t must meet the same H2
schedule. Never identify an LP feasible vector with an integer solution.

PtXLens LP screening must first be independently source-hash admitted.
Each SOURCE verified mixed-integer cost solver witness is stored ONLY in
the user's PRIVATE research archive with immutable provenance; not public
GitHub or the sanitized public result directory. The independent PtXLens
hourly witness replay is a separate subsequent step and must finish before
any paired savings claim.

A solver timeout/nonclosing 1e-6 MIP gap is INCONCLUSIVE, not infeasible,
and is not silently recorded as a negative economic result.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from .f3d_external_year_controlled_counterfactual import (
    load_verified_research_inputs, need, SOURCE_BLOB_SHA
)
from .f3d_year_matched_service import (
    array_sha, load_source_parameters, physical_duty, certify_cost_case,
    ALLOWED_YEARS
)
from .f3_matched_ideal_benchmark import (
    solve_ideal_storage, SourceLockedDispatchError, DIM
)

SCHEMA="ptxflex.f3d_PRIVATE_exogenous_fixed_h2_source_year_cost_integer_witness.v1"
LP_SCHEMA="ptxlens.f3d_original_year_exogenous_fixed_h2_service_pair_LP_screen.v1"
SERVICE_TPD=30.
WIND_POWER_FACTOR=.9
MODES=("max_inventory","usable_service")
CASES=("E","E_plus_S")


def fixed_target(hours,tonnes_day=SERVICE_TPD):
    """Non-optimized exogenously specified H2, identical to PtXLens LP grid."""
    need(type(hours) is int and hours in ALLOWED_YEARS.values(),
         "unsupported source UTC year calendar")
    need(type(tonnes_day) in (float,int) and
         float(tonnes_day)==SERVICE_TPD,
         "only original preregistered 30t/day service admitted in first MILP")
    return np.full(hours,tonnes_day*1000./24.,dtype=np.float64)


def check_lp_manifest(path,year,mode,original_price_sha,original_wind_sha,
                      selected_h2_sha,original_max_h2_tpd,target,stress_wind):
    """Review external LP screen before any new annual integer solver run."""
    path=Path(path)
    need(path.is_file() and not path.is_symlink(),
         "source-hash verified exogenous LP screening result file missing")
    original_bytes=path.read_bytes()
    screen=json.loads(original_bytes.decode("utf-8"))
    need(screen.get("schema_version")==LP_SCHEMA and
         screen.get("source_year")==year and
         screen.get("capacity_semantics")==mode and
         screen.get("source_calendar_UTC_hours")==ALLOWED_YEARS[year] and
         screen.get("source_original_4_case_public_Git_blob_sha1")==SOURCE_BLOB_SHA and
         screen.get("source_original_price_float64_SHA256")==original_price_sha and
         screen.get("source_original_wind_power_float64_SHA256")==original_wind_sha and
         screen.get("source_original_E_max_selected_hourly_H2_float64_SHA256")==selected_h2_sha and
         screen.get("source_price_year_input_unchanged") is True and
         screen.get("same_H2_target_hourly_for_E_and_ES_at_every_wind_factor") is True and
         screen.get("exogenous_delivery_schedules_selected_without_looking_at_stressed_wind_outcomes") is True and
         screen.get("original_integer_dispatch_or_matched_wholesale_savings_certified") is False and
         screen.get("real_site_or_manufacturer_or_native_BAFU_or_scientific_v1_0") is False,
         "source exogenous LP screen identity or scientific scope changed")
    max_tpd=float(original_max_h2_tpd)
    need(math.isfinite(max_tpd) and SERVICE_TPD<max_tpd-1e-8,
         "prespecified H2 contract must remain below selected E-max service")
    need(abs(float(screen.get("original_selected_E_max_nominal_tonnes_day",float("nan")))-
                 max_tpd)<1e-9,
         "original E maximal service product drift")
    need(screen.get("prespecified_exogenous_delivery_tonnes_day")==[25.,27.5,30.] and
         screen.get("source_wind_electric_power_multipliers")==[.9,.95,1.],
         "LP screen pre-registered research grid modified")
    entries=screen.get("nine_service_factor_pairs_two_architectures_LP_cells")
    need(type(entries) is list and len(entries)==9,
         "complete exogenous LP feasibility matrix missing")
    relevant=[r for r in entries if r.get("exogenous_H2_tonnes_per_day")==SERVICE_TPD and
              r.get("source_wind_power_multiplier")==WIND_POWER_FACTOR]
    need(len(relevant)==1,"exact original 30t/day 90pct wind LP case missing")
    cell=relevant[0]
    need(cell.get("exogenous_H2_original_same_hourly_SHA256")==array_sha(target) and
         abs(float(cell.get("exogenous_same_product_annual_H2_kg",float("nan")))-
             float(np.sum(target)))<.005 and
         cell.get("E_and_ES_original_integer_dispatch_both_certified") is False and
         cell.get("matched_source_annual_E_minus_EplusS_cost_saving_eur") is None,
         "source-locked fixed 30t/day original target LP screening compromised")
    case_rows=cell.get("cases")
    need(type(case_rows) is dict and set(case_rows)==set(CASES),
         "both original E/ES capacity cases missing")
    for name in CASES:
        row=case_rows[name]
        need(row.get("HiGHS_LP_status_code")==0 and
             row.get("source_E_or_EplusS_original_model_LP_status")==
                 "SOURCE_LP_PRIMAL_FEASIBLE_INTEGER_UNDETERMINED" and
             row.get("original_integer_MILP_feasible") is None and
             row.get("source_matched_service_annual_cost_saving_eur") is None and
             row.get("source_stress_wind_electric_power_multiplier")==WIND_POWER_FACTOR,
             "E or E+S independent LP not accepted feasible at fixed service")
    need(stress_wind.shape==target.shape and np.isfinite(stress_wind).all(),
         "original stressed wind chronology missing")
    return {"LP_screen_bytes_SHA256":hashlib.sha256(original_bytes).hexdigest(),
            "LP_cell_status":"BOTH_ORIGINAL_MODEL_LPS_FEASIBLE_INTEGER_UNKNOWN",
            "exogenous_H2_fixed_hourly_SHA256":array_sha(target),
            "LP_selected_source_year":year,"capacity_semantics":mode,
            "LP_wind_factor":WIND_POWER_FACTOR}


def private_result_file(private,year,mode,case):
    return private/"results"/"exogenous_service_robustness"/(
        f"PRIVATE_F3D_EXOGENOUS_{year}_{mode}_H30_W090_{case}.json"
    )


def run(year,mode,case,private_root,original_public,lp_screen,*,time_limit_s=3600):
    need(year in ALLOWED_YEARS and mode in MODES and case in CASES,
         "unregistered original provider source year/mode/case")
    need(type(time_limit_s) is int and 30<=time_limit_s<=14400,
         "original full-year integer solve time budget must be explicitly bounded")
    private=Path(private_root).resolve(strict=True)
    need(private.is_dir() and private.name=="PtX_PRIVATE_RESEARCH",
         "original private research archive identity mismatch")
    price,wind,original_target,meta=load_verified_research_inputs(
        year,mode,"wind_power_090",private,original_public)
    selected_target=original_target
    target=fixed_target(ALLOWED_YEARS[year])
    original_max_tpd=float(original_target[0])*24./1000.
    source_sha=meta["source_original_selected_H2_SHA256"]
    need(array_sha(selected_target)==source_sha and
         array_sha(wind)==meta["counterfactual_wind_SHA256"],
         "original locked maximal H2 or reduced-wind source arrays changed")
    receipt=check_lp_manifest(
        lp_screen,year,mode,
        meta["source_original_price_SHA256"],
        meta["source_original_wind_SHA256"],
        source_sha,original_max_tpd,target,wind,
    )
    metadata={
        "year":year,"mode":mode,"case":case,
        "exogenous_H2_tonnes_day":SERVICE_TPD,
        "exogenous_H2_annual_kg":float(np.sum(target)),
        "exogenous_H2_hourly_SHA256":array_sha(target),
        "wind_model_electric_power_factor":WIND_POWER_FACTOR,
        "source_original_price_SHA256":meta["source_original_price_SHA256"],
        "source_original_wind_SHA256":meta["source_original_wind_SHA256"],
        "source_stressed_wind_SHA256":meta["counterfactual_wind_SHA256"],
        "source_original_E_max_H2_SHA256":source_sha,
        "source_public_original_source_blob":SOURCE_BLOB_SHA,
        "source_independent_LP_screen_SHA256":receipt["LP_screen_bytes_SHA256"],
        "original_site_or_BAFU_or_manufacturer_v1_certified":False,
    }
    path=private_result_file(private,year,mode,case)
    need(path.parent.resolve().is_relative_to(private) and
         path.parent.parent==private/"results",
         "private full-year MILP witness cannot escape protected original archive")
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        existing=json.loads(path.read_text(encoding="utf-8"))
        need(existing.get("schema_version")==SCHEMA and
             existing.get("metadata")==metadata and
             existing.get("scenario")==case and
             existing.get("outcome")=="SOURCE_MILP_SOLVER_REPORTED_COST_BOUND_NOT_INDEPENDENTLY_REPLAYED" and
             existing.get("hourly_witness_private_not_for_git") is True,
             "existing private scientific outcome changed; cannot overwrite")
        print("F3D_EXOGENOUS_SOURCE_CASE_ALREADY_PRIVATE",year,mode,case,
              "independent PtXLens replay STILL REQUIRED")
        return existing
    p=load_source_parameters()[case]
    duty=physical_duty(p,mode)
    result=solve_ideal_storage(
        wind,price,target,p,
        pressure_duty=duty,
        time_limit_s=time_limit_s,
        mip_rel_gap=1e-6,
        source_calendar_year=year,
        external_year_input_class="private_provider_pair_admission_candidate_not_peer_reviewed",
    )
    audit=certify_cost_case(result,target,case,year)
    states=np.asarray(result["hourly_solved_states"],dtype=np.float64)
    need(states.shape==(ALLOWED_YEARS[year],DIM),
         "complete original full-year 8-variable integer dispatch witness absent")
    record={
        "schema_version":SCHEMA,"metadata":metadata,"scenario":case,
        "outcome":"SOURCE_MILP_SOLVER_REPORTED_COST_BOUND_NOT_INDEPENDENTLY_REPLAYED",
        "source_solver_cost_eur":audit["modelled_cost_eur_in_source_calendar_not_inflation_adjusted"],
        "source_solver_reported_cost_lower_bound_eur":audit["solver_cost_lower_bound_eur"],
        "source_solver_reported_relative_MIP_gap":audit["mip_relative_gap"],
        "source_solver_reported_annual_h2_kg":audit["modelled_annual_hydrogen_kg"],
        "original_full_hourly_states_SHA256":array_sha(states.reshape(-1)),
        "original_full_hourly_states_8var_PRIVATE":states.tolist(),
        "original_source_solver_audit":audit,
        "hourly_witness_private_not_for_git":True,
        "original_provider_price_wind_arrays_not_duplicated":True,
        "independent_full_year_hourly_physical_replay_complete":False,
        "independent_original_cost_dual_proof_complete":False,
        "matched_service_E_minus_ES_cost_saving_eur":None,
        "real_site_or_manufacturer_or_BAFU_v1_certified":False,
    }
    with path.open("x",encoding="utf-8",newline="\n") as out:
        json.dump(record,out,sort_keys=True,separators=(",",":"),allow_nan=False)
        out.write("\n")
    print("F3D_EXOGENOUS_SOURCE_MILP_SOLVED_PRIVATE",year,mode,case,
          f"modelled_wholesale_source_EUR={record['source_solver_cost_eur']:.2f}; "
          "PUBLIC cost result BLOCKED until BOTH PtXLens independent replays")
    return record


def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--year",type=int,choices=sorted(ALLOWED_YEARS),required=True)
    a.add_argument("--mode",choices=MODES,required=True)
    a.add_argument("--case",choices=CASES,required=True)
    a.add_argument("--private-root",type=Path,required=True)
    a.add_argument("--public-source",type=Path,required=True)
    a.add_argument("--lp-screen",type=Path,required=True)
    a.add_argument("--time-limit",type=int,default=3600)
    v=a.parse_args(argv)
    run(v.year,v.mode,v.case,v.private_root,v.public_source,v.lp_screen,
        time_limit_s=v.time_limit)


if __name__=="__main__":
    main()
