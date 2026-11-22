"""F3-D exact-source-2023 8760h re-optimized equal-H2 stress benchmark.

Four controlled COUNTERFACTUAL transformations of ORIGINAL PyNEXUS source
2023 NL A44 price / ERA5-derived wind. The source raw ZIPs and Stage-A
physical H2 service are SHA checked in private CI. Original E20t and E+S40t
MUST serve one identical H2(t) within a mode, using the same transformed
price(t),wind(t) and 313K/20-200bar(a) Type-I compressor power model.

NOT authenticated 2022/2024 price or wind weather observations. NOT a
stochastic future market forecast. Do not publish original raw market arrays
or wind source/derived sensitive prices. Numerical residual/HiGHS bounds only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from .f3_matched_ideal_benchmark import load_matched_pilot,solve_ideal_storage,SourceLockedDispatchError
from .f3_pressure_matched_service import construct_common_service,SOURCE_SPARSE_SHA
from .pressure_storage_duty import build_screened_pressure_duty,audit_gas_pressure_boundaries

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"research/F3_D_2023_SOURCE_DERIVED_PRICE_WIND_COUNTERFACTUAL_PROTOCOL_v1.json"
SCHEMA="ptxflex.f3d_2023_source_hourly_joint_price_wind_paired_equalH2_counterfactual_stress.v1"
YEARS=8760
SOURCE_WIND_NOT_SITE="source 52.5N 3.5E offshore wind-resource grid, NOT an industrial H2 customer"
SUPPORTED=("price_circular_168h","price_centered_spread_150","wind_090_multiplier","wind_110_multiplier")
SRC_E="069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051"
SRC_ES="cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9"
STAGEA={
"max_inventory":("6731bdaeeaa01a531f577150815dcf6638c15d21bc0ccee5e9ac0fa748ffe3c8","8e0d55994c7fe5f1abd952771a1b169336893d12698147fb3a93cb61a4ee7a16"),
"usable_service":("18dec140df7cab63dd9cae8836e3f23fd2dcfb0370acd48db0e36e6af81813cd","6a30baf00ddb065cd906dedd711db7cbf67504c50b4fda5809c5dfd29b23fa87")
}

def require(x,msg):
    if not x:raise SourceLockedDispatchError("F3-D "+msg)


def sha_float64(x):
    x=np.asarray(x,dtype="<f8")
    require(x.ndim==1 and x.size==YEARS and np.isfinite(x).all(),
            "2023 observed hourly series not exactly 8760 finite float64 values")
    return hashlib.sha256(x.tobytes()).hexdigest()


def protocol():
    a=json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(a.get("schema_version")=="oem.ptx.f3d_source_2023_hourly_stress_protocol.v1" and
            a.get("source_year")==2023 and
            a.get("source_zip_E_sha256")==SRC_E and
            a.get("source_zip_EplusS_sha256")==SRC_ES and
            a.get("independently_observed_new_price_or_wind_year_available") is False and
            a.get("alternative_2022_2024_provider_files_independently_fetched_and_sha_verified") is False and
            a.get("derived_source_hourly_arrays_not_committed") is True and
            a.get("E_ES_require_same_adjusted_2023_market_and_wind_each_hour") is True and
            a.get("price_and_wind_changes_preserve_original_2023_H2_hourly_target") is True and
            a.get("full_economic_plant_GWP_or_LCOH_releasable") is False,
            "source 2023 original versus non-existing later observed year conflated")
    for mode in STAGEA:
        f=a["stageA_modelled_h2_deficits"][mode]
        require(f["archive_zip_sha256"]==STAGEA[mode][0] and
                f["common_hourly_H2_float64_sha256"]==STAGEA[mode][1],
                "original E source Stage A physical feasible common service changed")
    catalog=a.get("scenario_catalog",[])
    require(isinstance(catalog,list) and [c.get("id") for c in catalog]==list(SUPPORTED),
            "unregistered wholesale/wind source history perturbation")
    for c in catalog:
        require(c.get("weather_year_as_actual_other_year") is False and
                isinstance(c.get("causal_meaning"),str) and len(c["causal_meaning"])>35,
                "source-derived counterfactual falsely called new observed weather year")
    return a


def derive_scenario(price,wind,scenario):
    """No random draw, no new or invented 2022/2024 historical data."""
    require(scenario in SUPPORTED,"unsupported F3-D source-2023 price/wind perturbation")
    p=np.asarray(price,dtype=np.float64).copy()
    w=np.asarray(wind,dtype=np.float64).copy()
    psha=sha_float64(p);wsha=sha_float64(w)
    require(w.min()>=0,"negative original source wind capacity")
    if scenario=="price_circular_168h":
        p=np.roll(p,168)
    elif scenario=="price_centered_spread_150":
        p=np.median(p)+1.5*(p-np.median(p))
    elif scenario=="wind_090_multiplier":
        w=0.9*w
    elif scenario=="wind_110_multiplier":
        w=1.1*w
    require(np.isfinite(w).all() and w.min()>=0 and np.isfinite(p).all(),
            "invalid derived source hourly input")
    if scenario.startswith("wind_"):
        require(sha_float64(p)==psha,"original 2023 observed NL A44 price changed during wind-only stress")
    else:
        require(sha_float64(w)==wsha,"original source 2023 wind changed during price-only stress")
    if scenario=="price_circular_168h":
        require(np.array_equal(np.sort(p),np.sort(price)) and not np.array_equal(p,price),
                "not actually reshuffling original observed 2023 price vectors")
    if scenario=="price_centered_spread_150":
        require(np.isclose(float(np.median(p)),float(np.median(price)),atol=1e-10),
                "price source median not preserved by counterfactual spread")
    return {
        "price_eur_per_mwh":p,"wind_available_mw":w,
        "source_price_2023_float64_sha256":psha,
        "source_wind_2023_float64_sha256":wsha,
        "scenario_price_float64_sha256":sha_float64(p),
        "scenario_wind_float64_sha256":sha_float64(w),
        "price_mean_2023_eur_per_mwh":float(np.mean(price)),
        "price_mean_scenario_eur_per_mwh":float(np.mean(p)),
        "source_wind_annual_mwh":float(np.sum(wind)),
        "counterfactual_wind_annual_mwh":float(np.sum(w)),
        "market_price_2023_redistributed":False,
        "is_alternative_observed_price_or_wind_year":False
    }


def run_paired(mode,scenario,E_source,ES_source,stageA_hourly_json,stageA_archive_sha256,
               *,time_limit_s=720):
    reg=protocol()
    require(mode in STAGEA and scenario in SUPPORTED,"unregistered source scenario/mode")
    require(stageA_archive_sha256==STAGEA[mode][0],"bad real Stage A source artifact ZIP SHA")
    a,b,original_delivered,pE,pES=load_matched_pilot(E_source,ES_source)
    require(a["registered_sha"]==SRC_E and b["registered_sha"]==SRC_ES and
            np.array_equal(a["price"],b["price"]) and np.array_equal(a["wind"],b["wind"]),
            "not same original source E/ES 2023 prices and weather")
    tdata=json.loads(Path(stageA_hourly_json).read_text(encoding="utf-8"))
    c=construct_common_service(original_delivered,tdata,mode,
       archived_StageA_zip_sha256=stageA_archive_sha256)
    require(c["target_hash_sha256"]==STAGEA[mode][1],"hourly original E physically feasible H2 target invalid")
    pwind=derive_scenario(a["price"],a["wind"],scenario)
    results={}
    for case,params in (("E",pE),("E_plus_S",pES)):
        duty=build_screened_pressure_duty(
           "I_200bar",params["capacity_kg"],capacity_semantics=mode,
           source_PEM_outlet_bar_absolute=params["source_bafu_PEM_pressure_bar"],
           delivery_min_bar_absolute=params["source_pipeline_min_delivery_pressure_bar"])
        try:
            z=solve_ideal_storage(pwind["wind_available_mw"],pwind["price_eur_per_mwh"],
                    c["common_target"],params,time_limit_s=time_limit_s,
                    mip_rel_gap=1e-6,pressure_duty=duty)
        except SourceLockedDispatchError as exc:
            # Without original SciPy infeasibility CERTIFICATE, do NOT label
            # no incumbent/time-limit as mathematically infeasible.
            results[case]={
                "solver_outcome":"NO_ACCEPTED_INCUMBENT_OR_FAILED_UNKNOWN",
                "cost_modelled_counterfactual_eur2023":None,
                "solver_dual_eur2023":None,
                "source_2023_hourly_H2_target_proven_feasible_under_this_wind_stress":None,
                "cannot_conclude_matched_service_preference":True,
                "solver_error_class":type(exc).__name__
            }
            continue
        states=np.asarray(z["hourly_solved_states"],dtype=np.float64)
        require(states.shape==(YEARS,8),"source 8760h vector shape mismatch")
        h2=params["h2_coefficient_kg_mwh"]*states[:,0]-states[:,5]+states[:,6]
        audit=z["derived_audit"]
        require(np.max(np.abs(h2-c["common_target"]))<2e-4 and
                max(audit["independent_max_physical_residuals"].values())<2e-4 and
                audit["hours"]==YEARS and
                audit["pressure_EOS_bounds"]["EOS_hourly_mass_bounds_imply_pressure_limits"] is True,
                "source 2023 physical mass/energy/pressure and same H2 target failed")
        # Report signed price-times-hourly-grid independent objective.
        signed_cost=float(np.dot(states[:,2],pwind["price_eur_per_mwh"]))
        upper=float(audit["total_wholesale_net_grid_eur2023"])
        lower=z["best_bound_eur"]
        require(abs(upper-signed_cost)<1e-3 and
                lower is not None and math.isfinite(lower) and lower<=upper+0.1,
                "invalid source-price counterfactual grid monetary audit or lower bound")
        certified=(z["solver_optimal"] and z["mip_relative_gap"] is not None and
                   0<=z["mip_relative_gap"]<=1e-6)
        results[case]={
            "solver_outcome":"CERTIFIED_HIGHS_RELATIVE_GAP_LE_1E6" if certified else "FEASIBLE_BUT_UNCERTIFIED",
            "source_2023_hourly_H2_target_proven_feasible_under_this_wind_stress":True,
            "counterfactual_price_2023_real_eur_per_mwh_not_observed_new_year":True,
            "cost_modelled_counterfactual_eur2023":upper,
            "solver_dual_eur2023":lower,
            "solver_relative_mip_gap":z["mip_relative_gap"],
            "modelled_H2_delivered_kg":float(audit["annual_service_h2_kg"]),
            "source_PEM_electricity_mwh":float(audit["electrolyser_energy_mwh"]),
            "source_compressor_electricity_mwh":float(audit["annual_compression_electricity_mwh"]),
            "counterfactual_grid_import_mwh":float(audit["grid_import_mwh"]),
            "counterfactual_grid_export_mwh":float(audit["grid_export_mwh"]),
            "source_TypeI_screened_200bar_pressure_OK":True,
            "maximum_independent_hourly_residual":max(float(v) for v in audit["independent_max_physical_residuals"].values()),
            "modelled_source_hourly_electricity_and_hydrogen_state_sha256":hashlib.sha256(states.tobytes()).hexdigest(),
            "no_actual_2023_vendor_or_dynamically_qualified_compressor":True
        }
    e=results["E"];es=results["E_plus_S"]
    certified=e["solver_outcome"]=="CERTIFIED_HIGHS_RELATIVE_GAP_LE_1E6" and es["solver_outcome"]=="CERTIFIED_HIGHS_RELATIVE_GAP_LE_1E6"
    if certified:
        estimate=e["cost_modelled_counterfactual_eur2023"]-es["cost_modelled_counterfactual_eur2023"]
        lo=e["solver_dual_eur2023"]-es["cost_modelled_counterfactual_eur2023"]
        hi=e["cost_modelled_counterfactual_eur2023"]-es["solver_dual_eur2023"]
        require(lo<=estimate+1e-3<=hi+1e-3 and hi>=lo-1e-4,
                "source-certified 2023 transformed E/ES wholesale saving interval invalid")
    else:
        estimate=lo=hi=None
    return {
       "schema_version":SCHEMA,"programme":"OEM-PTX-2026-01",
       "source_observed_year":2023,
       "counterfactual_not_an_independently_verified_historical_weather_or_market_year":True,
       "scenario_id":scenario,"capacity_semantics":mode,
       "original_source_E_archive_SHA256":SRC_E,"original_source_ES_archive_SHA256":SRC_ES,
       "original_source_StageA_archive_SHA256":STAGEA[mode][0],
       "original_2023_hourly_E_feasible_common_H2_target_SHA256":c["target_hash_sha256"],
       "source_stageA_shortage_constructive_not_globally_minimal":True,
       "source_full_original_2023_industrial_contract_kg":18250000,
       "source_same_hourly_modelled_H2_year_kg":float(c["common_target"].sum()),
       "original_full_contract_H2_still_unserved_kg":18250000-float(c["common_target"].sum()),
       "source_2023_input_price_and_wind_provenance":{k:v for k,v in pwind.items() if k not in ("price_eur_per_mwh","wind_available_mw")},
       "transformation_method":next(x for x in reg["scenario_catalog"] if x["id"]==scenario),
       "physical_equipment_reference":"Type I paper reference 20-200bar absolute isothermal 313K, RVO compressor source 80/90 efficiency",
       "same_source_2023_h2_product_service_and_market_wind_for_E_ES":True,
       "both_H2_source_cases_certified_MIP_gap_le_1e6":certified,
       "paired_modelled_incremental_EplusS_wholesale_saving_eur2023_COUNTERFACTUAL_not_forecast":estimate,
       "paired_modelled_source_HiGHS_error_saving_bounds_eur2023":None if not certified else [lo,hi],
       "E":e,"E_plus_S":es,
       "actual_new_2022_or_2024_observed_pairing":False,
       "future_H2_supplier_storage_safety_and_delivered_quality_proven":False,
       "manufacturer_fully_installed_20t_incremental_storage_CAPEX_eur":None,
       "actual_incremental_non_grid_opex_eur":None,
       "matched_native_BAFU_GWP_per_kg_H2":None,
       "whole_plant_economic_GWP_and_v1_0_release_PASSED":False
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--E",required=True);p.add_argument("--ES",required=True)
    p.add_argument("--hourly-stageA",required=True)
    p.add_argument("--stageA-archive-sha256",required=True)
    p.add_argument("--mode",required=True,choices=tuple(STAGEA))
    p.add_argument("--scenario",required=True,choices=SUPPORTED)
    p.add_argument("--time-limit",type=int,default=720)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    out=Path(a.output)
    if out.exists():raise FileExistsError("do not overwrite registered source counterfactual result")
    r=run_paired(a.mode,a.scenario,a.E,a.ES,a.hourly_stageA,
                 a.stageA_archive_sha256,time_limit_s=a.time_limit)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(r["capacity_semantics"],r["scenario_id"],"2023-modelled new hourly stress wholesale saving EUR2023",
          r["paired_modelled_incremental_EplusS_wholesale_saving_eur2023_COUNTERFACTUAL_not_forecast"],
          "certified",r["both_H2_source_cases_certified_MIP_gap_le_1e6"])
    print("NO 2022/24 independently observed new weather year; no vendor actual 2026+ market price CAPEX/BOM/GWP/LCOH.")
if __name__=="__main__":main()
