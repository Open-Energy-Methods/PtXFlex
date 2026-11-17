"""F3-H2-CONTRACT: two-contract, pressure- and hourly-time-indexed H2 source gate.

Important: Hynetwork connects/transports H2, DOES NOT procure/supply H2.
Reference 2023 modelled shortage arises from PyNEXUS offshore ERA5 weather
(52.5N,3.5E) rather than an actual hydrogen end-use location. The 2026
Connection Exit Annex 12 is a network operating envelope and offers either
open-pipe or individually agreed reduced pressure via Contract Data Sheet.
Hynetwork exit connection evidence alone cannot qualify a molecule supplier.

This routine tests 8760 aligned model-hour flow, pressure, outage and
composition booleans for a no-buffer delivery interface only; it NEVER
certifies actual plant safety, hydraulics, contractual rights, cost or LCA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"data/results"
REG=ROOT/"research/f3_h2_exit_and_supplier_source_evidence_v1.json"
SOURCE_SHA={
    "max_inventory":"9acefa605c878e19f369f57cd94519fc9dd926beda284135529b7d89ce31208e",
    "usable_service":"9c66837c105e5c17e2fbdceb50250a2ea7940ac0a2a321a08ffec8cf81622999",
}
EXISTING_YEAR=2023
NETWORK_REFERENCE_YEAR=2026
HOURS=8760


class UnqualifiedContractEvidence(ValueError):
    pass


def _source_registry():
    data=json.loads(REG.read_text(encoding="utf-8"))
    if data.get("schema_version")!="oem.ptx.f3_NL_h2_connection_supplier_independent_evidence.v1":
        raise UnqualifiedContractEvidence("wrong NL source register")
    a=data.get("original_PyNEXUS_annual_config",{})
    location=a.get("original_ERA5_wind_resource_location",{})
    if (location.get("lat")!=52.5 or location.get("lon")!=3.5
        or a.get("industrial_H2_delivered_site_lat_lon") is not None
        or a.get("industrial_H2_customer_name_or_address") is not None
        or a.get("weather_grid_not_a_pipeline_connection_coordinate") is not True):
        raise UnqualifiedContractEvidence("offshore ERA5 weather coordinates falsely converted to installed hydrogen customer site")
    roles=data.get("commercial_and_technical_roles",{})
    if not all(roles.get(key) is True for key in (
         "hynetwork_is_not_H2_molecule_supply_guarantor",
         "supplier_or_shipper_is_distinct_from_network_operator",
         "requires_independent_signed_network_exit_connection_and_signed_H2_purchase_shipping_contract",
         "network_access_contract_alone_proves_no_guaranteed_gas")):
        raise UnqualifiedContractEvidence("HNS falsely assumed to be a merchant gas supply guarantor")
    ids={x.get("id") for x in data.get("official_operator_sources",[])}
    required={"hns_exit_general_2026","hns_exit_annex12_2026","hns_exit_annex3_2026",
              "hns_exit_annex4_example_2026","hns_csa_0126","hns_connection_process_2026",
              "hns_connection_policy_2026"}
    if not required.issubset(ids):
        raise UnqualifiedContractEvidence("missing official 2026 gas exit contractual source")
    if any(x.get("customer_specific_contract_available") is not False for x in data["official_operator_sources"]):
        raise UnqualifiedContractEvidence("operator standard PDF incorrectly marked installed customer contract")
    hhv=data.get("hynetwork_connection_study_annex_A_HHV_MJ_per_Nm3")
    density=data.get("hynetwork_connection_study_annex_A_density_kg_per_Nm3")
    factor=data.get("hynetwork_study_HHV_kWh_per_kg_derived")
    if (hhv!=12.74 or density!=0.090 or
        not isinstance(factor,(float,int)) or abs(factor-hhv/density/3.6)>1e-9
        or data.get("study_HHV_is_energy_conversion_not_hydrogen_supply_entitlement") is not True
        or data.get("contract_peak_capacity_kWh_per_hour_requires_correct_total_connection_flow_not_automatically_incremental_backstop") is not True):
        raise UnqualifiedContractEvidence("HNS study form HHV, total exit capacity or source conversion incorrectly represented")
    if (data.get("original_2023_Hynetwork_network_available_to_site") is not False
        or data.get("original_2023_Hynetwork_linkage_cannot_be_claimed") is not True
        or data.get("original_2023_actual_site_connection_existing") is not None
        or data.get("comparative_full_lifecycle_E_vs_ES_admissible") is not False):
        raise UnqualifiedContractEvidence("unsupported 2023 actual site/pressure/connection claim")
    for x in ("2026_any_customer_exit_pressure_specified_for_this_study",
              "2026_any_customer_exit_gas_quality_guaranteed_for_end_use",
              "2026_any_supplier_year_round_firm_flow_to_site",
              "2026_any_site_specific_supplier_GWP_kgCO2e_per_kg",
              "2026_any_site_specific_backup_cost_EUR_per_kg"):
        if data.get(x,"MISSING") is not None:
            raise UnqualifiedContractEvidence("unsourced 2026 project specific pressure, quality or supply cost")
    return data


def _source_demand(mode):
    if mode not in SOURCE_SHA:raise UnqualifiedContractEvidence("wrong 2023 source E storage capacity semantics")
    file=SRC/f"F3_2023_original_E_sparse_H2_backup_need_{mode}.json"
    raw=file.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA[mode]:
        raise UnqualifiedContractEvidence("original modelled 8760h source needs altered without review")
    d=json.loads(raw)
    if (d.get("schema_version")!="ptxflex.f3_2023_sparse_modelled_backup_hourly_need.v1"
       or d.get("original_source_year")!=EXISTING_YEAR
       or d.get("source_8760_hourly_count")!=HOURS
       or d.get("capacity_semantics")!=mode
       or d.get("zero_kg_h_at_all_hours_not_listed") is not True
       or d.get("modelled_need_not_actual_hydrogen_supplier_delivery") is not True
       or d.get("actual_supplier_capacity_and_quality_pressure_checked") is not False):
        raise UnqualifiedContractEvidence("unsupported source data service scope")
    v=[0.0]*HOURS;seen=set()
    for x in d["positive_H2_topup_needed_kg_by_0_based_source_hour"]:
        hour=x.get("hour_index_0_based")
        kg=x.get("additional_modelled_H2_kg")
        if not isinstance(hour,int) or isinstance(hour,bool) or hour in seen or not 0<=hour<HOURS:
            raise UnqualifiedContractEvidence("invalid original model hour index")
        if not isinstance(kg,(float,int)) or isinstance(kg,bool) or not math.isfinite(kg) or kg<=0:
            raise UnqualifiedContractEvidence("invalid original model positive shortage")
        seen.add(hour);v[hour]=float(kg)
    if (len(seen)!=d["positive_hours"] or
        abs(sum(v)-d["modelled_additional_annual_topup_for_feasible_incumbent_kg"])>1e-3 or
        abs(max(v)-d["source_incumbent_peak_kg_h"])>1e-3):
        raise UnqualifiedContractEvidence("source positive hours, annual or peak corrupted")
    return d,v


def _series(p,key,*,numeric=False):
    v=p.get(key)
    if not isinstance(v,list) or len(v)!=HOURS:
        raise UnqualifiedContractEvidence(key+" requires precisely 8760 aligned original MODEL hour records")
    if numeric:
        for x in v:
            if (isinstance(x,bool) or not isinstance(x,(int,float))
                or not math.isfinite(x) or x<0):
                raise UnqualifiedContractEvidence(key+" requires nonnegative finite kg/h or bar(a)")
        return [float(x) for x in v]
    if any(type(x) is not bool for x in v):
        raise UnqualifiedContractEvidence(key+" requires Boolean certified composition/connection status for each model hour")
    return v


def check_no_buffer_interface(mode,profile=None):
    """No physical/contractual certificate is issued even when toy flow screening clears.

    profile=None: sourced original model duty and all supplier requirements unresolved.
    User profiles can screen numeric flow, pressure, outages, purity only;
    three separate numeric rates are modeled at same H2 mass-flow boundary:
    producer firm capability, shipper transmission nomination, station capacity.
    Pure numeric screen ignores reactor/station transients, mixing, linepack,
    buffer dynamics, contractual enforcement, product quality measurement.
    """
    registry=_source_registry(); source,demand=_source_demand(mode)
    peak=max(demand)
    hhv=registry["hynetwork_study_HHV_kWh_per_kg_derived"]
    result={
        "schema_version":"ptxflex.f3_source_2023_supplier_qualification_no_buffer.v1",
        "mode":mode,
        "programme":"OEM-PTX-2026-01",
        "original_dispatch_year":EXISTING_YEAR,
        "prospective_network_terms_year":NETWORK_REFERENCE_YEAR,
        "not_actual_2023_operational_supplier":True,
        "wind_grid_lat_lon_not_real_industrial_site":True,
        "HNS_network_transport_not_molecule_supplier":True,
        "separate_supplier_gas_contract_and_network_exit_contract_needed":True,
        "exit_CDS_pressure_and_firm_flow_not_proved":True,
        "original_modelled_reference_service_is_only_E_original_delivered_not_full_H2_contract":True,
        "reference_pressure_bar_absolute":registry["source_required_original_model_delivery_pressure_bar_absolute"],
        "source_hourly_H2_need_sha256":SOURCE_SHA[mode],
        "source_mode_feasible_incumbent_annual_shortage_kg":sum(demand),
        "source_mode_feasible_incumbent_max_hour_kg_h":peak,
        "source_mode_peak_HHV_from_HNS_2026_CSA_kWh_h":peak*hhv,
        "peak_CSA_capacity_is_incremental_topup_only_not_whole_connected_exit":True,
        "source_positive_need_hours":sum(x>0 for x in demand),
        "supplier_professionally_qualified":False,
        "site_location_verified":False,
        "signed_HNS_exit_CDS_pressure_and_capacity_verified":False,
        "independent_signed_H2_purchase_and_shipper_nomination_verified":False,
        "end_use_gas_grade_certified":False,
        "hydrogen_station_P_and_ID_and_flow_hydraulics_verified":False,
        "full_Backup_LCI_and_DCF_verified":False,
        "full_matched_service_LCA_or_TEA_allowed":False,
        "financial_cost_EUR_per_kg":None,
        "environmental_GWP_kgCO2e_per_kg":None,
        "numerical_flow_only_result":"NOT_ASSESSABLE_NO_SUPPLIER_HOURLY_SERIES",
        "modelled_unmet_backup_need_kg":None,
        "modelled_unmet_backup_hours":None,
        "modelled_delivered_backup_kg":None,
        "illustrative_profile_only":None,
        "modeled_no_buffer":True,
        "original_hour_timestamps_not_reconstructed_from_clock_or_DST":True,
    }
    if profile is None:return result
    if not isinstance(profile,dict) or profile.get("scenario_class")!="SYNTHETIC_BOUNDARY_TEST_ONLY":
        raise UnqualifiedContractEvidence("only explicitly synthetic profiles may be assessed until actual independently verified site/contract evidence is available")
    if (profile.get("timebase")!="SOURCE_2023_8760_SEQUENTIAL_INDEX_ZERO_BASED"
        or profile.get("pressure_basis")!="ABSOLUTE_BAR_AT_CUSTOMER_PRODUCT_HEADER"
        or profile.get("flow_kg_per_hour_is")!="ANALYST_ASSUMED_NOT_CONTRACTUALLY_NOMINATED"):
        raise UnqualifiedContractEvidence("unverified source hourly alignment, customer bar(a) or transport nomination semantics")
    supplier=_series(profile,"supplier_kg_h",numeric=True)
    transport=_series(profile,"transport_nomination_kg_h",numeric=True)
    station=_series(profile,"station_capacity_kg_h",numeric=True)
    press=_series(profile,"product_header_pressure_bar_absolute",numeric=True)
    quality=_series(profile,"product_quality_acceptable",numeric=False)
    online=_series(profile,"both_supplier_and_exit_connection_operational",numeric=False)
    served=0.0; gap=0.0; unsatisfied=0; peak_gap=0.0
    # Capture counts where a positive hour fails solely due to each control;
    # indicators may overlap and are NOT additive to unserved mass.
    failures={"insufficient_supplier_flow_hours":0,
              "insufficient_transport_nominated_flow_hours":0,
              "insufficient_customer_station_flow_hours":0,
              "low_customer_product_pressure_hours":0,
              "product_quality_rejected_hours":0,
              "supplier_or_exit_connection_offline_hours":0}
    failed_indices=[]
    for i,need in enumerate(demand):
        if need<=0:continue
        if supplier[i]+1e-9<need:failures["insufficient_supplier_flow_hours"]+=1
        if transport[i]+1e-9<need:failures["insufficient_transport_nominated_flow_hours"]+=1
        if station[i]+1e-9<need:failures["insufficient_customer_station_flow_hours"]+=1
        if press[i]+1e-9<result["reference_pressure_bar_absolute"]:
            failures["low_customer_product_pressure_hours"]+=1
        if not quality[i]:failures["product_quality_rejected_hours"]+=1
        if not online[i]:failures["supplier_or_exit_connection_offline_hours"]+=1
        flow=min(supplier[i],transport[i],station[i])
        valid=(online[i] and quality[i]
               and press[i]+1e-9>=result["reference_pressure_bar_absolute"])
        delivered=min(need,flow) if valid else 0.0
        served+=delivered
        miss=max(0.0,need-delivered)
        if miss>1e-7:
            unsatisfied+=1;gap+=miss;peak_gap=max(peak_gap,miss);failed_indices.append(i)
    result.update({
      "numerical_flow_only_result":"ALL_MODEL_HOURS_MATHEMATICALLY_COVERED_NOT_PHYSICALLY_CERTIFIED"
                                   if unsatisfied==0 else
                                   "SYNTHETIC_ASSUMPTIONS_SHOW_INSUFFICIENT_FLOW_OR_PRODUCT_QUALIFICATION",
      "modelled_unmet_backup_need_kg":gap,
      "modelled_unmet_backup_hours":unsatisfied,
      "modelled_delivered_backup_kg":served,
      "largest_modelled_unmet_kg_in_one_hour":peak_gap,
      "source_h2_hour_index_nonzero_shortfall_remaining":failed_indices,
      "failed_condition_hour_counts_overlap_not_additive":failures,
      "illustrative_profile_only":True,
    })
    if abs((served+gap)-sum(demand))>1e-3:
        raise UnqualifiedContractEvidence("modelled source H2 mass not conserved")
    return result


def _illustration(mode, scenario):
    _,d=_source_demand(mode);maxneed=max(d)
    full_capacity=maxneed
    all_true=[True]*HOURS
    p={
       "scenario_class":"SYNTHETIC_BOUNDARY_TEST_ONLY",
       "timebase":"SOURCE_2023_8760_SEQUENTIAL_INDEX_ZERO_BASED",
       "pressure_basis":"ABSOLUTE_BAR_AT_CUSTOMER_PRODUCT_HEADER",
       "flow_kg_per_hour_is":"ANALYST_ASSUMED_NOT_CONTRACTUALLY_NOMINATED",
       "supplier_kg_h":[full_capacity]*HOURS,
       "transport_nomination_kg_h":[full_capacity]*HOURS,
       "station_capacity_kg_h":[full_capacity]*HOURS,
       "product_header_pressure_bar_absolute":[20.0]*HOURS,
       "product_quality_acceptable":all_true[:],
       "both_supplier_and_exit_connection_operational":all_true[:]
    }
    if scenario=="EXACT_PEAK_FLOW_20BARA_PERFECT_UPTIME":
        pass
    elif scenario=="BELOW_PEAK_FLOW_ONE_HALF":
        p["supplier_kg_h"]=[maxneed/2]*HOURS
    elif scenario=="LOW_PRESSURE_AT_CUSTOMER_NODE":
        p["product_header_pressure_bar_absolute"]=[19.0]*HOURS
    elif scenario=="EXIT_OR_SUPPLIER_OFFLINE_AT_PEAK_HOUR":
        idx=d.index(maxneed)
        p["both_supplier_and_exit_connection_operational"][idx]=False
    elif scenario=="PRODUCT_QUALITY_FAILED_AT_PEAK_HOUR":
        idx=d.index(maxneed)
        p["product_quality_acceptable"][idx]=False
    else:raise UnqualifiedContractEvidence("unregistered synthetic-only threshold scenario")
    return p


def source_only_boundary_tests():
    _source_registry()
    scenarios=[
     "EXACT_PEAK_FLOW_20BARA_PERFECT_UPTIME",
     "BELOW_PEAK_FLOW_ONE_HALF",
     "LOW_PRESSURE_AT_CUSTOMER_NODE",
     "EXIT_OR_SUPPLIER_OFFLINE_AT_PEAK_HOUR",
     "PRODUCT_QUALITY_FAILED_AT_PEAK_HOUR",
    ]
    outcomes={}
    for mode in SOURCE_SHA:
        cases={}
        for scenario in scenarios:
            q=check_no_buffer_interface(mode,_illustration(mode,scenario))
            cases[scenario]={
              "result":q["numerical_flow_only_result"],
              "unmet_h2_kg":q["modelled_unmet_backup_need_kg"],
              "unmet_h2_hours":q["modelled_unmet_backup_hours"],
              "delivered_h2_kg":q["modelled_delivered_backup_kg"],
              "condition_hours":q["failed_condition_hour_counts_overlap_not_additive"],
              "full_lca_tea_eligible":q["full_matched_service_LCA_or_TEA_allowed"],
              "physical_supplier_verified":q["supplier_professionally_qualified"],
            }
        zero=cases["EXACT_PEAK_FLOW_20BARA_PERFECT_UPTIME"]
        if abs(zero["unmet_h2_kg"])>1e-6 or zero["unmet_h2_hours"]!=0:
            raise UnqualifiedContractEvidence("synthetic source boundary peak assumption should cover every original modelled hour")
        for x in scenarios[1:]:
            if cases[x]["unmet_h2_kg"]<=0:
                raise UnqualifiedContractEvidence("scientific negative control unexpectedly passed: "+x)
        base=check_no_buffer_interface(mode)
        outcomes[mode]={
            "2023_source_mode":mode,
            "source_annual_additional_modelled_H2_kg":base["source_mode_feasible_incumbent_annual_shortage_kg"],
            "max_2023_incumbent_replacement_H2_kg_h":base["source_mode_feasible_incumbent_max_hour_kg_h"],
            "incremental_topup_HNS_CSA_study_form_HHV_kWh_h":base["source_mode_peak_HHV_from_HNS_2026_CSA_kWh_h"],
            "actual_connection_total_peak_HHV_kWh_h":None,
            "source_2023_hourly_shortage_SHA256":SOURCE_SHA[mode],
            "no_actual_h2_supplier_8760h_series":base["numerical_flow_only_result"],
            "mathematical_boundary_cases":cases,
        }
    return {
        "schema_version":"ptxflex.f3_2023_H2_shortage_vs_prospective_contractual_supply_thresholds.v1",
        "model_year":2023,
        "source_2026_Hynetwork_operator_terms_are_not_actual_2023_gas_supply":True,
        "original_ERA5_wind_location_not_a_real_H2_customer_exit_location":True,
        "network_operator_does_not_guarantee_hydrogen_supply":True,
        "supplier_contract_exit_connection_contract_both_missing":True,
        "Hynetwork_CSA_HHV_kWh_kg":_source_registry()["hynetwork_study_HHV_kWh_per_kg_derived"],
        "all_scenarios_ARE_MATHEMATICAL_synthetic_no_buffer_tests":True,
        "no_scenario_proves_supplier_availability_hydraulics_or_certified_end_use_quality":True,
        "native_BAFU_full_comparative_GWP":None,
        "full_EUR2023_system_DCF":None,
        "comparative_E_vs_ES_matched_service_permitted":False,
        "modes":outcomes,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    arg=parser.parse_args()
    target=Path(arg.output)
    if target.exists():raise FileExistsError("do not overwrite source-verified F3 supplier boundary control")
    v=source_only_boundary_tests()
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    for mode,d in v["modes"].items():
        print(mode,"source modeled peak kg/h",d["max_2023_incumbent_replacement_H2_kg_h"],
              "study HNS Annex A incremental peak kWh/h",
              d["incremental_topup_HNS_CSA_study_form_HHV_kWh_h"])
    print("No site, no signed connection data sheet, no merchant H2 supply guarantee; full comparative LCA/DCF BLOCKED.")


if __name__=="__main__":
    main()
