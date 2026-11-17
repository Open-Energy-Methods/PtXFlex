"""F3-D physical matched H2 source 2023 -10% wind LP RELAXATION DIAGNOSTIC.

The F3-D source case (wind electrical availability multiplied by 0.90)
returned NO ACCEPTED MILP INCUMBENT. This independent *necessary*
feasibility check uses EXACTLY the same constraint rows/bounds/pressure
screen as the original solver but relaxes original unit-commitment and
charge/discharge binaries to [0,1] and replaces wholesale cost by ZERO.

LP INFEASIBLE (HiGHS status=2) proves the true integer formulation is
also infeasible under the mathematical model, subject to the numerical
solver's tolerances: MILP feasible set is a subset of LP feasible set.
LP FEASIBLE (status=0) does NOT prove the MILP feasible, and fractional
LP dispatch is expressly NOT a physically admissible H2 plant.
LP status 1/3/4 is UNKNOWN, never interpreted as infeasibility.

This does NOT prove a real H2 installation cannot serve the customers:
the 2023 model is a 200bar(a), 313K engineering screen with original
source electrolyzer/market/grid assumptions, not site-certified equipment.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from .f3_matched_ideal_benchmark import load_matched_pilot,solve_ideal_storage
from .f3_pressure_matched_service import construct_common_service
from .f3d_2023_source_hourly_counterfactuals import (
   SRC_E,SRC_ES,STAGEA,derive_scenario,protocol,require,sha_float64
)
from .pressure_storage_duty import build_screened_pressure_duty

SCHEMA="ptxflex.f3d_2023_weak_wind_090_model_relaxed_LP_feasibility_status_source_locked.v1"


def run_diagnostic(mode,E_original,ES_original,StageA_hourly_json,
                   StageA_archive_sha256,*,timeout=180):
    reg=protocol()
    require(mode in STAGEA,"unsupported source mode for weak-wind feasibility")
    require(StageA_archive_sha256==STAGEA[mode][0],"source 2023 StageA original SHA changed")
    e,es,original_H2,pE,pES=load_matched_pilot(E_original,ES_original)
    require(e["registered_sha"]==SRC_E and es["registered_sha"]==SRC_ES,
            "wrong E/E+S original 2023 physical model")
    stage=json.loads(Path(StageA_hourly_json).read_text(encoding="utf-8"))
    target=construct_common_service(original_H2,stage,mode,
           archived_StageA_zip_sha256=StageA_archive_sha256)
    require(target["target_hash_sha256"]==STAGEA[mode][1],
            "source 2023 original physical H2 same-hour duty changed")
    perturb=derive_scenario(e["price"],e["wind"],"wind_090_multiplier")
    require(perturb["source_price_2023_float64_sha256"]==
            perturb["scenario_price_float64_sha256"] and
            perturb["source_wind_2023_float64_sha256"]!=
            perturb["scenario_wind_float64_sha256"],
            "diagnostic not exactly the original -10pct wind-source electricity")
    out={}
    for case,parameters in (("E",pE),("E_plus_S",pES)):
        duty=build_screened_pressure_duty(
            "I_200bar",parameters["capacity_kg"],capacity_semantics=mode,
            source_PEM_outlet_bar_absolute=parameters["source_bafu_PEM_pressure_bar"],
            delivery_min_bar_absolute=parameters["source_pipeline_min_delivery_pressure_bar"])
        res=solve_ideal_storage(
            perturb["wind_available_mw"],perturb["price_eur_per_mwh"],
            target["common_target"],parameters,time_limit_s=timeout,
            mip_rel_gap=1e-6,pressure_duty=duty,
            diagnostic_only_lp_relaxation=True)
        require(res["schema_version"]==
                "ptxflex.f3d_identical_model_binary_relaxed_h2_feasibility_diagnostic.v1" and
                res["tested_hours"]==8760 and
                res["source_model_pressure_screened"] is True and
                res["LP_relaxed_binary_primal_NOT_a_valid_integer_dispatch"] is True and
                res["all_original_hourly_electricity_H2_storage_pressure_compressor_constraints_preserved"] is True,
                "LP relaxed problem not the original source physical model")
        out[case]=res
    proven=all(out[name]["LP_relaxation_infeasible_as_reported_by_HiGHS"]
               for name in ("E","E_plus_S"))
    return {
      "schema_version":SCHEMA,"programme":"OEM-PTX-2026-01",
      "source_year":2023,"scenario_id":"wind_090_multiplier",
      "mode":mode,
      "source_observed_E_SHA256":SRC_E,
      "source_observed_EplusS_SHA256":SRC_ES,
      "source_StageA_zip_SHA256":STAGEA[mode][0],
      "source_2023_common_h2_hourly_SHA256":target["target_hash_sha256"],
      "same_hourly_H2_and_identical_price_wind_for_E_and_EplusS":True,
      "source_hourly_2023_price_sha256":perturb["source_price_2023_float64_sha256"],
      "source_hourly_2023_wind_sha256":perturb["source_wind_2023_float64_sha256"],
      "counterfactual_source_2023_wind_power_sha256":perturb["scenario_wind_float64_sha256"],
      "experimental_design":"2023 ERA5-derived original source available wind MW ×0.90, original market price unchanged, 2023 original 8760hour source H2 target unchanged",
      "solver_necessary_condition_explanation":"LP relaxation is a superset of the original binary MILP feasible set; LP solver status2 under numerical tolerances supports model infeasibility; status0 does not show MILP feasibility",
      "both_original_source_E_and_ES_relaxed_LPs_reported_infeasible":proven,
      "paired_economic_preference_OR_certified_wholesale_savings_eur":None,
      "full_2023_industrial_18_25mkg_H2_demand_fulfilled":False,
      "not_observed_new_2022_or_2024_weather":True,
      "model_mathematical_not_physical_real_site_certification":True,
      "actual_manufacturer_typeI_station_bom_and_compressor_lifetime_verified":False,
      "full_LCA_LCOH_and_v1_release_passed":False,
      "E":out["E"],"E_plus_S":out["E_plus_S"],
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--E",required=True);p.add_argument("--ES",required=True)
    p.add_argument("--hourly-stageA",required=True)
    p.add_argument("--stageA-archive-sha256",required=True)
    p.add_argument("--mode",required=True,choices=tuple(STAGEA))
    p.add_argument("--time-limit",type=float,default=180.)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    out=Path(args.output)
    if out.exists():raise FileExistsError("source 2023 original LP diagnostic no overwrite")
    a=run_diagnostic(args.mode,args.E,args.ES,args.hourly_stageA,
                     args.stageA_archive_sha256,timeout=args.time_limit)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(a,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Original source 2023 weaker-wind LP feasibility diagnostic",a["mode"],
          "E status",a["E"]["solver_status_code"],a["E"]["solver_status_message"],
          "E+S status",a["E_plus_S"]["solver_status_code"],a["E_plus_S"]["solver_status_message"])
    print("This is a source-screened mathematical LP-necessary-condition analysis, not operating success or plant installation proof.")
if __name__=="__main__":main()
