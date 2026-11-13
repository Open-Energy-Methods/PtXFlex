"""F3 original-source physically bounded bank feasibility matrix.

Never infer a winner from infeasible source cases. Both original E and
E+S and 2023 hourly delivery/weather/market inputs are locked by SHA.
The Type I 200bar tank is a literature reference, NOT an actual plant.
For all cases, save an explicit pass/infeasible/error record. No silent
synthetic "feasibility repair", constraint relaxation or fabricated costs.

For a physically **usable** 20/40t bank, source model storage S is the
withdrawable volume ABOVE the residual EOS heel, and full gas loss is
accounted from S+heel. For maximum **inventory** bank, original 20/40t
upper physical mass is unchanged and minimum S=EOS heel.
Both definitions are separately reported and never treated as identical.
"""
from __future__ import annotations
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

from ptxflex.f3_matched_ideal_benchmark import (
    load_matched_pilot, solve_ideal_storage, SourceLockedDispatchError
)
from ptxflex.pressure_storage_duty import build_screened_pressure_duty,validate_screened_duty
from ptxflex.hydrogen_physics import HydrogenPropertyError

SCHEMA="ptxflex.F3_pressure_storage_2023_source_technical_feasibility.v0.1"

def investigate(E_original,ES_original,out_directory,*,time_limit_s=250):
    a,b,target,pE,pES=load_matched_pilot(E_original,ES_original)
    root=Path(out_directory)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError("must never overwrite source-pressure feasibility evidence")
    root.mkdir(parents=True,exist_ok=True)
    result={
      "schema_version":SCHEMA,"programme":"OEM-PTX-2026-01",
      "source_original_E_SHA256":a["registered_sha"],
      "source_original_EplusS_SHA256":b["registered_sha"],
      "source_hourly_target_sha256":hashlib.sha256(target.tobytes()).hexdigest(),
      "matched_source_target_original_E_delivered_H2_kg":float(target.sum()),
      "target_not_original_total_full_50t_day_contract":True,
      "source_input_weather_and_price_identical_8760h":True,
      "source_vessel_paper_doi":"10.1016/j.ijhydene.2025.152849",
      "source_RVO_compressor":"https://www.rvo.nl/sites/default/files/2023-12/GHG_EF_including_conversion_efficiencies_for_RFNBO_GHG_calculations_LBST.pdf",
      "bank_reference":"Type I steel 200bar published physical vessel",
      "suction_and_isothermal_bank_temperature_K":313.,
      "efficiency_source_assumptions":{"compressor_isentropic":0.8,"motor":0.9},
      "outlet_pressure_max_bar_absolute":200.,
      "minimum_withdrawal_pressure_bar_absolute":20.,
      "staged_compressor_equal_intercooling_model":True,
      "intercooler_auxiliary_electricity_and_pressure_drop_missing":True,
      "approved_real_installation_or_vendor_motor_map":False,
      "manufacturer_BOM_and_full_native_BAFU_GWP":False,
      "source_pressure_gauge_vs_absolute_verified":False,
      "v1_release_ready":False,
      "scenarios":{}
    }
    for mode in ("max_inventory","usable_service"):
        case_results={}
        for label,params in (("E",pE),("E_plus_S",pES)):
            rec={"source_case":label,"source_model_capacity_kg":params["capacity_kg"],
                 "capacity_semantics":mode}
            duty=build_screened_pressure_duty("I_200bar",params["capacity_kg"],
                     capacity_semantics=mode,
                     source_PEM_outlet_bar_absolute=params["source_bafu_PEM_pressure_bar"],
                     delivery_min_bar_absolute=params["source_pipeline_min_delivery_pressure_bar"])
            rec["source_based_screened_duty"]=asdict(duty)
            try:
                validate_screened_duty(duty,params)
                x=solve_ideal_storage(a["wind"],a["price"],target,params,
                       time_limit_s=time_limit_s,pressure_duty=duty)
                rec["solver_status"]=x["solver_status"]
                rec["solver_message"]=x["solver_message"]
                rec["mip_gap"]=x["mip_relative_gap"]
                if not x["solver_optimal"] or x["mip_relative_gap"] is None or x["mip_relative_gap"]>1e-6:
                    rec["result_state"]="NOT_VERIFIED_SOLVER_OR_GAP"
                else:
                    rec["result_state"]="VERIFIED_PRESSURE_SCREEN_8760h"
                    rec["audited_annual"]=x["derived_audit"]
                    rec["solver_best_bound_eur2023"]=x["best_bound_eur"]
                    rec["actual_source_hourly_delivery_matched"]=True
                    state_file=root/f"{mode}_{label}_source_2023_8760h_modelled_states.json"
                    state_file.write_text(json.dumps({
                          "schema_version":SCHEMA,"research_scope":"physics-screened modelled dispatch only",
                          "source_original_case":label,"source_case_zip_sha256":a["registered_sha"] if label=="E" else b["registered_sha"],
                          "reference_service_profile_SHA256":result["source_hourly_target_sha256"],
                          "same_original_market_wind_and_hourly_H2_service":True,
                          "modelled_hourly_states":[{"P_MW":row[0],"grid_signed_MW":row[2],
                            "curtailment_MW":row[3],"stored_H2_model_kg":row[4],
                            "charge_kg_h":row[5],"discharge_kg_h":row[6]}
                            for row in x["hourly_solved_states"]],
                          "native_LCA_and_certified_vessel_absent":True
                    },sort_keys=True,allow_nan=False)+"\n")
                    rec["hourly_dispatch_artifact"]=state_file.name
            except (SourceLockedDispatchError,HydrogenPropertyError) as err:
                rec["result_state"]="PHYSICAL_MATCHED_SERVICE_NOT_FEASIBLE_OR_UNVERIFIED"
                rec["failure_classification"]=type(err).__name__
                rec["failure_message"]=str(err)[:700]
                rec["attempted_max_2023_source_target_without_relaxation"]=True
            case_results[label]=rec
            print(mode,label,rec["result_state"],rec.get("failure_message",""))
            # Save per-case before moving on, preserving partial scientific
            # evidence on a later solver/system failure.
            (root/f"{mode}_{label}_source_result.json").write_text(
                json.dumps(rec,indent=2,sort_keys=True,allow_nan=False)+"\n")
        a_case,b_case=case_results["E"],case_results["E_plus_S"]
        if a_case["result_state"]==b_case["result_state"]=="VERIFIED_PRESSURE_SCREEN_8760h":
            a_cost=a_case["audited_annual"]["total_wholesale_net_grid_eur2023"]
            b_cost=b_case["audited_annual"]["total_wholesale_net_grid_eur2023"]
            case_results["matched_service_comparison"]={
                "valid_under_200bar_source_pressure_screen_only":True,
                "same_8760h_modelled_delivered_H2_kg":a_case["audited_annual"]["annual_service_h2_kg"],
                "E_minus_ES_net_wholesale_eur2023":a_cost-b_cost,
                "lower_certified_approx_eur2023":a_case["solver_best_bound_eur2023"]-b_cost,
                "upper_certified_approx_eur2023":a_cost-b_case["solver_best_bound_eur2023"],
                "native_BAFU_comparative_GWP_complete":False,
                "source_PyNEXUS_full_original_demand_met":False,
                "v1_release_ready":False
            }
        else:
            case_results["matched_service_comparison"]={
                "valid":False,
                "reason":"At least one configuration failed source H2 service or certified numerical solution; no missing numerical cost/GWP invented."
            }
        result["scenarios"][mode]=case_results
        (root/"F3_pressure_screen_incremental_summary.json").write_text(
            json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    return result

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--E",required=True)
    p.add_argument("--ES",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--time-limit",type=float,default=250)
    arg=p.parse_args()
    result=investigate(arg.E,arg.ES,arg.output,time_limit_s=arg.time_limit)
    for mode,entry in result["scenarios"].items():
        print(mode,json.dumps(entry["matched_service_comparison"],sort_keys=True))
