"""F3 source-pinned Stage A adequacy: minimum additional H2 shortage.

Uses frozen 2023 PyNEXUS E hourly delivered H2 as fixed target for both
storage capacities. It reports NEW inadequacy arising from actual screened
vessel heel and RVO compressor electricity, rather than forcing an
infeasible equal-service cost comparison. It is not plant validation and
does not satisfy the original full 50t/day industrial demand.
"""
from __future__ import annotations
from dataclasses import asdict
import json
from pathlib import Path
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

from .f3_matched_ideal_benchmark import (
    load_matched_pilot,SourceLockedDispatchError,independently_audit
)
from .pressure_storage_duty import (
    build_screened_pressure_duty,validate_screened_duty,audit_gas_pressure_boundaries
)

P,U,G,C,S,CH,DIS,Z,SHORT=range(9)
DIM=9
SCHEMA="ptxflex.F3_frozen_2023_real_gas_pressure_adequacy_StageA.v0.1"


def minimum_new_shortfall(wind,price,target,params,duty,*,limit_seconds=300):
    wind=np.asarray(wind,dtype=float)
    price=np.asarray(price,dtype=float)
    target=np.asarray(target,dtype=float)
    n=target.size
    if n<2 or n>8760 or wind.shape!=(n,) or price.shape!=(n,):
        raise SourceLockedDispatchError("invalid common original source horizon")
    if not all(np.isfinite(x).all() for x in (wind,price,target)) or min(wind.min(),target.min())<0:
        raise SourceLockedDispatchError("invalid source wind, prices or hourly target")
    validate_screened_duty(duty,params)
    idx=lambda t,k:t*DIM+k
    lower=np.zeros(n*DIM);upper=np.zeros(n*DIM)
    cost=np.zeros(n*DIM)
    integral=np.zeros(n*DIM,dtype=np.int32)
    eta=params["h2_coefficient_kg_mwh"]
    loss=params["loss_fraction_per_hour"]
    comp=duty.compressor_mw_per_kg_h()
    fixed_heel_leak=duty.inventory_equation_fixed_heel_leak_kg_h(loss)
    pmax=params["rated_mw"]*params["max_load_fraction"]
    pmin=params["rated_mw"]*params["min_load_fraction"]
    for t in range(n):
        upper[idx(t,P)]=pmax
        upper[idx(t,U)]=1
        lower[idx(t,G)]=-params["grid_max_mw"]
        upper[idx(t,G)]=params["grid_max_mw"]
        upper[idx(t,C)]=wind[t]
        lower[idx(t,S)]=duty.min_model_inventory_kg()
        upper[idx(t,S)]=params["capacity_kg"]
        upper[idx(t,CH)]=params["charge_max_kg_h"]
        upper[idx(t,DIS)]=params["discharge_max_kg_h"]
        upper[idx(t,Z)]=1
        upper[idx(t,SHORT)]=target[t]
        integral[idx(t,U)]=integral[idx(t,Z)]=1
        cost[idx(t,SHORT)]=1.
    rr=[];cc=[];vv=[];lo=[];hi=[]
    def add(terms,lb=-np.inf,ub=np.inf):
        i=len(lo);lo.append(lb);hi.append(ub)
        for j,v in terms.items():
            if v:
                rr.append(i);cc.append(j);vv.append(float(v))
    for t in range(n):
        add({idx(t,P):1,idx(t,CH):comp,idx(t,G):-1,idx(t,C):1},wind[t],wind[t])
        add({idx(t,P):1,idx(t,U):-pmin},0,np.inf)
        add({idx(t,P):1,idx(t,U):-pmax},-np.inf,0)
        add({idx(t,P):eta,idx(t,CH):-1,idx(t,DIS):1,idx(t,SHORT):1},target[t],target[t])
        stock={idx(t,S):1,idx(t,CH):-1,idx(t,DIS):1}
        if t:stock[idx(t-1,S)]=-(1-loss)
        rhs=((1-loss)*params["initial_kg"] if t==0 else 0)-fixed_heel_leak
        add(stock,rhs,rhs)
        add({idx(t,CH):1,idx(t,Z):-params["charge_max_kg_h"]},-np.inf,0)
        add({idx(t,DIS):1,idx(t,Z):params["discharge_max_kg_h"]},-np.inf,params["discharge_max_kg_h"])
        if t:
            ramp=params["ramp_mw_h"]
            add({idx(t,P):1,idx(t-1,P):-1},-np.inf,ramp)
            add({idx(t-1,P):1,idx(t,P):-1},-np.inf,ramp)
    add({idx(n-1,S):1},params["terminal_kg"],params["terminal_kg"])
    A=coo_matrix((vv,(rr,cc)),shape=(len(lo),n*DIM)).tocsr()
    result=milp(c=cost,integrality=integral,
        bounds=Bounds(lower,upper),
        constraints=LinearConstraint(A,np.asarray(lo),np.asarray(hi)),
        options={"time_limit":float(limit_seconds),"mip_rel_gap":1e-6})
    if result.x is None or result.status!=0 or result.mip_gap is None or result.mip_gap>1e-6:
        raise SourceLockedDispatchError("minimum-shortfall Stage A not certifiably solved: "+str(result.message))
    x=np.asarray(result.x,dtype=float).reshape((n,DIM))
    shortage=x[:,SHORT]
    if np.min(shortage)<-1e-5 or np.max(shortage-target)>1e-5:
        raise SourceLockedDispatchError("invalid shortfall variable")
    actual=target-shortage
    # Source-independent physical/economic identities from existing F3 audit.
    audit=independently_audit(x[:,:8],wind,price,actual,params,
       source_cost=float(np.dot(x[:,G],price)),pressure_duty=duty)
    audit["pressure_EOS_bounds"]=audit_gas_pressure_boundaries(duty,x[:,S])
    mass_residual=np.max(np.abs(eta*x[:,P]-x[:,CH]+x[:,DIS]+shortage-target))
    if mass_residual>2e-4:
        raise SourceLockedDispatchError("source target/slack balance failed independent audit")
    return {
      "source_case_stage":"Minimize ADDITIONAL shortage against exact original E delivered 8760h service",
      "solver_optimal":True,"solver_gap":float(result.mip_gap),
      "solver_best_bound_unserved_kg":float(result.mip_dual_bound),
      "additional_shortfall_kg":float(np.sum(shortage)),
      "shortfall_hour_count":int(np.count_nonzero(shortage>1e-5)),
      "maximum_single_hour_shortfall_kg":float(np.max(shortage)),
      "original_E_delivered_reference_target_kg":float(np.sum(target)),
      "achievable_annual_h2_under_screen_kg":float(np.sum(actual)),
      "engineering_duty":asdict(duty),
      "audit":audit,
      "screening_only_no_full_contract_or_LCA":True,
      "additional_shortfall_by_hour_kg":shortage.tolist()
    }


