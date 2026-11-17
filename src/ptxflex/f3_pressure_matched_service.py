"""F3-C: source-2023 Type I pressure-screened E/E+S fixed-hourly H2 service.

The common hourly product delivery is the original frozen E delivered profile
MINUS the exact historical Stage-A feasible E incumbent's physical shortfall
for the selected capacity semantics.  Two distinct reference targets are
registered (max_inventory, usable_service), NEVER cross-compared as one case.
The original wind/price/source archives and the Stage-A derivative ZIP are
independently SHA-checked BEFORE invoking this module in Actions.

The choice is **constructive, not optimal**: the Stage-A E incumbent is feasible
and its shortfall is *not* proven globally minimal. Equal-hourly net-grid
settlement is an operational comparison only; source original E reference
already falls 1.9147 million kg short of the original full 2023 contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from .f3_matched_ideal_benchmark import (
    load_matched_pilot,solve_ideal_storage,SourceLockedDispatchError,
)
from .pressure_storage_duty import (
    build_screened_pressure_duty,audit_gas_pressure_boundaries,
)
from .f3_backup_sparse_hourly import (
    EXPECTED_ARTIFACT_ZIP_SHA,EXPECTED_BACKUP_SUMMARY_SHA,E_SHA,ES_SHA,
    REFERENCE_TARGET_KG,ZERO_THRESHOLD_KG_H,
)

ROOT=Path(__file__).resolve().parents[2]
SOURCE_SPARSE_SHA={
 "max_inventory":"9acefa605c878e19f369f57cd94519fc9dd926beda284135529b7d89ce31208e",
 "usable_service":"9c66837c105e5c17e2fbdceb50250a2ea7940ac0a2a321a08ffec8cf81622999"
}
SCHEMA="ptxflex.f3C_2023_source_pressure_screen_equal_hourly_reduced_service.v1"
VALID_CASES={"E","E_plus_S"}
HOURS=8760


def _read_sparse_source(mode):
    if mode not in SOURCE_SPARSE_SHA:
        raise SourceLockedDispatchError("unregistered source Type I bank inventory interpretation")
    p=ROOT/"data/results"/f"F3_2023_original_E_sparse_H2_backup_need_{mode}.json"
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SPARSE_SHA[mode]:
        raise SourceLockedDispatchError("frozen source Stage A 2023 sparse deficit file SHA changed")
    d=json.loads(raw)
    if (d.get("schema_version")!="ptxflex.f3_2023_sparse_modelled_backup_hourly_need.v1"
        or d.get("original_source_year")!=2023
        or d.get("source_8760_hourly_count")!=HOURS
        or d.get("capacity_semantics")!=mode
        or d.get("source_model_E_zip_sha256")!=E_SHA
        or d.get("source_model_E_plus_S_zip_sha256")!=ES_SHA
        or d.get("source_registered_stageB_derived_summary_sha256")!=EXPECTED_BACKUP_SUMMARY_SHA[mode]
        or d.get("source_stageA_artifact_zip_sha256")!=EXPECTED_ARTIFACT_ZIP_SHA[mode]
        or d.get("zero_kg_h_at_all_hours_not_listed") is not True
        or d.get("modelled_need_not_actual_hydrogen_supplier_delivery") is not True
        or d.get("full_LCA_TEA_qualified") is not False):
        raise SourceLockedDispatchError("Stage A 2023 source provenance or scientific limits invalid")
    if abs(float(d["original_E_delivered_target_kg"])-REFERENCE_TARGET_KG)>.002:
        raise SourceLockedDispatchError("original source E reference annual delivery changed")
    sparse=np.zeros(HOURS)
    seen=set()
    rows=d.get("positive_H2_topup_needed_kg_by_0_based_source_hour")
    if not isinstance(rows,list):raise SourceLockedDispatchError("invalid sparse source hour rows")
    for item in rows:
        h=item.get("hour_index_0_based")
        mass=item.get("additional_modelled_H2_kg")
        if (type(h) is not int or h<0 or h>=HOURS or h in seen
            or isinstance(mass,bool) or not isinstance(mass,(int,float))
            or not math.isfinite(mass) or mass<=ZERO_THRESHOLD_KG_H):
            raise SourceLockedDispatchError("invalid or repeated certified original E shortfall source hour")
        seen.add(h);sparse[h]=mass
    if (len(rows)!=d["positive_hours"] or
        abs(float(sparse.sum())-d["modelled_additional_annual_topup_for_feasible_incumbent_kg"])>.002
        or abs(float(sparse.max())-d["source_incumbent_peak_kg_h"])>.002):
        raise SourceLockedDispatchError("original sparse source extra H2 mass/peak mismatch")
    return d,sparse


def construct_common_service(original_E_delivered,full_source_StageA_hourly,mode,
                             *,archived_StageA_zip_sha256):
    """Validate exact 8760h Stage A witness against independently published sparse digest.

    The authentic Stage A ZIP is verified byte-for-byte against its registered
    SHA before extraction in CI.  This function verifies the extracted source
    JSON against the registered public sparse envelope in every hour.
    Raw negative solver round-off down to -1e-7 kg is accepted and clamped.
    """
    sparse_record,sparse=_read_sparse_source(mode)
    if archived_StageA_zip_sha256!=EXPECTED_ARTIFACT_ZIP_SHA[mode]:
        raise SourceLockedDispatchError("wrong full-hour source Stage A artifact ZIP digest")
    if not isinstance(full_source_StageA_hourly,dict) or set(full_source_StageA_hourly)!={
        "hourly_additional_shortfall_kg",
        "derived_source_not_original_raw_prices_or_wind",
        "source_E_delivered_reference_profile_is_modelled"
    }:
        raise SourceLockedDispatchError("unexpected original Stage A hourly source payload schema")
    if (full_source_StageA_hourly["derived_source_not_original_raw_prices_or_wind"] is not True
        or full_source_StageA_hourly["source_E_delivered_reference_profile_is_modelled"] is not True):
        raise SourceLockedDispatchError("Stage A is not authenticated modelled original-E-source derivative")
    raw=full_source_StageA_hourly["hourly_additional_shortfall_kg"]
    if not isinstance(raw,list) or len(raw)!=HOURS:
        raise SourceLockedDispatchError("Stage A source must contain all 8760 model hour entries")
    if any(isinstance(x,bool) or not isinstance(x,(int,float))
           or not math.isfinite(x) for x in raw):
        raise SourceLockedDispatchError("nonfinite original stage A solver shortfall")
    q=np.asarray(raw,dtype=np.float64)
    if q.min()<-1e-7:raise SourceLockedDispatchError("negative physically modelled source shortage")
    q=np.maximum(q,0.)
    target=np.asarray(original_E_delivered,dtype=np.float64)
    if (target.shape!=(HOURS,) or not np.all(np.isfinite(target)) or target.min()<-1e-6
        or abs(float(target.sum())-REFERENCE_TARGET_KG)>.002):
        raise SourceLockedDispatchError("original E stage B daily/electricity delivered reference changed")
    # The public sparse derivative deliberately omits solver noise <1e-5 kg/h.
    q_sparse=np.where(q>ZERO_THRESHOLD_KG_H,q,0.)
    if not np.allclose(q_sparse,sparse,atol=1e-8,rtol=0):
        raise SourceLockedDispatchError("Stage A source full-hour witness differs from frozen sparse rows")
    if abs(float(q.sum())-float(sparse.sum()))>.002:
        raise SourceLockedDispatchError("source full-hour and registered sparse mass do not close")
    if q.max()>target.max()+1e-4 or np.max(q-target)>2e-5:
        raise SourceLockedDispatchError("source physical shortfall exceeds E original hourly delivery")
    # Preserve exact source Stage A deficit, not sparse-clipped variant, to
    # ensure a constructive feasible E dispatch exists under model assumptions.
    common=target-q
    if common.min()<-2e-5:
        raise SourceLockedDispatchError("source deficit creates negative matched-service target")
    if np.any(common<0):
        common=np.maximum(common,0.)
    if not np.all(common<=target+1e-7):
        raise SourceLockedDispatchError("constructed target increased original E service")
    original_gap=18_250_000.-float(target.sum())
    new_gap=18_250_000.-float(common.sum())
    if abs((new_gap-original_gap)-float(q.sum()))>.003:
        raise SourceLockedDispatchError("original full-demand and feasible-E shortfall accounting failed")
    return {
        "common_target":common,
        "source_shortage":q,
        "original_E_reference":target,
        "sparse_record":sparse_record,
        "target_hash_sha256":hashlib.sha256(common.tobytes()).hexdigest(),
        "StageA_full_hourly_shortage_hash_sha256":hashlib.sha256(q.tobytes()).hexdigest(),
        "source_stageA_archive_sha256":archived_StageA_zip_sha256,
    }


def compare_case(E_zip,ES_zip,StageA_hourly_json,mode,case,*,artifact_zip_sha256,
                 time_limit_seconds=480):
    if case not in VALID_CASES:raise SourceLockedDispatchError("unknown source E or E+S case")
    a,b,target,pE,pES=load_matched_pilot(E_zip,ES_zip)
    raw=Path(StageA_hourly_json).read_bytes()
    source=json.loads(raw)
    t=construct_common_service(target,source,mode,
                               archived_StageA_zip_sha256=artifact_zip_sha256)
    params=pE if case=="E" else pES
    duty=build_screened_pressure_duty(
        "I_200bar",params["capacity_kg"],capacity_semantics=mode,
        source_PEM_outlet_bar_absolute=params["source_bafu_PEM_pressure_bar"],
        delivery_min_bar_absolute=params["source_pipeline_min_delivery_pressure_bar"])
    result=solve_ideal_storage(
        a["wind"],a["price"],t["common_target"],params,
        time_limit_s=time_limit_seconds,pressure_duty=duty)
    if (result.get("solver_status") not in (0,1)
        or result.get("hourly_solved_states") is None
        or result.get("pressure_vessel_eos_screened") is not True):
        raise SourceLockedDispatchError("unverified pressure-screened source MILP incumbent")
    residual=result["derived_audit"]["independent_max_physical_residuals"]
    if not residual or max(float(v) for v in residual.values())>2e-4:
        raise SourceLockedDispatchError("source 2023 matched hourly H2/energy/pressure/cost residual failed")
    if result["derived_audit"]["hours"]!=8760:
        raise SourceLockedDispatchError("source model does not contain 8760 hours")
    x=np.asarray(result["hourly_solved_states"],dtype=np.float64)
    if x.shape!=(HOURS,8):raise SourceLockedDispatchError("source MILP dispatch state shape mismatch")
    # Indep verification of exact 8760h delivered service, not annual totals alone.
    physical_h2=params["h2_coefficient_kg_mwh"]*x[:,0]-x[:,5]+x[:,6]
    if np.max(np.abs(physical_h2-t["common_target"]))>2e-4:
        raise SourceLockedDispatchError("source E and ES do not deliver same constructed hourly service")
    pressure=audit_gas_pressure_boundaries(duty,x[:,4])
    if pressure["EOS_hourly_mass_bounds_imply_pressure_limits"] is not True:
        raise SourceLockedDispatchError("Type I EOS 20bar/200bar source inventory bounds unverified")
    lower=result["best_bound_eur"]
    upper=float(result["derived_audit"]["total_wholesale_net_grid_eur2023"])
    if lower is not None and (not math.isfinite(lower) or lower>upper+0.1):
        raise SourceLockedDispatchError("solver lower bound exceeds verified incumbent wholesale cost")
    gap=result["mip_relative_gap"]
    certified=(result["solver_optimal"] and gap is not None and gap<=1e-6)
    if certified and lower is None:
        raise SourceLockedDispatchError("certified optimum lacks credible HiGHS objective bound")
    return {
       "schema_version":SCHEMA,"programme":"OEM-PTX-2026-01",
       "research_stage":"F3-C constructive common modelled hydrogen service; Stage B pressure-screened cost MILP",
       "source_year":2023,"mode":mode,"case":case,
       "original_source_E_archive_sha256":E_SHA,
       "original_source_EplusS_archive_sha256":ES_SHA,
       "source_StageA_E_hourly_archive_zip_sha256":artifact_zip_sha256,
       "source_StageA_E_hourly_json_sha256":hashlib.sha256(raw).hexdigest(),
       "source_StageA_shortage_canonical_float64_sha256":t["StageA_full_hourly_shortage_hash_sha256"],
       "published_source_sparse_sha256":SOURCE_SPARSE_SHA[mode],
       "common_hourly_modelled_H2_service_float64_sha256":t["target_hash_sha256"],
       "source_original_8760_hours":HOURS,
       "same_original_2023_weather_and_A44_price_every_hour":True,
       "common_hourly_modelled_H2_delivery_strict":True,
       "derived_common_hourly_reference_service_kg":float(np.sum(t["common_target"])),
       "source_original_E_hourly_reference_annual_delivery_kg":float(np.sum(target)),
       "original_full_2023_industrial_contract_kg":18_250_000.,
       "original_E_preexisting_full_contract_shortfall_kg":18_250_000.-float(target.sum()),
       "source_StageA_E_feasible_incumbent_additional_shortage_kg":float(t["source_shortage"].sum()),
       "physically_reduced_common_service_shortfall_vs_full_contract_kg":18_250_000.-float(t["common_target"].sum()),
       "source_StageA_incumbent_not_proven_globally_minimum":True,
       "global_common_service_selection_optimal":False,
       "source_modelled_hourly_delivery_not_measured_plant":True,
       "source_typeI_vessel_pressure_EOS_screen_only":True,
       "modelled_20bar_abs_min_delivery_node_pressure":True,
       "source_RVO_two_stage_compressor_electricity_included":True,
       "physical_compressor_part_load_and_CHT_not_validated":True,
       "installed_manufacturer_stationary_vessel_BOM_unknown":True,
       "native_full_BAFU_2026_v1_1_GWP":None,
       "source_whole_plant_discounted_EUR_LCOH_or_DCF":None,
       "2023_plant_or_vendor_validated":False,
       "complete_v1_0_LCA_or_TEA_ready":False,
       "case_source_original_capacity_kg":params["capacity_kg"],
       "case_source_initial_storage_model_kg":params["initial_kg"],
       "case_source_terminal_storage_model_kg":params["terminal_kg"],
       "case_model_200bar_reference_total_heel_kg":float(duty.gas_heel_kg),
       "solver":"SciPy HiGHS integer MILP",
       "solver_status":result["solver_status"],
       "solver_message":result["solver_message"],
       "solver_optimality_certified_to_gap_1e_6":bool(certified),
       "solver_relative_mip_gap":gap,
       "objective_minimised":"net wholesale grid electricity settlement 2023 EUR; excludes CAPEX and all non-grid OPEX",
       "source_2023_wholesale_operating_cost_feasible_incumbent_eur":upper,
       "solver_lower_bound_wholesale_eur":lower,
       "cost_comparison_with_other_case_optimal_only_if_both_certified":True,
       "case_modelled_annual_audit":result["derived_audit"],
       "gas_reference_EOS_pressure_bounds":pressure,
       "hourly_modelled_states_float64_sha256":hashlib.sha256(x.tobytes()).hexdigest(),
       "did_not_publish_raw_2023_wind_or_original_A44_price":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--E",required=True)
    p.add_argument("--ES",required=True)
    p.add_argument("--hourly-stageA",required=True)
    p.add_argument("--artifact-zip-sha256",required=True)
    p.add_argument("--mode",required=True,choices=tuple(SOURCE_SPARSE_SHA))
    p.add_argument("--case",required=True,choices=tuple(VALID_CASES))
    p.add_argument("--output",required=True)
    p.add_argument("--time-limit",type=int,default=480)
    args=p.parse_args()
    out=Path(args.output)
    if out.exists():raise FileExistsError("never replace a registered source-modelled F3-C physical benchmark")
    r=compare_case(args.E,args.ES,args.hourly_stageA,args.mode,args.case,
                   artifact_zip_sha256=args.artifact_zip_sha256,
                   time_limit_seconds=args.time_limit)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(args.mode,args.case,"source reconstructed service kg",r["derived_common_hourly_reference_service_kg"])
    print(args.mode,args.case,"2023 net grid wholesale EUR",r["source_2023_wholesale_operating_cost_feasible_incumbent_eur"])
    print("Solver certified optimum",r["solver_optimality_certified_to_gap_1e_6"],
          "mip gap",r["solver_relative_mip_gap"])
    print("NOT whole-plant LCA, TEA, observed plant, or complete original demand.")


if __name__=="__main__":
    main()
