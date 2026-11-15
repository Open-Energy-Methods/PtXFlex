"""F3-D genuine-calendar E/E+S matched-service MILP (research method, not plant).

Phase 1: maximum *constant* 50t/day service fraction of the 20t E model,
independent of electricity price and E+S results. Unit-commitment,
hourly conservation, cyclic 10t storage, 20-200bar screened heel and
fixed-upper-pressure compressor electricity are retained.

Phase 2: same EXACT selected hourly H2 target and source-year price/wind
for E and E+S with certified cost primal/dual intervals. A source-year
calibration certificate is required before calculation. This is source
model screening, not installation feasibility, full plant LCA/DCF or a
2022/2024 real industrial hydrogen contract.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import time
from types import SimpleNamespace
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

from .f3_matched_ideal_benchmark import (
    P, U, G, C, S, CH, DIS, Z, DIM, SourceLockedDispatchError,
    independently_audit, solve_ideal_storage,
)
from .f3d_live_provider_pair_gate import verify_pair
from .pressure_storage_duty import (
    build_screened_pressure_duty, validate_screened_duty,
    audit_gas_pressure_boundaries,
)

ROOT=Path(__file__).resolve().parents[2]
REGISTRY=ROOT/"research/F3_D_ORIGINAL_PYNEXUS_2023_E_ES_FROZEN_PLANT_PARAMETERS_FOR_2022_2024_v1.json"
ALLOWED_YEARS={2022:8760,2024:8784}
SERVICE_CONTRACT_KG_DAY=50000.0
SEL_SCHEMA="ptxflex.f3d_E_price_blind_maximum_uniform_H2_service.v1"
OUTPUT_SCHEMA="ptxflex.f3d_2022_2024_equal_hourly_model_service_pressure_screening.v1"
E_SHA="069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051"
ES_SHA="cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9"


def require(ok,reason):
    if not ok: raise SourceLockedDispatchError("F3-D year-service: "+reason)


def array_sha(a):
    a=np.asarray(a,dtype="<f8")
    require(a.ndim==1 and np.isfinite(a).all(),"invalid source array")
    return hashlib.sha256(a.tobytes()).hexdigest()


def load_source_parameters():
    r=json.loads(REGISTRY.read_text(encoding="utf-8"))
    require(r.get("schema_version")=="oem.ptx.f3d_2023_frozen_source_parameters_for_external_calendar.v1",
            "plant registration version not frozen")
    src=r["source"]
    require(src["E_original_zip_sha256"]==E_SHA and
            src["E_plus_S_original_zip_sha256"]==ES_SHA and
            r["science_claims"]["source_parameters_independently_read_from_pinned_archives"] is True,
            "original 2023 E/E+S source registry not certified")
    require(r["original_h2_demand_kg_per_day"]==SERVICE_CONTRACT_KG_DAY,
            "changed reference flat demand")
    require(r["capacity_modes"]==["max_inventory","usable_service"],
            "capacity pressure semantics changed")
    common=r["model_common"]
    require(common["initial_kg"]==common["terminal_kg"]==10000 and
            common["h2_coefficient_kg_mwh"]==21.086108610861086 and
            common["loss_fraction_per_hour"]==0.0001 and
            common["rated_mw"]==125 and common["grid_max_mw"]==50 and
            common["source_bafu_PEM_pressure_bar"]==30 and
            common["source_pipeline_min_delivery_pressure_bar"]==20,
            "source physical model modified")
    cases={}
    for name,key,capacity in (("E","model_E",20000),("E_plus_S","model_E_plus_S",40000)):
        require(r[key]=={"capacity_kg":capacity},"source storage capacities changed")
        cases[name]={**common,**r[key]}
        require(all(math.isfinite(float(v)) for v in cases[name].values()),
                "unphysical original source plant field")
    return cases


def load_private_hourly(path,year,column,*,nonnegative=False):
    """Independent exact UTC chronology; no interpolation, including leap day."""
    path=Path(path)
    require(year in ALLOWED_YEARS,"only 2022/2024 alternative source years")
    with path.open("r",encoding="utf-8-sig",newline="") as handle:
        rows=csv.DictReader(handle)
        require(rows.fieldnames==["timestamp_utc",column],"private source fields changed")
        data=[]
        first=datetime(year,1,1,tzinfo=timezone.utc)
        for hour,row in enumerate(rows):
            require(hour<ALLOWED_YEARS[year],"private file has excess UTC hours")
            require(set(row)=={"timestamp_utc",column},"unrecognized source CSV column")
            want=(first+timedelta(hours=hour)).strftime("%Y-%m-%dT%H:%M:%SZ")
            require(row["timestamp_utc"]==want,"source UTC hour missing, shifted or duplicated")
            v=float(row[column])
            require(math.isfinite(v) and (not nonnegative or v>=0),
                    "nonfinite or unphysical raw provider source")
            data.append(v)
    require(len(data)==ALLOWED_YEARS[year],"private source has incomplete historical calendar")
    return np.asarray(data,dtype=np.float64)


def physical_duty(params,mode):
    require(mode in ("max_inventory","usable_service"),"unknown physical bank interpretation")
    duty=build_screened_pressure_duty(
        "I_200bar",params["capacity_kg"],capacity_semantics=mode,
        source_PEM_outlet_bar_absolute=params["source_bafu_PEM_pressure_bar"],
        delivery_min_bar_absolute=params["source_pipeline_min_delivery_pressure_bar"])
    validate_screened_duty(duty,params)
    return duty


def try_lp_bound_fixed_binary_certificate(c,A,lb,ub,lo,hi,*,n,time_limit_s,
                                          gap_tolerance=1e-6):
    """Certified exact-model selector: root LP bound + integer-feasible LP.

    This is a mathematically valid MILP optimality proof ONLY when both LPs
    terminate optimal, a binary-fixed primal is feasible, and their GLOBAL
    upper/lower alpha gap is <= the unchanged 1e-6 scientific tolerance.

    No binary feasibility constraints, pressure/physical balance equations,
    source-year target or HiGHS optimality tolerance are dropped. If the
    fixed binary trial is not certified, return None to run original MILP.
    """
    n=int(n)
    nvar=n*DIM+1
    require(len(c)==nvar and n>0,"invalid LP certificate model dimensions")
    lc=LinearConstraint(A,lb,ub)
    t0=time.monotonic()
    print(f"F3D_SELECTOR_ROOT_LP_START hours={n} fields={nvar}; no original provider values logged",flush=True)
    try:
        root=milp(c=c,bounds=Bounds(lo,hi),constraints=lc,
                  options={"time_limit":min(240.,max(5.,float(time_limit_s)*0.2))})
    except MemoryError:
        print("F3D_SELECTOR_ROOT_LP_OUT_OF_MEMORY: preserving all previous results",flush=True)
        return None
    if root.status!=0 or root.x is None or root.fun is None or not math.isfinite(float(root.fun)):
        print("F3D_SELECTOR_ROOT_LP_NOT_CERTIFIED; original mixed integer MILP required",flush=True)
        return None
    upper=float(-root.fun)
    require(-1e-7<=upper<=1.000001,"LP relaxed service upper outside [0,1]")
    root_states=np.asarray(root.x[:n*DIM],dtype=np.float64).reshape(n,DIM)
    for policy in ("LP_commitment","always_committed"):
        uidx=np.arange(n)*DIM+U
        zidx=np.arange(n)*DIM+Z
        if policy=="LP_commitment":
            u=(root_states[:,U]>=.5).astype(float)
        else:
            u=np.ones(n,dtype=float)
        # CH=charge; DIS=discharge. This is a trial integral direction,
        # not an assumption that the LP relaxation's physical cycles vanish.
        z=(root_states[:,CH]>=root_states[:,DIS]).astype(float)
        f_lo=lo.copy()
        f_hi=hi.copy()
        f_lo[uidx]=f_hi[uidx]=u
        f_lo[zidx]=f_hi[zidx]=z
        print(f"F3D_SELECTOR_FIXED_BINARY_LP_START policy={policy} "
              f"root_max_service_fraction_UB={upper:.9f}",flush=True)
        try:
            candidate=milp(
                c=c,bounds=Bounds(f_lo,f_hi),constraints=lc,
                options={"time_limit":min(240.,max(5.,float(time_limit_s)*0.2))},
            )
        except MemoryError:
            print("F3D_SELECTOR_FIXED_BINARY_LP_OUT_OF_MEMORY; trying another proof route",flush=True)
            continue
        if candidate.status!=0 or candidate.x is None or candidate.fun is None:
            print(f"F3D_SELECTOR_FIXED_BINARY_LP_NOT_FEASIBLE policy={policy} "
                  f"status={candidate.status}",flush=True)
            continue
        alpha=float(candidate.x[n*DIM])
        # Require integer feasibility independently of any fixed-bound claims.
        states=np.asarray(candidate.x[:n*DIM],dtype=np.float64).reshape(n,DIM)
        integral=max(float(np.max(np.abs(states[:,U]-np.rint(states[:,U])))),
                     float(np.max(np.abs(states[:,Z]-np.rint(states[:,Z])))))
        if integral>1e-6 or not math.isfinite(alpha) or alpha<=0:
            continue
        # The LP optimum is an upper bound on the ORIGINAL integer optimum.
        # Add 1e-8 to avoid rounding a valid dual bound down, which can
        # otherwise give spurious negative relative gaps.
        upper_safe=min(1.,upper+1e-8)
        if upper_safe<alpha-1e-7:
            continue
        rel_gap=max(0.,upper_safe-alpha)/max(alpha,1e-12)
        if rel_gap<=gap_tolerance:
            # Caller performs independent physics, mass, power, EOS replay.
            print(f"F3D_SELECTOR_LP_PRIMAL_DUAL_CERTIFIED policy={policy} "
                  f"alpha={alpha:.9f} upper_bound={upper_safe:.9f} "
                  f"relative_gap={rel_gap:.3g}; no integer branch tree",flush=True)
            return SimpleNamespace(
                x=candidate.x,status=0,mip_gap=rel_gap,
                mip_dual_bound=-upper_safe,
                certificate_kind="LP_GLOBAL_UPPER_BOUND_AND_INTEGER_FIXED_BINARY_FEASIBLE_PRIMAL",
                root_lp_optimization_status=0,
                fixed_binary_lp_optimization_status=0,
                fixed_binary_primal_integrality_max=integral,
            )
        print(f"F3D_SELECTOR_FIXED_BINARY_LP_GAP_NOT_CERTIFIED policy={policy} "
              f"alpha={alpha:.9f} upper_bound={upper_safe:.9f} "
              f"relative_gap={rel_gap:.6g}",flush=True)
    print("F3D_SELECTOR_LP_PROOF_NOT_CERTIFIED; fallback original MILP with bounded search",flush=True)
    return None


def select_max_uniform_fraction(wind,params,pressure_duty,*,year=None,
                                time_limit_s=900,mip_rel_gap=1e-6,
                                testing_only=False):
    """Price-independent primary selection MILP with alpha in [0,1].

    Maximize alpha such that each t delivers exactly
      H2(t) = alpha * 50_000/24 [kg/h].
    Never select different targets for E and E+S, nor price-optimize
    service choice. The E storage and grid equations are the SAME as
    `solve_ideal_storage`, independently audited after convergence.
    """
    wind=np.asarray(wind,dtype=np.float64)
    n=len(wind)
    require(wind.ndim==1 and n>=2 and np.isfinite(wind).all() and
            np.min(wind)>=0,"wind not an eligible nonnegative vector")
    if not testing_only:
        require(year in ALLOWED_YEARS and n==ALLOWED_YEARS[year],
                "external observed source calendar is not full UTC 2022/2024")
    else:
        require(n<=8784,"synthetic test horizon exceeds leap calendar")
    require(pressure_duty is None or
            validate_screened_duty(pressure_duty,params) is True,
            "physical bank screening is not admitted")

    cap=float(params["capacity_kg"])
    initial=float(params["initial_kg"])
    terminal=float(params["terminal_kg"])
    yield_kg=float(params["h2_coefficient_kg_mwh"])
    pmax=float(params["rated_mw"])*float(params["max_load_fraction"])
    pmin=float(params["rated_mw"])*float(params["min_load_fraction"])
    ramp=float(params["ramp_mw_h"])
    gridmax=float(params["grid_max_mw"])
    charge=float(params["charge_max_kg_h"])
    discharge=float(params["discharge_max_kg_h"])
    loss=float(params["loss_fraction_per_hour"])
    require(cap>0 and yield_kg>0 and pmax>=pmin>0 and ramp>0 and
            gridmax>0 and charge>0 and discharge>0 and 0<=loss<1 and
            0<=initial<=cap and 0<=terminal<=cap,
            "source E parameters violate physical bound conditions")
    customer=SERVICE_CONTRACT_KG_DAY/24.
    require(customer<=params["delivery_limit_kg_h"],"modelled contract exceeds pipeline")
    floor=(pressure_duty.min_model_inventory_kg() if pressure_duty else 0.)
    electric_per_kg=(pressure_duty.compressor_mw_per_kg_h() if pressure_duty else 0.)
    heel_loss=(pressure_duty.inventory_equation_fixed_heel_leak_kg_h(loss)
               if pressure_duty else 0.)
    alpha_i=n*DIM
    count=alpha_i+1
    lo=np.zeros(count,dtype=float)
    hi=np.zeros(count,dtype=float)
    c=np.zeros(count,dtype=float)
    integer=np.zeros(count,dtype=np.int32)
    c[alpha_i]=-1.
    hi[alpha_i]=1.
    idx=lambda t,k:DIM*t+k
    for t in range(n):
        lo[idx(t,P)],hi[idx(t,P)]=0.,pmax
        lo[idx(t,U)],hi[idx(t,U)]=0.,1.
        lo[idx(t,G)],hi[idx(t,G)]=-gridmax,gridmax
        lo[idx(t,C)],hi[idx(t,C)]=0.,wind[t]
        lo[idx(t,S)],hi[idx(t,S)]=floor,cap
        lo[idx(t,CH)],hi[idx(t,CH)]=0.,charge
        lo[idx(t,DIS)],hi[idx(t,DIS)]=0.,discharge
        lo[idx(t,Z)],hi[idx(t,Z)]=0.,1.
        integer[idx(t,U)]=integer[idx(t,Z)]=1

    rr=[];cc=[];vv=[];lb=[];ub=[]
    def add(coeff,lower=-math.inf,upper=math.inf):
        k=len(lb)
        lb.append(lower);ub.append(upper)
        for j,v in coeff.items():
            if v:
                rr.append(k);cc.append(j);vv.append(float(v))
    for t in range(n):
        add({idx(t,P):1,idx(t,C):1,idx(t,G):-1,
             idx(t,CH):electric_per_kg},wind[t],wind[t])
        add({idx(t,P):1,idx(t,U):-pmin},0,math.inf)
        add({idx(t,P):1,idx(t,U):-pmax},-math.inf,0)
        add({idx(t,P):yield_kg,idx(t,CH):-1,idx(t,DIS):1,
             alpha_i:-customer},0,0)
        previous={idx(t,S):1,idx(t,CH):-1,idx(t,DIS):1}
        if t:previous[idx(t-1,S)]=-(1-loss)
        add(previous,(1-loss)*initial-heel_loss if t==0 else -heel_loss,
            (1-loss)*initial-heel_loss if t==0 else -heel_loss)
        add({idx(t,CH):1,idx(t,Z):-charge},-math.inf,0)
        add({idx(t,DIS):1,idx(t,Z):discharge},-math.inf,discharge)
        if t:
            add({idx(t,P):1,idx(t-1,P):-1},-math.inf,ramp)
            add({idx(t-1,P):1,idx(t,P):-1},-math.inf,ramp)
    add({idx(n-1,S):1},terminal,terminal)
    A=coo_matrix((vv,(rr,cc)),shape=(len(lb),count)).tocsr()
    bounds=Bounds(lo,hi)
    constraints=LinearConstraint(A,np.asarray(lb),np.asarray(ub))
    # The 2022 usable-service selector exhausted Windows RAM in the
    # unbounded HiGHS MIP search. Try a GLOBAL LP dual bound with a
    # complete feasible fixed-hour binary LP certificate first.
    r=(try_lp_bound_fixed_binary_certificate(
            c,A,np.asarray(lb),np.asarray(ub),lo,hi,n=n,
            time_limit_s=time_limit_s,gap_tolerance=mip_rel_gap)
       if n>=1000 else None)
    if r is None:
        print(f"F3D_SELECTOR_EXACT_MILP_START hours={n} "
              f"node_limit={500 if n>=1000 else 'unlimited'} "
              f"gap={mip_rel_gap}; memory-bounded fallback",flush=True)
        options={"time_limit":float(time_limit_s),"mip_rel_gap":float(mip_rel_gap),
                 "disp":False}
        if n>=1000:
            # Prevent an unbounded search tree on ordinary Windows RAM.
            # If its exact gap is not met, STOP -- never call partial optimal.
            options["node_limit"]=500
        try:
            r=milp(c=c,integrality=integer,bounds=bounds,
                   constraints=constraints,options=options)
        except MemoryError as exc:
            raise SourceLockedDispatchError(
                "F3-D price-neutral full-year selector ran out of HiGHS RAM; "
                "completed historical cases are preserved. No source-year "
                "optimality or economic result is claimed for this mode."
            ) from exc
        r.certificate_kind="HIGHS_ORIGINAL_FULL_INTEGER_MIP_PRIMAL_DUAL"

    gap=float(getattr(r,"mip_gap",math.nan) or 0.) if getattr(r,"mip_gap",None) is not None else math.nan
    dual=getattr(r,"mip_dual_bound",None)
    require(r.status==0 and r.x is not None and math.isfinite(gap) and
            0<=gap<=mip_rel_gap and dual is not None and math.isfinite(float(dual)),
            "price-neutral E maximum-service MILP not certified: status "+str(r.status))
    alpha=float(r.x[alpha_i])
    alpha_ub=-float(dual)
    require(-1e-8<=alpha<=1.+1e-8 and
            alpha_ub>=alpha-1e-7 and alpha_ub<=1.+0.01 and
            np.max(np.abs(np.asarray(r.x[:alpha_i]).reshape(n,DIM)[:,U]-
                     np.rint(np.asarray(r.x[:alpha_i]).reshape(n,DIM)[:,U])))<1e-5,
            "source E selector alpha/dual/integer witness invalid")
    target=np.full(n,customer*alpha,dtype=np.float64)
    states=np.asarray(r.x[:alpha_i],dtype=np.float64).reshape(n,DIM)
    audit=independently_audit(
        states,wind,np.zeros(n,dtype=np.float64),target,params,
        source_cost=0.0,pressure_duty=pressure_duty)
    require(max(audit["independent_max_physical_residuals"].values())<=2e-4 and
            np.max(np.abs(yield_kg*states[:,P]-states[:,CH]+states[:,DIS]-target))<=2e-4,
            "independent E price-blind constant service physical audit failed")
    eos=(audit_gas_pressure_boundaries(pressure_duty,states[:,S])
         if pressure_duty is not None else None)
    require(eos is None or eos["EOS_hourly_mass_bounds_imply_pressure_limits"] is True,
            "E source bank pressure screening failed")
    return {
        "schema_version":SEL_SCHEMA,
        "year":year,
        "testing_only":testing_only,
        "selected_fraction_50t_per_day":alpha,
        "certified_fraction_upper_bound":alpha_ub,
        "modelled_E_flat_h2_service_kg_per_hour":float(customer*alpha),
        "modelled_E_annual_h2_service_kg":float(n*customer*alpha),
        "original_nominal_h2_demand_kg":float(n*customer),
        "selected_h2_target_float64_sha256":array_sha(target),
        "E_price_neutral_mip_relative_gap":gap,
        "E_max_service_global_optimality_certificate_method":r.certificate_kind,
        "E_max_service_global_LP_upper_bound_matches_fixed_binary_primal":
            r.certificate_kind=="LP_GLOBAL_UPPER_BOUND_AND_INTEGER_FIXED_BINARY_FEASIBLE_PRIMAL",
        "E_binary_price_neutral_feasible":True,
        "E_price_neutral_physical_residual_max":float(max(audit["independent_max_physical_residuals"].values())),
        "source_E_pressure_screen_only":pressure_duty is not None,
        "source_PEM_model_not_site_validated":True,
        "_E_selector_states_private":states,
        "_target_private":target,
    }


def certify_cost_case(result,target,case,year):
    require(result["source_year"]==year,"wrong source calendar solver provenance")
    require(result["solver_optimal"] is True and result["solver_status"]==0,
            case+" did not complete a certified integer solve")
    gap=result["mip_relative_gap"]
    require(gap is not None and math.isfinite(gap) and 0<=gap<=1e-6,
            case+" solver cost gap exceeds 1e-6")
    audit=result["derived_audit"]
    cost=float(audit["total_wholesale_net_grid_eur_unadjusted_source_calendar"])
    dual=result["best_bound_eur"]
    require(dual is not None and math.isfinite(dual) and dual<=cost+0.1,
            case+" lacks a valid economic lower bound")
    require(audit["strict_reference_hourly_delivery_profile_is_matched"] is True and
            audit["hours"]==len(target) and
            abs(audit["annual_service_h2_kg"]-float(np.sum(target)))<.005 and
            max(float(v) for v in audit["independent_max_physical_residuals"].values())<=2e-4,
            case+" independently audited mass/electricity/pressure conservation not certified")
    x=np.asarray(result["hourly_solved_states"],dtype=np.float64)
    require(x.shape==(len(target),DIM),"missing source full-year dispatch witness")
    return {
        "modelled_cost_eur_in_source_calendar_not_inflation_adjusted":cost,
        "solver_cost_lower_bound_eur":float(dual),
        "mip_relative_gap":float(gap),
        "modelled_hourly_H2_service_sha256":array_sha(target),
        "modelled_annual_hydrogen_kg":audit["annual_service_h2_kg"],
        "modelled_grid_import_mwh":audit["grid_import_mwh"],
        "modelled_grid_export_mwh":audit["grid_export_mwh"],
        "modelled_compressor_electricity_mwh":audit["annual_compression_electricity_mwh"],
        "modelled_hydrogen_storage_peak_kg":audit["max_storage_state_kg"],
        "max_independent_residual":max(float(v) for v in audit["independent_max_physical_residuals"].values()),
        "pressure_EOS_screen_bounds":audit.get("pressure_EOS_bounds"),
        "source_hourly_dispatch_float64_sha256":array_sha(x.reshape(-1)),
        "not_actual_industrial_operation":True,
    }


def run_verified_year(year,mode,price_root,wind_root,reference_price_root,
                      reference_wind_root,*,selection_limit_s=900,dispatch_limit_s=900,
                      private_witness_out=None):
    require(year in ALLOWED_YEARS,"only external 2022/2024 source years")
    require(mode in ("max_inventory","usable_service"),"unknown source bank scenario")
    gate=verify_pair(year,price_root,wind_root,reference_price_root,reference_wind_root)
    require(gate["source_price_and_weather_calendar_and_original_hashes_verified"] is True and
            gate["actual_2023_original_price_reproduction"] is True and
            gate["actual_2023_original_wind_reproduction"] is True,
            "source provider price/wind original hashes and 2023 anchor not independently verified")
    price=load_private_hourly(Path(price_root)/"normalized_UTC_price.csv",year,"day_ahead_eur_mwh")
    wind=load_private_hourly(Path(wind_root)/"normalized_UTC_wind.csv",year,"wind_available_mw",nonnegative=True)
    require(array_sha(price)==gate["year_price"]["normalized_float64_sha256"] and
            array_sha(wind)==gate["year_wind"]["normalized_float64_sha256"],
            "private provider 2022/2024 arrays differ from calibrated original source admission")
    params=load_source_parameters()
    pE=params["E"];pES=params["E_plus_S"]
    duties={name:physical_duty(p,mode) for name,p in params.items()}
    service=select_max_uniform_fraction(wind,pE,duties["E"],year=year,
                                        time_limit_s=selection_limit_s)
    target=service.pop("_target_private")
    selected_E_states=service.pop("_E_selector_states_private")
    answers={}
    private_states={}
    for case,p in params.items():
        r=solve_ideal_storage(wind,price,target,p,
                              source_calendar_year=year,
                              external_year_input_class="private_provider_pair_admission_candidate_not_peer_reviewed",
                              pressure_duty=duties[case],
                              time_limit_s=dispatch_limit_s,mip_rel_gap=1e-6)
        answers[case]=certify_cost_case(r,target,case,year)
        private_states[case]=np.asarray(r["hourly_solved_states"],dtype=np.float64)
    e=answers["E"];es=answers["E_plus_S"]
    estimate=e["modelled_cost_eur_in_source_calendar_not_inflation_adjusted"]-es["modelled_cost_eur_in_source_calendar_not_inflation_adjusted"]
    low=e["solver_cost_lower_bound_eur"]-es["modelled_cost_eur_in_source_calendar_not_inflation_adjusted"]
    high=e["modelled_cost_eur_in_source_calendar_not_inflation_adjusted"]-es["solver_cost_lower_bound_eur"]
    require(low<=estimate+1e-3<=high+1e-3,
            "certified E/E+S source-year wholesale cost difference outside bound")
    if private_witness_out is not None:
        out=Path(private_witness_out)
        require(not out.exists(),"private full-hour dispatch witness cannot overwrite originals")
        original={
            "schema_version":"ptxflex.f3d_PRIVATE_original_source_dispatch_witness.v1",
            "year":year,"capacity_semantics":mode,
            "original_E_SHA256":E_SHA,"original_ES_SHA256":ES_SHA,
            "price_float64_sha256":array_sha(price),
            "wind_float64_sha256":array_sha(wind),
            "target_float64_sha256":array_sha(target),
            "target_hourly_kg":target.tolist(),
            "E_price_neutral_alpha_witness_hourly_states":selected_E_states.tolist(),
            "source_year_prices_and_wind_NOT_duplicated_in_witness":True,
            "source_original_provider_hourly_market_weather_kept_PRIVATE":True,
            "cases":{
                name:{
                    "source_model_parameters":p,
                    "Type_I_200bar_model_pressure_duty":asdict(duties[name]),
                    "cost_optimum_hourly_states":private_states[name].tolist(),
                }
                for name,p in params.items()
            },
            "not_measured_industrial_operation":True,
        }
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(original,separators=(",",":"),allow_nan=False)+"\n",encoding="utf-8")
    return {
        "schema_version":OUTPUT_SCHEMA,
        "year":year,"capacity_semantics":mode,
        "year_UTC_hours":ALLOWED_YEARS[year],
        "original_source_E_zip_SHA256":E_SHA,"original_source_ES_zip_SHA256":ES_SHA,
        "source_year_price_f64_sha256":array_sha(price),
        "source_year_wind_f64_sha256":array_sha(wind),
        "original_2023_E_and_ES_source_parameters_reused_as_scenarios":True,
        "provider_pair_source_2023_reconstruction_and_calendar_verified":True,
        "source_A44_and_ERA5_provider_original_files_held_private":True,
        "year_wind_provider_representation":gate.get("year_wind_provider_representation","ORIGINAL_MONTHLY_CDS_ERA5_NETCDF"),
        "year_wind_original_monthly_CDS_NetCDF_not_ARCO":(
            gate.get("year_wind_provider_representation","ORIGINAL_MONTHLY_CDS_ERA5_NETCDF")=="ORIGINAL_MONTHLY_CDS_ERA5_NETCDF"),
        "year_wind_ARCO_full_2023_original_CDS_8760h_calibration_required_and_source_checked":(
            gate.get("year_wind_alternate_ARCO_calibrated_2023_original_8760h",False)),
        "ERA5_2022_2024_source_may_be_repackaged_ARCO_not_original_monthly_CDS":True,
        "E_price_blind_identical_model_H2_service_selection":service,
        "E":e,"E_plus_S":es,
        "mathematically_matched_exact_same_modelled_hourly_H2_target":True,
        "cost_savings_E_minus_EplusS_source_calendar_nominal_eur":float(estimate),
        "solver_difference_guaranteed_lower_upper_interval_eur":[float(low),float(high)],
        "modelled_annual_hydrogen_not_full_50t_per_day_if_alpha_below_one":True,
        "energy_year_2022_and_2024_eur_not_yet_inflation_normalized":True,
        "actual_industrial_H2_delivery_or_independent_measurements":False,
        "vendor_200bar_compressor_and_storage_station_BOM_verified":False,
        "native_BAFU_whole_plant_GWP_verified":False,
        "installed_plant_LCOH_or_investment_DCF_certified":False,
        "independent_external_scientific_peer_review_completed":False,
        "v1_0_scientific_release_allowed":False,
        "no_provider_price_wind_or_dispatch_hourly_arrays_in_report":True,
    }


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--year",type=int,choices=sorted(ALLOWED_YEARS),required=True)
    ap.add_argument("--mode",choices=["max_inventory","usable_service"],required=True)
    ap.add_argument("--price-root",required=True)
    ap.add_argument("--wind-root",required=True)
    ap.add_argument("--reference-price-root",required=True)
    ap.add_argument("--reference-wind-root",required=True)
    ap.add_argument("--selection-time-limit",type=int,default=900)
    ap.add_argument("--dispatch-time-limit",type=int,default=900)
    ap.add_argument("--output",required=True)
    ap.add_argument("--private-witness-out",
                    help="Private full-hour cost/selection primal witness for independently checking physics; never commit")
    args=ap.parse_args(argv)
    target=Path(args.output)
    require(not target.exists(),"cannot overwrite an existing source-year model result")
    report=run_verified_year(args.year,args.mode,args.price_root,args.wind_root,
                             args.reference_price_root,args.reference_wind_root,
                             selection_limit_s=args.selection_time_limit,
                             dispatch_limit_s=args.dispatch_time_limit,
                             private_witness_out=args.private_witness_out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("F3-D source-year matched E/E+S",args.year,args.mode,
          "cost savings nominal EUR",report["cost_savings_E_minus_EplusS_source_calendar_nominal_eur"])
    print("NOT a full industrial contract, vendor cost quote, site operational prediction, BAFU GWP, or investment NPV")


if __name__=="__main__":
    main()