def source_annual_pressure_adequacy(E_original,ES_original,out_directory,*,limit_seconds=300):
    a,b,target,pa,pb=load_matched_pilot(E_original,ES_original)
    folder=Path(out_directory)
    if folder.exists():
        raise FileExistsError("never overwrite the source original 2023 physical adequacy study")
    folder.mkdir(parents=True,exist_ok=False)
    summary={
      "schema_version":SCHEMA,"source_E_sha256":a["registered_sha"],
      "source_EplusS_sha256":b["registered_sha"],
      "source_electricity_NL_A44_and_wind_ERA5_real_hydrogen_modelled":True,
      "source_hourly_E_delivered_target_kg":float(target.sum()),
      "original_full_2023_H2_demand_kg":float(a["demand"].sum()),
      "source_bank":"Type I 200bar IJHE Table 2, 313K, 20bar absolute outlet",
      "compressor_model":"RVO/LBST compressor 80%, motor 90%, 2 ideal intercooled stages",
      "plant_validation":False,
      "complete_installation_BOM_LCA_and_TEA":False,
      "scenario_results":{}
    }
    for mode in ("max_inventory","usable_service"):
        summary["scenario_results"][mode]={}
        for case,params in (("E",pa),("E_plus_S",pb)):
            duty=build_screened_pressure_duty("I_200bar",params["capacity_kg"],
                capacity_semantics=mode,
                source_PEM_outlet_bar_absolute=params["source_bafu_PEM_pressure_bar"],
                delivery_min_bar_absolute=params["source_pipeline_min_delivery_pressure_bar"])
            try:
                r=minimum_new_shortfall(a["wind"],a["price"],target,params,duty,
                                        limit_seconds=limit_seconds)
                short=r.pop("additional_shortfall_by_hour_kg")
                summary["scenario_results"][mode][case]={
                  "status":"VERIFIED_STAGE_A_MIN_ADDITIONAL_SOURCE_SHORTFALL",**r}
                fname=mode+"_"+case+"_hourly_additional_shortfall.json"
                (folder/fname).write_text(json.dumps({
                  "hourly_additional_shortfall_kg":short,
                  "derived_source_not_original_raw_prices_or_wind":True,
                  "source_E_delivered_reference_profile_is_modelled":True
                },allow_nan=False)+"\n")
                summary["scenario_results"][mode][case]["hourly_evidence_file"]=fname
            except SourceLockedDispatchError as err:
                summary["scenario_results"][mode][case]={
                  "status":"NOT_CERTIFIED","reason":str(err)[:900],"source_duty":asdict(duty)}
            print(mode,case,summary["scenario_results"][mode][case]["status"],
                  summary["scenario_results"][mode][case].get("additional_shortfall_kg"))
            (folder/"stageA_2023_source_pressure_adequacy.json").write_text(
                json.dumps(summary,sort_keys=True,indent=2,allow_nan=False)+"\n")
    return summary

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--E",required=True)
    p.add_argument("--ES",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--time-limit",type=float,default=300)
    args=p.parse_args()
    source_annual_pressure_adequacy(args.E,args.ES,args.output,limit_seconds=args.time_limit)
