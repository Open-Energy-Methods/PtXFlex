"""Prospective F3 backup-H2 delivery architecture: source-pinned design BASIS only.

Important time distinction: 2023 observed Dutch market/weather drives the
original model; Hynetwork's 2026 infrastructure/terms must NOT be labelled an
available physical 2023 backup facility. No site or contracted supplier exists.
A 900 kg US DOE composite-trailer nominal payload is a benchmark, NOT a Dutch
delivered usable payload at 20 bar(a) and never a certified trailer count.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE_REGISTRY=ROOT/"research/f3_backup_physical_source_register_v1.json"
RESULTS=ROOT/"data/results"
RECONCILED_SHA="5dead18cfa0c3fecf15562f423e01044bcc6ad4ba4f5212dfb44a010b0d1a0d3"
ENVELOPE_SHA={
 "max_inventory":"c65fda894ef4b30e09339ad88a3972625af78c17802fd0cb9a2fc25d3205882f",
 "usable_service":"d893c6388f14d276b2ef5d4bff4b6c8057dd252067f307f83b9baafcfa1e5308",
}
ORIGINAL_E="069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051"
ORIGINAL_ES="cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9"
SCHEMA="ptxflex.f3_prospective_backup_delivery_design_basis.v1"
MODES=("max_inventory","usable_service")


class CandidateNotVerified(ValueError):
    pass


def load_register(path=SOURCE_REGISTRY):
    x=json.loads(Path(path).read_text(encoding="utf-8"))
    if (x.get("schema_version")!="oem.ptx.f3_backup_physical_source_register.v1"
        or x.get("review_date_utc")!="2026-11-14"
        or x.get("fixed_dispatch_model_delivery_pressure_bar_absolute")!=20
        or x.get("source_case_semantics")!=list(MODES)):
        raise CandidateNotVerified("unregistered physical reference/pressure semantics")
    mandatory={
      "hynetwork_2026_transport_pressure",
      "hynetwork_2026_transport_quality",
      "hynetwork_2026_connection_process",
      "gasunie_rotterdam_2026",
      "eiga_15_21",
      "doe_tube_trailer",
      "iso_14687_2025",
      "ped_2014_68",
    }
    refs=x.get("source_references")
    if not isinstance(refs,list) or not mandatory.issubset({r.get("id") for r in refs}):
        raise CandidateNotVerified("missing network/legal/quality/logistics evidence reference")
    for ref in refs:
        if (not isinstance(ref.get("url"),str) or not ref["url"].startswith("https://")
            or not ref.get("locator") or ref.get("site_specific_contract") is not False):
            raise CandidateNotVerified("evidence citation incorrectly claimed as site-specific approval")
    safeguards=x.get("source_reference_safety",{})
    if not safeguards or any(value is not True for value in safeguards.values()):
        raise CandidateNotVerified("scientific safeguards missing")
    for key in (
        "site_connection_and_contract","2023_site_transport_availability",
        "customer_guaranteed_min_exit_pressure_bar_absolute",
        "regulator_and_pipe_min_pressure_drop_bar",
        "customer_guaranteed_flow_kg_h",
        "external_hydrogen_product_impurity_vector",
        "externally_sourced_h2_specific_GWP_kgCO2e_per_kg",
        "external_supply_cost_EUR2023_per_kg",
        "backup_station_material_BOM_and_end_of_life",
        "supplier_reliability_and_time_indexed_availability",
    ):
        if key not in x or x[key] is not None:
            raise CandidateNotVerified("unsourced site/contract field was populated as fact: "+key)
    if (x.get("matched_service_end_use_qualified") is not False
        or x.get("comparative_native_LCIA_and_full_EUR_DCF_allowed") is not False
        or x.get("pipeline_reference_not_exit_guarantee") is not True
        or x.get("us_doe_composite_nominal_payload_not_actual_usable_at_20bar") is not True):
        raise CandidateNotVerified("unsupported delivery capability or full LCA claim")
    if x.get("pipeline_entry_network_gauge_reference_min_bar_g")!=30 or x.get(
            "pipeline_entry_network_gauge_reference_max_bar_g")!=50:
        raise CandidateNotVerified("network entry gauge reference not from June 2026 annex 7")
    if x.get("us_doe_composite_trailer_benchmark_max_nominal_payload_kg")!=900:
        raise CandidateNotVerified("unregistered US reference payload")
    atm=x.get("reference_atmospheric_pressure_bar_for_unit_conversion_only")
    if not isinstance(atm,(int,float)) or isinstance(atm,bool) or not math.isfinite(atm) or abs(atm-1.01325)>1e-8:
        raise CandidateNotVerified("illustrative atmosphere not specified")
    if x.get("reference_atmospheric_pressure_is_analyst_illustrative_not_measured") is not True:
        raise CandidateNotVerified("gauge-to-absolute example mislabeled as actual pressure measurement")
    return x


def _read_hash(path,expected):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:
        raise CandidateNotVerified("source-derived original annual H2 result SHA256 changed")
    return json.loads(raw)


def _finite(x,key):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x):
        raise CandidateNotVerified("invalid original source scalar "+key)
    return float(x)


def evaluate_physical_routes(*,registry_path=SOURCE_REGISTRY,results_directory=RESULTS):
    registry=load_register(registry_path)
    root=Path(results_directory)
    original=_read_hash(root/"F3_2023_reconciled_research_evidence.json",RECONCILED_SHA)
    if (original.get("source_original_E_zip_sha256")!=ORIGINAL_E or
        original.get("source_original_EplusS_zip_sha256")!=ORIGINAL_ES or
        original.get("matched_service_E_vs_EplusS_LCA_or_TEA_comparison_eligible") is not False):
        raise CandidateNotVerified("frozen original service or LCA eligibility changed")
    output={
      "schema_version":SCHEMA,
      "programme":"OEM-PTX-2026-01",
      "reference_weather_and_wholesale_price_year":2023,
      "external_network_architecture_source_year":2026,
      "original_2023_hydrogen_reference_is_modelled_not_measured":True,
      "prospective_2026_infrastructure_is_not_observed_2023_site_supply":True,
      "actual_site_location":None,
      "physical_hydrogen_connection_and_supply_contract":None,
      "published_hynetwork_pressure_is_network_entry_not_customer_exit_guarantee":True,
      "published_hynetwork_quality_annex_is_not_end_use_grade_contract":True,
      "end_use_purity_grade_and_impurity_limits":None,
      "source_specific_20bar_absolute_delivery_pressure_verified":False,
      "fixed_original_model_required_delivery_pressure_bar_absolute":20.0,
      "source_reference_ids":[r["id"] for r in registry["source_references"]],
      "upstream_reconciled_source_derived_sha256":RECONCILED_SHA,
      "source_frozen_original_E_SHA256":ORIGINAL_E,
      "source_frozen_original_EplusS_SHA256":ORIGINAL_ES,
      "candidate_route_priority":"direct_industrial_H2_pipeline_import_if_site_connection_and_exits_proven",
      "backup_LCA_process_inventory_available":False,
      "backup_whole_system_EUR_DCF_available":False,
      "physically_verified_common_hourly_service":False,
      "comparative_environmental_or_cost_superiority_eligible":False,
      "evidence_maturity":"PROSPECTIVE_HARDWARE_DESIGN_BASIS_ONLY_NOT_OPERATIONAL",
      "modes":{}
    }
    for mode in MODES:
        e=_read_hash(root/f"F3_2023_original_E_source_hypothetical_backup_{mode}.json",ENVELOPE_SHA[mode])
        if (e.get("source_E_zip_sha256")!=ORIGINAL_E or e.get("source_EplusS_zip_sha256")!=ORIGINAL_ES
            or e.get("capacity_semantics")!=mode
            or e.get("source_pressure_screen_case")!="E"
            or e.get("external_H2_supplier_physically_specified") is not False
            or e.get("external_H2_pressure_regulation_and_transport_verified") is not False
            or e.get("external_H2_gas_purity_quality_verified") is not False
            or e.get("matched_service_LCA_TEA_comparison_permitted") is not False):
            raise CandidateNotVerified("incompatible source-proven 2023 hourly E additional load")
        for x in ("incremental_backup_H2_kgCO2e_per_kg","incremental_backup_cost_EUR_per_kg"):
            if e.get(x) is not None:
                raise CandidateNotVerified("invented backup environmental or economic factor")
        d=original.get("modes",{}).get(mode,{}).get("cases",{}).get("E",{})
        lo=_finite(d.get("minimum_additional_modelled_H2_shortfall_lower_bound_kg"),"lower shortage")
        hi=_finite(d.get("minimum_additional_modelled_H2_shortfall_upper_bound_kg"),"upper shortage")
        annual=_finite(e.get("single_incumbent_hypothetical_topup_annual_kg"),"annual topup")
        peak=_finite(e.get("single_incumbent_hypothetical_topup_max_kg_per_hour"),"peak hour")
        day=_finite(e.get("single_incumbent_hypothetical_topup_24h_peak_kg"),"peak 24 h")
        if not 0<lo<=hi+1e-4 or abs(annual-hi)>1e-3 or not 0<peak<=day<=annual+1e-4:
            raise CandidateNotVerified("source annual/hourly H2 replacement envelope inconsistent")
        if (d.get("minimum_positive_shortfall_proven") is not True or
            original["modes"][mode]["cases"]["E_plus_S"].get(
                "zero_shortfall_feasible_and_optimal_proven") is not True):
            raise CandidateNotVerified("original matched service pressure-screen evidence missing")
        # Example conversion ONLY, strictly NOT site-specific pipeline delivery data:
        illustrative_entry_abs=registry["pipeline_entry_network_gauge_reference_min_bar_g"]+registry[
            "reference_atmospheric_pressure_bar_for_unit_conversion_only"]
        reference_delta=illustrative_entry_abs-20
        nominal_trailer=registry["us_doe_composite_trailer_benchmark_max_nominal_payload_kg"]
        int_equiv=lambda q:int(math.ceil(q/nominal_trailer-1e-12))
        output["modes"][mode]={
            "source_evidence_sha256":ENVELOPE_SHA[mode],
            "source_stageA_proven_minimum_additional_shortage_lower_bound_kg":lo,
            "source_specific_feasible_incumbent_topup_annual_kg":annual,
            "source_specific_incumbent_peak_hour_topup_kg_h":peak,
            "source_specific_incumbent_largest_rolling_24hour_topup_kg":day,
            "source_specific_incumbent_occupied_hours":e["single_incumbent_hypothetical_topup_occupied_hours"],
            "source_specific_incumbent_number_of_separate_events":e["single_incumbent_contiguous_event_count"],
            "minimum_backup_flow_and_buffer_equipment_design_validated":False,
            "pathways":{
                "contracted_dedicated_H2_pipeline": {
                    "priority":"CONDITIONAL_FIRST_OPTION",
                    "status":"NO_SITE_NO_EXIT_PRESSURE_NO_FIRM_FLOW_OR_PURCHASE_AGREEMENT",
                    "documented_existing_site_connection":False,
                    "required_customer_node_pressure_bar_absolute":20.0,
                    "hynetwork_2026_general_network_entry_minimum_bar_gauge":30.0,
                    "reference_conversion_at_1_atm_entry_bar_absolute":illustrative_entry_abs,
                    "illustrative_entry_pressure_minus_20bar_node_bar":reference_delta,
                    "the_30barg_value_is_not_site_customer_exit_pressure":True,
                    "customer_guaranteed_min_exit_pressure_bar_absolute":None,
                    "customer_pipe_pressure_loss_bar":None,
                    "customer_regulator_margin_bar":None,
                    "customer_firm_hourly_nomination_capacity_kg_h":None,
                    "customer_h2_impurity_certification":None,
                    "hourly_2023_supply_availability":None,
                    "candidate_station_components_to_specify":[
                        "connection and legally agreed boundary node",
                        "custody-transfer metering and flow control",
                        "isolation and ESD valves, nonreturn/check",
                        "pressure regulation/overpressure relief and vent/purge",
                        "filter and sampling with contractual gas impurity limits",
                        "gas detection, classified electrical safety and materials review",
                        "site piping/pressure-drop and peak hydraulic calculation",
                        "redundancy, commissioning, maintenance and outage scenarios"
                    ],
                    "engineering_code_considerations":[
                        "EIGA DOC 15/21 (industrial consumer station guidance)",
                        "EU PED 2014/68/EU and relevant harmonized codes",
                        "hydrogen materials/pipe code selection and local permits"
                    ],
                    "full_plant_LCI_and_capex":None
                },
                "gaseous_tube_trailer_delivery": {
                    "priority":"SECONDARY_CONDITIONAL_LOGISTICS_SCREEN",
                    "status":"NO_DUTCH_SOURCE_SITE_PERMISSION_USABLE_PRESSURE_PAYLOAD_OR_REFILL_TIMES",
                    "us_DOE_nonEU_composite_reference_max_nominal_payload_kg":nominal_trailer,
                    "optimistic_payload_equivalents_at_900kg_per_nominal_load_annual":
                        int_equiv(annual),
                    "optimistic_payload_equivalents_at_900kg_per_nominal_load_peak_24h":
                        int_equiv(day),
                    "optimistic_payload_equivalents_at_900kg_per_nominal_load_peak_hour":
                        int_equiv(peak),
                    "payload_equivalents_are_not_actual_required_vehicle_trips":True,
                    "recovered_usable_H2_from_tank_down_to_20bar_absolute_kg":None,
                    "transfer_compressor_or_booster_and_buffer_design":None,
                    "logistics_schedule_and_delivery_access":None,
                    "operator_qualification_and_ADR_approvals":None,
                    "actual_deliverable_peak_flow_kg_h":None,
                    "full_plant_LCI_and_cost":None
                },
                "additional_on_site_electrolysis": {
                    "priority":"EXPANSION_OPTION_NOT_A_FREE_BACKUP",
                    "status":"ADDITIONAL_ELECTRICAL_CONNECTION_AND_WATER_AND_PEM_CAPEX_UNSOURCED",
                    "additional_grid_interconnection_available":None,
                    "additional_grid_interconnection_verified":False,
                    "additional_peaking_PEM_firm_electricity_MW":None,
                    "additional_electrolyser_and_cooling_LCI":None
                }
            },
            "mandatory_missing_proofs":[
                "plant geographical site and actual 2023/forward connection date",
                "signed H2 supplier or certified distribution and exit point pressure contract",
                ">= incumbent peak flow at specified pressure including line/regulator drop",
                "end-use-specific composition/impurity/water and metering certification",
                "8760h signed/feasible continuous backup nomination and reliability",
                "source-specific manufacturer materials and PED/ATEX/permits",
                "incremental service delivered fuel GWP and full native BAFU v1.1 LCI",
                "full EUR year-consistent tariff, source H2, replacement, CAPEX, OPEX",
                "source-preserving equal-delivered-service coupled dispatch and review"
            ],
            "environmental_and_tea_comparison_eligible":False
        }
    return output


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    dest=Path(a.output)
    if dest.exists():
        raise FileExistsError("do not overwrite physical hydrogen delivery screen evidence")
    result=evaluate_physical_routes()
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    for mode,d in result["modes"].items():
        p=d["pathways"]["gaseous_tube_trailer_delivery"]
        print(mode,"annual topup kg:",d["source_specific_feasible_incumbent_topup_annual_kg"],
              "peak kg/h:",d["source_specific_incumbent_peak_hour_topup_kg_h"],
              "US 900kg benchmark nominal payload equivalents annually:",
              p["optimistic_payload_equivalents_at_900kg_per_nominal_load_annual"])
    print("NO verified customer outlet pressure / physical supplier / GWP / EUR DCF. Comparison BLOCKED.")


if __name__=="__main__":
    main()
