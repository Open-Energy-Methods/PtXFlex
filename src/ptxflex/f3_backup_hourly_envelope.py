"""F3 Stage B — source-checked hourly hypothetical backup-H2 load envelope.

The Stage A 20t physical-pressure MILP produced a *feasible incumbent*
dispatch with additional unmet hourly hydrogen. A hypothetical delivery-node
top-up equal to that trace would mathematically restore the SAME frozen 2023
hourly E-delivered reference service. It is NOT a sourced backup plant:
H2 source, product purity, 20bar supply, reserve/ramp, transportation, carbon,
marginal grid electricity, investment and operating costs are all UNKNOWN.

The certified Stage A dual lower bound is a lower bound on additional
hydrogen needed by any pressure-screened E dispatch. The feasible-incumbent
sum is one reproducible upper-bound dispatch's hypothetical top-up quantity,
NOT proof that the minimum can be implemented as a physical backup.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

SCHEMA="ptxflex.F3_2023_hypothetical_source_hourly_H2_backup_load_envelope.v1"
SOURCE_E="069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051"
SOURCE_ES="cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9"
TARGET=16335279.317376737
FULL=18250000.0


class BackupEnvelopeError(ValueError):
    pass


def _real(x,name):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x):
        raise BackupEnvelopeError(name+" not finite numeric value")
    return float(x)


def _consecutive_events(mask):
    start=None
    spans=[]
    for i,yes in enumerate(mask):
        if yes and start is None:
            start=i
        if not yes and start is not None:
            spans.append([start,i-1])
            start=None
    if start is not None:spans.append([start,len(mask)-1])
    return spans


def source_hourly_backup_envelope(cert,trace,mode):
    """Accept only 8760h original E source-derived MILP results and labels."""
    if mode not in ("max_inventory","usable_service"):
        raise BackupEnvelopeError("capacity semantics not registered")
    if cert.get("schema_version")!="ptxflex.f3_stage_a_adequacy_certificates.v1":
        raise BackupEnvelopeError("unknown original-source Stage A certificate schema")
    if cert.get("original_source_E_sha256")!=SOURCE_E or cert.get("original_source_EplusS_sha256")!=SOURCE_ES:
        raise BackupEnvelopeError("original source ZIP SHA changed")
    if abs(_real(cert.get("reference_service_kg"),"reference")-TARGET)>.002 or abs(_real(
            cert.get("full_original_demand_kg"),"full demand")-FULL)>.002:
        raise BackupEnvelopeError("original 2023 H2 annual service changed")
    if cert.get("physical_installation_BOM_LCIA_TEA_complete") is not False or cert.get(
            "not_a_matched_service_cost_or_environmental_comparison") is not True:
        raise BackupEnvelopeError("source stage misclassified as full LCA or TEA")
    scenarios=cert.get("cases")
    if not isinstance(scenarios,dict) or set(scenarios)!={mode} or set(scenarios[mode])!={"E"}:
        raise BackupEnvelopeError("need exactly one original-source 20t E pressure case")
    r=scenarios[mode]["E"]
    if r.get("status")!="BOUNDED_INCUMBENT_MINIMUM_UNPROVEN":
        raise BackupEnvelopeError("expected original E cert with positive dual and feasible incumbent")
    if r.get("minimum_shortfall_certified") is not False or r.get("positive_minimum_shortfall_proven") is not True:
        raise BackupEnvelopeError("positive 20t minimum shortage not independently dual certified")
    lo=_real(r.get("shortfall_lower_bound_kg"),"min mathematical shortage lower bound")
    hi=_real(r.get("shortfall_upper_bound_kg"),"feasible incumbent additional shortage")
    if not (0<lo<=hi and hi<TARGET):
        raise BackupEnvelopeError("unphysical or uncertified source H2 shortfall interval")
    if r.get("annual_operating_cost_eur") is not None or r.get("native_full_system_GWP_kgCO2e") is not None:
        raise BackupEnvelopeError("unsupported backup climate/financial result")
    if trace.get("derived_source_not_original_raw_prices_or_wind") is not True or trace.get(
            "source_E_delivered_reference_profile_is_modelled") is not True:
        raise BackupEnvelopeError("original hourly H2 modelled-source declaration missing")
    values=trace.get("hourly_additional_shortfall_kg")
    if not isinstance(values,list) or len(values)!=8760:
        raise BackupEnvelopeError("original 2023 source hourly trace must be exactly 8760h")
    a=np.asarray([_real(v,"hourly source shortage") for v in values],dtype=float)
    if np.min(a)<-1e-5 or np.max(a)>TARGET:
        raise BackupEnvelopeError("negative/unbounded hourly additional source shortage")
    # Numerical tolerance: Stage A SciPy/HiGHS solution residuals <=2e-4kg.
    a=np.maximum(a,0.)
    if abs(float(np.sum(a))-hi)>2e-4:
        raise BackupEnvelopeError("hourly shortage series does not close to independently certified annual MILP incumbent")
    mask=a>1e-5
    if r.get("incumbent_shortfall_hours_only")!=int(np.sum(mask)):
        raise BackupEnvelopeError("original source shortfall-hour count does not match")
    spans=_consecutive_events(mask)
    rolling_24=np.convolve(a,np.ones(24),mode="valid")
    return {
      "schema_version":SCHEMA,
      "programme":"OEM-PTX-2026-01",
      "source_E_zip_sha256":SOURCE_E,
      "source_EplusS_zip_sha256":SOURCE_ES,
      "source_2023_original_E_reference_delivered_kg":TARGET,
      "original_full_2023_modelled_demand_kg":FULL,
      "preexisting_full_demand_shortfall_kg":FULL-TARGET,
      "additional_shortage_is_relative_to_E_delivered_reference_not_full_contract":True,
      "capacity_semantics":mode,
      "source_pressure_screen_case":"E",
      "modelled_hydrogen_not_measured_plant_production":True,
      "source_8760_sequential_hourly_indices":True,
      "stageA_original_MILP_min_shortage_certified_lower_bound_kg":lo,
      "stageA_original_feasible_dispatch_shortage_upper_bound_kg":hi,
      "single_incumbent_hypothetical_topup_annual_kg":float(np.sum(a)),
      "single_incumbent_hypothetical_topup_max_kg_per_hour":float(np.max(a)),
      "single_incumbent_hypothetical_topup_24h_peak_kg":float(np.max(rolling_24)),
      "single_incumbent_hypothetical_topup_occupied_hours":int(np.sum(mask)),
      "single_incumbent_contiguous_event_count":len(spans),
      "single_incumbent_longest_event_hours":max((end-start+1 for start,end in spans),default=0),
      "single_incumbent_contiguous_events_0_indexed_inclusive":spans,
      "modelled_ideal_delivery_node_topup_can_close_reference_hourly_shortage_by_definition":True,
      "external_H2_supplier_physically_specified":False,
      "external_H2_gas_purity_quality_verified":False,
      "external_H2_pressure_regulation_and_transport_verified":False,
      "external_backup_supply_ramp_availability_and_reliability_verified":False,
      "incremental_backup_H2_kgCO2e_per_kg":None,
      "incremental_backup_cost_EUR_per_kg":None,
      "backup_full_lca_or_tea_complete":False,
      "matched_service_LCA_TEA_comparison_permitted":False,
      "requires_source_20bar_abs_at_pipeline_node_and_product_quality_confirmation":True,
      "hourly_shortage_magnitude_is_a_modelled_feasible_incumbent_not_global_optimum":True,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--certificate",required=True)
    p.add_argument("--hourly-trace",required=True)
    p.add_argument("--mode",choices=("max_inventory","usable_service"),required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    dest=Path(args.output)
    if dest.exists():
        raise FileExistsError("do not overwrite original backup design-envelope evidence")
    cert=json.loads(Path(args.certificate).read_text())
    trace=json.loads(Path(args.hourly_trace).read_text())
    result=source_hourly_backup_envelope(cert,trace,args.mode)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(args.mode, "hypothetical H2 topup, kg/year:",result["single_incumbent_hypothetical_topup_annual_kg"])
    print("Peak source-hour topup, kg/h:", result["single_incumbent_hypothetical_topup_max_kg_per_hour"])
    print("Backup provider/cost/native emissions: UNKNOWN; LCA/TEA comparison blocked")


if __name__=="__main__":
    main()
