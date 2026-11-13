"""F3 source-grounded matched-service IDEAL storage-control benchmark.

This is NOT the final physical compressor / pressure-resolved F3 model.
It is an independent SciPy/HiGHS MILP that compares original E(20t) and
E+S(40t) at the EXACT SAME HOURLY DELIVERED-H2 SERVICE, derived from the
frozen 2023 E Stage B delivered service. Source original "E" model has
shortfall: matching its delivered schedule is not satisfying all original
50,000 kg/day demand. This is a controlled historical *pilot comparator*.

All hourly wind and 2023 NL price values are byte-hash-verified against
the original immutable PyNEXUS E and E+S ZIPs. The optimiser is new, not
presented as reproducing original variable-level dispatch. Gas pressure,
compressor electricity, usable inventory/heel, storage vessel manufacturing,
methanol, and full LCA/TEA remain excluded.

MODEL: source linearized PEM H2 yield, unit commitment, ramps, one signed
grid exchange (-export,+import), explicit wind curtailment, H2 storage
charge/discharge exclusivity, source standing loss and equal initial/final
inventory. No synthetic 2023 observations or hypothetical GHG factors.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix
import yaml

from .pynexus_hydrogen_benchmark import load_archive

SCHEMA="ptxflex.F3_frozen_2023_E_delivered_hourly_matched_IDEAL_storage.v0.1"
SOURCE_SHA={
 "E":"069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051",
 "E_plus_S":"cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9"
}
P,U,G,C,S,CH,DIS,Z=range(8)
DIM=8


class SourceLockedDispatchError(ValueError):
    pass


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _read_original(path):
    checked=load_archive(path)
    scenario=checked["scenario"]
    with zipfile.ZipFile(path) as z:
        record=json.loads(z.read(scenario+"/record.json"))
        cfg=yaml.safe_load(z.read(scenario+"/config.yaml"))
        raw=z.read(scenario+"/stage_b.csv")
    rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if len(rows)!=8760:
        raise SourceLockedDispatchError("original source must have 8760 hourly records")
    def col(name):
        a=np.asarray([float(x[name]) for x in rows],dtype=np.float64)
        if a.shape!=(8760,) or not np.isfinite(a).all():
            raise SourceLockedDispatchError("nonfinite or incomplete original source "+name)
        return a
    return {
      "scenario":scenario,
      "registered_sha":checked["archive_sha256"],
      "stage_b_sha":sha_bytes(raw),
      "price":col("electricity_price"),
      "wind":col("wind_available_mw"),
      "demand":col("h2_demand_kg_h"),
      "original_delivered":col("h2_demand_kg_h")-col("demand_slack_kg_h"),
      "original_source_power":col("power_optimized_mw"),
      "original_source_h2":col("h2_produced_kg_h"),
      "original_source_storage":col("storage_level_kg"),
      "configuration":cfg,
      "record":record,
    }


def _same_history(a,b):
    for field in ("price","wind","demand"):
        if not np.array_equal(a[field],b[field]):
            raise SourceLockedDispatchError("source 2023 E/E+S input arrays differ: "+field)
    for x in (a,b):
        if x["registered_sha"]!=SOURCE_SHA[x["scenario"]]:
            raise SourceLockedDispatchError("original source SHA changed")


def _source_physical_parameters(obj):
    cfg=obj["configuration"]
    h=cfg["hydrogen_storage"]
    el=cfg["electrolyzer"]
    grid=cfg["grid"]
    y=float(obj["record"]["metrics"]["linearized_h2_kg_per_mwh"])
    if not math.isfinite(y) or y<=0:
        raise SourceLockedDispatchError("unphysical original H2 coefficient")
    a={
      "capacity_kg":float(h["capacity_kg"]),
      "initial_kg":float(h["initial_level_kg"]),
      "terminal_kg":float(h["final_level_min_kg"]),
      "charge_max_kg_h":float(h["max_charge_rate_kg_h"]),
      "discharge_max_kg_h":float(h["max_discharge_rate_kg_h"]),
      "loss_fraction_per_hour":float(h["loss_fraction_per_hour"]),
      "rated_mw":float(el["rated_power_mw"]),
      "min_load_fraction":float(el["min_load_fraction"]),
      "max_load_fraction":float(el["max_load_fraction"]),
      "ramp_mw_h":float(el["ramp_rate_per_hour"])*float(el["rated_power_mw"]),
      "grid_max_mw":float(grid["connection_capacity_mw"]),
      "h2_coefficient_kg_mwh":y,
      "delivery_limit_kg_h":float(cfg["pipeline"]["max_flow_kg_per_s"])*3600,
      "source_bafu_PEM_pressure_bar":float(el["hydrogen_output_pressure_bar"]),
      "source_pipeline_min_delivery_pressure_bar":float(cfg["pipeline"]["min_outlet_pressure_bar"]),
    }
    if not (0<=a["loss_fraction_per_hour"]<1):
        raise SourceLockedDispatchError("invalid original fractional storage loss")
    return a


def load_matched_pilot(E_original,ES_original):
    a,b=_read_original(E_original),_read_original(ES_original)
    if a["scenario"]!="E" or b["scenario"]!="E_plus_S":
        raise SourceLockedDispatchError("require frozen E and E+S archives")
    _same_history(a,b)
    pE,pES=_source_physical_parameters(a),_source_physical_parameters(b)
    common_keys=set(pE)-{"capacity_kg"}
    for key in common_keys:
        if not math.isclose(pE[key],pES[key],rel_tol=0,abs_tol=1e-10):
            raise SourceLockedDispatchError("non-storage original configuration changed: "+key)
    if pE["capacity_kg"]!=20000 or pES["capacity_kg"]!=40000:
        raise SourceLockedDispatchError("unregistered original 20t/40t comparison")
    target=a["original_delivered"]
    if not np.all((target>=-1e-8)&(target<=a["demand"]+1e-8)):
        raise SourceLockedDispatchError("invalid original H2 reference service")
    if not np.isclose(np.sum(target),16335279.317376737,atol=.002):
        raise SourceLockedDispatchError("frozen original annual E-delivered service changed")
    return a,b,target,pE,pES


def solve_ideal_storage(wind_mw,price_eur_mwh,required_delivered_kg_h,params,
                        *,time_limit_s=240,mip_rel_gap=1e-6):
    """Minimize annual signed net grid wholesale settlement for fixed H2 service.

    Scientific optimization test: same hourly target in both configurations.
    The model includes SOURCE ideal inventory loss and original PEM coefficients
    but not pressure-verified usable capacity, compressor electric duty or
    vessel manufacture. NOT an industrial matched-service comparison.
    """
    wind=np.asarray(wind_mw,dtype=float)
    price=np.asarray(price_eur_mwh,dtype=float)
    target=np.asarray(required_delivered_kg_h,dtype=float)
    n=len(wind)
    if n<2 or price.shape!=(n,) or target.shape!=(n,) or not all(np.isfinite(x).all() for x in (wind,price,target)):
        raise SourceLockedDispatchError("invalid equal-length source hourly vectors")
    if min(wind.min(),target.min()) < -1e-8:
        raise SourceLockedDispatchError("negative wind or H2 service")
    if n>8760:raise SourceLockedDispatchError("original 2023 source has at most 8760 hours")
    if any(not math.isfinite(float(v)) for v in params.values()):
        raise SourceLockedDispatchError("unphysical source plant parameters")
    cap=params["capacity_kg"]
    initial=params["initial_kg"]
    final=params["terminal_kg"]
    y=params["h2_coefficient_kg_mwh"]
    pmax=params["rated_mw"]*params["max_load_fraction"]
    pmin=params["rated_mw"]*params["min_load_fraction"]
    ramp=params["ramp_mw_h"]
    gridmax=params["grid_max_mw"]
    charge_max=params["charge_max_kg_h"]
    discharge_max=params["discharge_max_kg_h"]
    loss=params["loss_fraction_per_hour"]
    if (min(cap,y,pmax,pmin,ramp,gridmax,charge_max,discharge_max)<=0
            or not 0<=initial<=cap or not 0<=final<=cap or not 0<=loss<1):
        raise SourceLockedDispatchError("invalid source model bounds")
    if max(target)>params["delivery_limit_kg_h"]+1e-9:
        raise SourceLockedDispatchError("source requested service exceeds pipeline mass flow")
    variable_count=n*DIM
    lower=np.zeros(variable_count,dtype=float)
    upper=np.zeros(variable_count,dtype=float)
    cost=np.zeros(variable_count,dtype=float)
    integ=np.zeros(variable_count,dtype=np.int32)
    idx=lambda t,k:DIM*t+k
    for t in range(n):
        lower[idx(t,P)],upper[idx(t,P)]=0,pmax
        lower[idx(t,U)],upper[idx(t,U)]=0,1
        lower[idx(t,G)],upper[idx(t,G)]=-gridmax,gridmax
        lower[idx(t,C)],upper[idx(t,C)]=0,wind[t]
        lower[idx(t,S)],upper[idx(t,S)]=0,cap
        lower[idx(t,CH)],upper[idx(t,CH)]=0,charge_max
        lower[idx(t,DIS)],upper[idx(t,DIS)]=0,discharge_max
        lower[idx(t,Z)],upper[idx(t,Z)]=0,1
        integ[idx(t,U)]=1
        integ[idx(t,Z)]=1
        cost[idx(t,G)]=price[t]

    rr=[]; cc=[];vv=[];bl=[];bu=[]
    def add(entries,lo=-math.inf,hi=math.inf):
        row=len(bl)
        bl.append(lo);bu.append(hi)
        for col,value in entries.items():
            if value:
                rr.append(row);cc.append(col);vv.append(float(value))
    for t in range(n):
        # Signed grid exchange: no simultaneous grid import and export.
        add({idx(t,P):1,idx(t,C):1,idx(t,G):-1},wind[t],wind[t])
        # Source original PEM unit commitment with nonzero minimum load.
        add({idx(t,P):1,idx(t,U):-pmin},0,math.inf)
        add({idx(t,P):1,idx(t,U):-pmax},-math.inf,0)
        # EXACT same hourly delivered service in E and E+S.
        add({idx(t,P):y,idx(t,CH):-1,idx(t,DIS):1},target[t],target[t])
        # Source standing H2 inventory loss at previous hour.
        row={idx(t,S):1,idx(t,CH):-1,idx(t,DIS):1}
        if t:row[idx(t-1,S)]=-(1-loss)
        add(row,(1-loss)*initial if t==0 else 0,(1-loss)*initial if t==0 else 0)
        # No simultaneous charge+discharge, even if solver degenerate.
        add({idx(t,CH):1,idx(t,Z):-charge_max},-math.inf,0)
        add({idx(t,DIS):1,idx(t,Z):discharge_max},-math.inf,discharge_max)
        if t:
            add({idx(t,P):1,idx(t-1,P):-1},-math.inf,ramp)
            add({idx(t-1,P):1,idx(t,P):-1},-math.inf,ramp)
    # Equal terminal bank inventory for comparable cyclic yearly service.
    add({idx(n-1,S):1},final,final)
    A=coo_matrix((vv,(rr,cc)),shape=(len(bl),variable_count)).tocsr()
    result=milp(c=cost,integrality=integ,bounds=Bounds(lower,upper),
                constraints=LinearConstraint(A,np.asarray(bl),np.asarray(bu)),
                options={"time_limit":float(time_limit_s),"mip_rel_gap":float(mip_rel_gap)})
    if result.x is None:
        raise SourceLockedDispatchError(f"full-physics-unverified matched ideal MILP infeasible or failed: {result.status}: {result.message}")
    x=np.asarray(result.x,dtype=float).reshape((n,DIM))
    audit=independently_audit(x,wind,price,target,params,source_cost=float(result.fun))
    opt_gap=getattr(result,"mip_gap",None)
    gap=float(opt_gap) if opt_gap is not None else None
    return {
      "model_schema":SCHEMA,
      "solver":"SciPy milp / HiGHS",
      "solver_status":int(result.status),
      "solver_optimal":bool(result.status==0),
      "solver_message":str(result.message),
      "mip_relative_gap":gap,
      "best_bound_eur":float(getattr(result,"mip_dual_bound",float("nan"))) if getattr(result,"mip_dual_bound",None) is not None else None,
      "source_year":2023,
      "modelled_hourly_delivered_kg":target.tolist(),
      "hourly_solved_states":x.tolist(),
      "derived_audit":audit,
      "source_input_history_kind":"observed NL market and ERA5-derived wind; H2 service from original solved model",
      "is_actual_full_hourly_contract_satisfied":False,
      "is_ideal_storage_only":True,
      "complete_physical_storage_compression_and_BAU_LCA":False,
      "valid_for_environmental_superiority_claim":False,
    }


def independently_audit(x,wind,price,target,params,*,source_cost,abs_tol=2e-4):
    """Recompute all physical equations from result, independent of solver matrix."""
    n=len(wind);y=params["h2_coefficient_kg_mwh"];loss=params["loss_fraction_per_hour"]
    p,u,g,cur,s,ch,dis,z=(x[:,i] for i in range(DIM))
    s_prev=np.r_[params["initial_kg"],s[:-1]]
    delivered=y*p-ch+dis
    balance_e=wind+g-p-cur
    balance_h=delivered-target
    balance_s=s-(1-loss)*s_prev-ch+dis
    cost_check=float(np.dot(g,price))
    bad={
     "electrical":float(np.max(np.abs(balance_e))),
     "H2_delivered":float(np.max(np.abs(balance_h))),
     "storage":float(np.max(np.abs(balance_s))),
     "terminal":float(abs(s[-1]-params["terminal_kg"])),
     "net_grid_cost":float(abs(cost_check-source_cost)),
     "charge_discharge_overlap_kg_h":float(np.max(np.minimum(ch,dis))),
     "startup_minload_MW":float(np.max(np.maximum(0,params["rated_mw"]*params["min_load_fraction"]*u-p))),
     "online_upper_MW":float(np.max(np.maximum(0,p-params["rated_mw"]*params["max_load_fraction"]*u))),
     "ramp_excess_MW":float(np.max(np.maximum(0,np.abs(np.diff(p))-params["ramp_mw_h"]))),
     "storage_capacity_excess_kg":float(np.max(np.maximum(0,s-params["capacity_kg"]))),
     "grid_interconnect_excess_MW":float(np.max(np.maximum(0,np.abs(g)-params["grid_max_mw"]))),
    }
    if any(v>abs_tol for v in bad.values()):
        raise SourceLockedDispatchError("independent mass/energy/feasibility/cost audit failed: "+str(bad))
    return {
      "independent_max_physical_residuals":bad,
      "annual_service_h2_kg":float(np.sum(target)),
      "annual_h2_produced_kg":float(np.sum(y*p)),
      "annual_h2_storage_loss_kg":float(np.sum(loss*s_prev)),
      "total_wholesale_net_grid_eur2023":cost_check,
      "grid_import_mwh":float(np.sum(np.maximum(g,0))),
      "grid_export_mwh":float(np.sum(np.maximum(-g,0))),
      "electrolyser_energy_mwh":float(np.sum(p)),
      "wind_used_mwh":float(np.sum(wind-cur)),
      "max_storage_state_kg":float(np.max(s)),
      "max_charge_kg_h":float(np.max(ch)),
      "max_discharge_kg_h":float(np.max(dis)),
      "hours":int(n),
      "strict_reference_hourly_delivery_profile_is_matched":True,
      "no_full_original_50t_daily_contract_claim":True,
      "no_pressure_or_compression_claim":True,
    }


def run_original_pair(E_original,ES_original,output,*,time_limit_s=240):
    destination=Path(output)
    if destination.exists():
        raise FileExistsError("will not overwrite source or previous original-pair results")
    a,b,target,cfgE,cfgES=load_matched_pilot(E_original,ES_original)
    runs={}
    for case,source,parameters in (("E",a,cfgE),("E_plus_S",b,cfgES)):
        res=solve_ideal_storage(a["wind"],a["price"],target,parameters,time_limit_s=time_limit_s)
        if not res["solver_optimal"] or res["mip_relative_gap"] is None or res["mip_relative_gap"]>1e-6:
            raise SourceLockedDispatchError("matched-service ideal comparison has not reached certified 1e-6 MILP gap for "+case)
        runs[case]={
         "source_archive_sha256":source["registered_sha"],
         "source_stage_b_sha256":source["stage_b_sha"],
         "plant_model":parameters,
         "solver_metadata":{k:v for k,v in res.items() if k not in ("hourly_solved_states","modelled_hourly_delivered_kg","derived_audit")},
         "audited_annual":res["derived_audit"],
         "hours":res["hourly_solved_states"]
        }
    # Same *actual* hourly delivery, not just denominator or annual tonnes.
    result={
      "schema_version":SCHEMA,"research_programme":"OEM-PTX-2026-01",
      "reference_service_provenance":"Frozen 2023 original PyNEXUS E hourly delivered hydrogen; not the original full 50t/day industrial demand",
      "source_original_E_sha256":a["registered_sha"],
      "source_original_EplusS_sha256":b["registered_sha"],
      "source_matched_market_and_weather":True,
      "source_matched_hourly_reference_H2_service_sha256":sha_bytes(target.tobytes()),
      "source_reference_hourly_delivery_kg":target.tolist(),
      "E":runs["E"],"E_plus_S":runs["E_plus_S"],
      "pilot_operational_service_parity":True,
      "source_full_demand_served_in_original":False,
      "pressure_resolved_operational_equivalence":False,
      "incremental_storage_vessel_BOM_included":False,
      "compressor_energy_and_losses_included":False,
      "native_full_BAFU_product_LCA_included":False,
      "fully_validated_v1_release":False
    }
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    return result


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--E",required=True)
    parser.add_argument("--ES",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--time-limit",type=float,default=240)
    opts=parser.parse_args()
    result=run_original_pair(opts.E,opts.ES,opts.output,time_limit_s=opts.time_limit)
    for case in ("E","E_plus_S"):
        print(case,json.dumps(result[case]["audited_annual"],sort_keys=True))
    print("matched original E-delivered hourly service, ideal storage only; NOT complete matched plant LCA")
