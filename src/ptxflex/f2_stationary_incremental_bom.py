"""F2/L1 stationary Type I reference BOM: 20t E -> 40t E+S, source-audited.

Peer-reviewed IJHE Type I 200bar Table 2 supplies per-vessel EMPTY EQUIPMENT
mass 2400kg and internal water volume 1.8m3, NOT an OEM steel-grade mass.
CoolProp real-gas EOS at 313K / 20-200bar(a) determines the independently
screened 20t and 40t gross vs usable capacities, by two distinct modes.
Public OEM heiserTEC PED stationary module 36x87L 210bar has a rated 49kg
H2 *nominal GROSS* but lacks stationed empty mass and certified source
200bar(a) temperature/pressures. Its mobile TPED 935kg empty bundle MUST
NOT be transferred to the stationary PED catalogue, ever.

This is an explicit, traceable EQUIPMENT REQUIREMENTS / UNCERTAINTY register.
No quantities or masses are invented for installed manifolds, supports,
cooler, compressor, valves, gas station, foundation, instruments, vents.
Neither complete supplier BOM, BAFU v1.1 native foreground LCI nor
discounted cash flow exists. Source F3-C operating evidence retains only
reference 2023 source dispatch and is used to derive duty specification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

from .storage_reference_vessels import screen_vessel_bank
from .hydrogen_physics import hydrogen_density_kg_m3

ROOT=Path(__file__).resolve().parents[2]
REGISTER=ROOT/"research/F2_L1_STATIONARY_TYPEI_OEM_AND_STANDARDS_SOURCE_REGISTER_v1.json"
RESULT_SHA={
    "max_inventory":{
      "E":"59aaa727416364c2f0f1df1544f32bfc4456550ef14ce3679d78fc9abbff5fed",
      "E_plus_S":"f53039f09b7005280023e6835dce60e5b595b0df76b254f14765e0df5a08e2e9"},
    "usable_service":{
      "E":"88597c1cbc5e07b5cbee84129dd64dede410470cc5078a7e8d19d3b5ca616662",
      "E_plus_S":"885ebc26c75107d8439aa9a5b29ec7666e1b933ee866f8c63423a22dc05131b6"}
}
SCHEMA="ptxflex.f2_l1_typeI_200bar_incremental_stationary_h2_equipment_requirements.v1"
SOURCE_E_SHA="069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051"
SOURCE_ES_SHA="cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9"


class IncompletePhysicalStation(Exception):pass


def require(flag,reason):
    if not flag:raise IncompletePhysicalStation(reason)


def source_register():
    data=json.loads(REGISTER.read_text(encoding="utf-8"))
    require(data.get("schema_version")=="oem.ptx.f2_l1_stationary_h2_equipment_source_register.v1",
            "unknown OEM/standards source register")
    models=data["original_source_hydrogen_model"]
    require(models["E_max_inventory_kg"]==20000 and models["E_plus_S_max_inventory_kg"]==40000 and
            models["storage_max_charge_kg_h"]==2200 and models["storage_max_discharge_kg_h"]==2200 and
            models["hydrogen_source_year"]==2023 and
            models["hydrogen_source_modelled_not_measured"] is True,
            "original source E/ES historical model configuration changed")
    require(data["temperature_screening_K"]==313 and
            data["screened_lower_pressure_bar_absolute"]==20 and
            data["screened_upper_pressure_bar_absolute"]==200 and
            data["reference_bar_is_abs_screening_assumption_not_vendor_pressure_plate"] is True,
            "sourced gas temperature or assumed pressure basis silently changed")
    rec={r["id"]:r for r in data["source_references"]}
    require(set(rec)=={"ijhe_adm_2026_table2","heisertec_cosmos_stationary_2026",
                      "heisertec_cosmos_mobile_not_stationary_mass",
                      "eiga_doc247_2024","burckhardt_HME_2026","EU_PED_2014_68_2026"},
            "source vessel/component/safety/pressure manufacturer evidence incomplete")
    paper=rec["ijhe_adm_2026_table2"]
    v=paper["verified_typeI_reference"]
    require(v["rated_pressure_bar"]==200 and v["empty_vessel_mass_kg"]==2400 and
            v["internal_volume_m3"]==1.8 and v["reference_vessels_per_paper_container"]==25 and
            v["reported_nominal_h2_kg_per_vessel"]==26 and
            paper["source_pressure_gauge_vs_absolute_explicitly_verified"] is False and
            paper["individual_manufacturer_steel_BOM_obtained"] is False,
            "peer-reviewed 200bar Type I shell source misrepresented as vendor manufacturer grade")
    st=rec["heisertec_cosmos_stationary_2026"]["vendor_example"]
    require(st["application"]=="stationary_PED_not_mobile_TPED" and
            st["pressure_class_nominal_bar"]==210 and
            st["pressure_basis_gauge_or_absolute_on_vendor_page"] is None and
            st["cylinders_per_stationary_bundle"]==36 and
            st["water_volume_per_cylinder_l"]==87 and
            st["reported_hydrogen_gross_kg_at_vendor_nominal_conditions_per_bundle"]==49 and
            st["stationary_module_nominal_empty_mass_kg"] is None and
            st["stationary_frame_steel_mass_kg"] is None,
            "heiserTEC true stationary PED source conflated with TPED mobile empty bundle")
    mobile=rec["heisertec_cosmos_mobile_not_stationary_mass"]
    require(mobile["mobile_example"]["nominal_empty_mobile_complete_bundle_kg"]==935 and
            mobile["mobile_example"]["stationary_application_or_PED_product"] is False and
            mobile["permanently_excluded_from_200bar_stationary_typeI_LCI_mass_transfer"] is True,
            "TPED mobile bundle mass cannot be used as a stationary PED vessel shell or rack")
    require(data["vendor_exact_stationary_module_empty_mass_kg"] is None and
            data["assumed_steel_manufacturing_kgCO2e_per_kg"] is None and
            data["installation_BOM_complete"] is False and
            data["native_full_system_LCA_and_cashflow_ready"] is False,
            "manufacturer mass or GWP/TEA field fabricated")
    return data,rec


def load_f3c_case(mode,case):
    path=ROOT/"data/results"/f"F3_C_2023_source_pressure_matched_{mode}_{case}.json"
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=RESULT_SHA[mode][case]:raise IncompletePhysicalStation("tampered 2023 F3-C original source physical dispatch")
    d=json.loads(path.read_bytes())
    require(d.get("mode")==mode and d.get("case")==case and d.get("source_year")==2023 and
            d.get("original_source_E_archive_sha256")==SOURCE_E_SHA and
            d.get("original_source_EplusS_archive_sha256")==SOURCE_ES_SHA and
            d.get("common_hourly_modelled_H2_delivery_strict") is True and
            d.get("solver_optimality_certified_to_gap_1e_6") is True and
            d.get("source_typeI_vessel_pressure_EOS_screen_only") is True and
            d.get("native_full_BAFU_2026_v1_1_GWP") is None and
            d.get("complete_v1_0_LCA_or_TEA_ready") is False,
            "F3-C audit/source not suitable to infer full physical plant equipment")
    return d


def _unknown(item,group,basis,source_id,unit="kg",*,equipment_status="REQUIRED_DESIGN_SCOPE"):
    return {
       "line_id":item,"system":group,
       "item_scope":basis,
       "quantity":None,
       "unit":unit,
       "empty_mass_kg":None,
       "manufacturer_quote_eur":None,
       "source_ref_id":source_id,
       "evidence_class":"ENGINEERING_REQUIRED_BUT_NOT_QUANTIFIED",
       "system_completeness_status":equipment_status,
       "contribution_to_full_LCI":"UNRESOLVED_NONZERO_NOT_ASSUMED_ZERO",
       "not_coupled_as_complete_native_BAFU_inventory":True
    }


def bom_lines(net_count,paper,st):
    # These are source-informed categories, not falsely sized manufacturer items.
    shell_mass=net_count*paper["empty_vessel_mass_kg"]
    categories=[
      ("steel_alloy_material_grade_and_inclusions","pressure_boundary","Actual compliant steel grade, forged cylinder chemistry, heat-treatment and shell/nozzle mass allocation","ijhe_adm_2026_table2"),
      ("rack_frames_and_anchors","storage_structure","Type I storage module frames, supports, anchors, lifting/inspection clearance, corrosion protection","eiga_doc247_2024"),
      ("high_pressure_headers_and_interconnects","hydrogen_process","H2-compatible high-pressure pipe material grade, DN/wall, welds, elbows, fittings and fabrication","eiga_doc247_2024"),
      ("isolation_valves_and_actuators","hydrogen_process","Per bank/pod isolation and actuated valves suitable for H2 and design pressure","eiga_doc247_2024"),
      ("non_return_valves_and_filters","hydrogen_process","Manifold strainers, H2 grade particulate filters and backflow prevention at delivery","eiga_doc247_2024"),
      ("pressure_relief_and_vent_stack","safety","Thermal/overpressure protection, relief discharge piping, safe vent location and dispersion analysis","eiga_doc247_2024"),
      ("pressure_regulation_delivery_header","hydrogen_process","Regulated 20bar absolute customer header + required pressure drops, reverse flow and relief protection","eiga_doc247_2024"),
      ("compressor_recips_and_seals","compression","30 to 200 bar assumed source charge compression, certified compressor map, seal, oil-free technology choice","burckhardt_HME_2026"),
      ("compressor_motor_drive_VFD","electrical","Rated electric motor, electrical drive power, motor/VFD MCC and wiring for selected compressor train","burckhardt_HME_2026"),
      ("intercooler_aftercooler_heat_exchange","thermal","Interstage and outlet heat rejection, cooling water/air system, exchanger mass, piping pressure drop","burckhardt_HME_2026"),
      ("cooling_pumps_and_fans","electrical_thermal","Actual auxiliary cooling electricity and pumps/fans duty for varying hydrogen charge pressure","burckhardt_HME_2026"),
      ("gas_quality_dryer_and_sample_system","hydrogen_process","H2 assay/impurities, sampling, moisture/oxygen and industrial customer acceptance requirements","eiga_doc247_2024"),
      ("pressure_temperature_flow_metering","instrumentation","Redundant pressure/temperature transmitters, H2-safe flow metering, calibrated uncertainty","eiga_doc247_2024"),
      ("hydrogen_leak_detection_ESD_ATEX","control_and_safety","Gas alarms, shutdown valves, emergency isolation, electrical area classification and safety logic","eiga_doc247_2024"),
      ("civil_foundations_and_construction","civil","Actual foundation, concrete, rebar, excavation, site access, bund arrangement and drainage","EU_PED_2014_68_2026"),
      ("inspections_fatigue_cycle_testing","maintenance","Fatigue analysis, inspection intervals, PED conformity, NDT, replacements, periodic pressure testing","eiga_doc247_2024"),
      ("installation_and_transport","construction","Regional transport, crane/lift and assembly/commissioning energy and installation losses","eiga_doc247_2024"),
      ("decommission_and_EOL","end_of_life","Spent pressure vessels recycling/remanufacture, scrap treatment, EOL transport","ijhe_adm_2026_table2"),
    ]
    known={
       "line_id":"typeI_200bar_bare_reference_vessels",
       "system":"storage_pressure_boundary",
       "item_scope":"Only additional empty published 2.4t EACH Type I reference pressure-vessel equipment, includes UNSPECIFIED shell closures/material split",
       "quantity":net_count,"unit":"reference_vessels",
       "empty_mass_kg":shell_mass,
       "manufacturer_quote_eur":None,
       "source_ref_id":"ijhe_adm_2026_table2",
       "evidence_class":"PEER_REVIEWED_PER_VESSEL_EMPTY_EQUIPMENT_MASS_NOT_OEM_SPEC",
       "system_completeness_status":"PRELIMINARY_SHELL_REFERENCE_ONLY",
       "contribution_to_full_LCI":"NOT_CHARACTERIZED_MATERIAL_GRADE_FABRICATION_UNKNOWN",
       "not_coupled_as_complete_native_BAFU_inventory":True,
       "empty_vessel_reference_per_unit_kg":paper["empty_vessel_mass_kg"],
       "per_unit_reference_internal_volume_m3":paper["internal_volume_m3"],
       "manufacturer_grade_source_verified":False,
       "raw_virgin_steel_mass_kg":None
    }
    return [known]+[_unknown(*r) for r in categories]


def compute_bank(mode,capacity,source):
    v=source["verified_typeI_reference"]
    screen=screen_vessel_bank("I_200bar",capacity,20,313.,capacity_semantics=mode)
    require(screen.source_capacity_semantics==mode and
            screen.original_scenario_capacity_kg==capacity and
            screen.empty_reference_vessels_total_kg==screen.number_of_reference_vessels*v["empty_vessel_mass_kg"] and
            screen.representative_internal_free_volume_total_m3==screen.number_of_reference_vessels*v["internal_volume_m3"],
            "reference vessel shell source mass or gas free-volume mismatch")
    return {
       "reference_vessels":screen.number_of_reference_vessels,
       "paper_reference_25_vessel_racks_ceil":screen.minimum_source_reference_container_count,
       "paper_empty_vessels_total_equipment_kg":screen.empty_reference_vessels_total_kg,
       "bank_internal_gas_free_volume_m3":screen.representative_internal_free_volume_total_m3,
       "actual_gas_max_kg_at_assumed_200bara_313K":screen.gross_hydrogen_at_max_pressure_kg,
       "residual_heel_kg_at_assumed_20bara_313K":screen.residual_heel_hydrogen_at_min_pressure_kg,
       "withdrawable_h2_between_200_and_20_bara_kg":screen.withdrawable_hydrogen_between_pressures_kg,
       "source_model_capacity_kg":capacity,
       "source_capacity_semantics":mode,
       "real_vendor_manufacturer_bom_approved":False
    }


def case_mode(mode,record,source):
    v=source["verified_typeI_reference"]
    e=compute_bank(mode,20000,vessel_source_or_error(source))
    es=compute_bank(mode,40000,vessel_source_or_error(source))
    delta=es["reference_vessels"]-e["reference_vessels"]
    require(delta>0 and delta in (e["reference_vessels"],e["reference_vessels"]-1,e["reference_vessels"]+1),
            "source E to E+S extra vessel count does not approximate 20t doubling")
    delta_shell=delta*v["empty_vessel_mass_kg"]
    rack_count=es["paper_reference_25_vessel_racks_ceil"]-e["paper_reference_25_vessel_racks_ceil"]
    full_rack_extra_positions=rack_count*v["reference_vessels_per_paper_container"]
    # Alternate FULL-25-vessel-rack vs FULL-25-vessel-rack configuration;
    # not a bound on the partial-vessel bank count. Both E and E+S baselines
    # must be fully packed for rack-count-delta*25 to be meaningful. Because
    # the E rack can have unused slots, this delta can be LESS than the
    # incremental bare-cylinder count in the partly filled architecture.
    # Never use it as a physical upper equipment-mass bound or real site plan.
    gross_modules=record["heisertec_cosmos_stationary_2026"]["vendor_example"]
    vendor_water_volume=gross_modules["water_volume_per_cylinder_l"]*gross_modules["cylinders_per_stationary_bundle"]/1000
    d200=hydrogen_density_kg_m3(200.,313.)
    d20=hydrogen_density_kg_m3(20.,313.)
    max_kg=vendor_water_volume*d200
    usable_kg=vendor_water_volume*(d200-d20)
    denom=max_kg if mode=="max_inventory" else usable_kg
    vendor_count_E=math.ceil(20000/denom)
    vendor_count_ES=math.ceil(40000/denom)
    vendor_nominal_rated_49kg_count_E=(math.ceil(20000/gross_modules["reported_hydrogen_gross_kg_at_vendor_nominal_conditions_per_bundle"])
        if mode=="max_inventory" else None)
    vendor_nominal_rated_49kg_count_ES=(math.ceil(40000/gross_modules["reported_hydrogen_gross_kg_at_vendor_nominal_conditions_per_bundle"])
        if mode=="max_inventory" else None)
    per_case={x:load_f3c_case(mode,x) for x in ("E","E_plus_S")}
    require(per_case["E"]["common_hourly_modelled_H2_service_float64_sha256"]==
            per_case["E_plus_S"]["common_hourly_modelled_H2_service_float64_sha256"],
            "historical F3-C source E/ES hourly service hashes differ")
    lines=bom_lines(delta,v,gross_modules)
    require(lines[0]["empty_mass_kg"]==delta_shell and
            all(c["empty_mass_kg"] is None for c in lines[1:]) and
            len(lines)>=18,"unsafe fabricated full plant equipment weight")
    return {
       "capacity_semantics":mode,
       "source_case_E_20t":e,
       "source_case_EplusS_40t":es,
       "incremental_only_research_sensitivity":{
           "net_additional_published_reference_vessel_count":delta,
           "net_additional_published_empty_vessel_equipment_mass_kg":delta_shell,
           "published_reference_25_vessel_rack_addition_count_minimum":rack_count,
           "paper_reference_full_rack_incremental_positions_if_all_filled":full_rack_extra_positions,
           "paper_reference_if_only_extra_full_rack_vessels_mass_kg":full_rack_extra_positions*v["empty_vessel_mass_kg"],
           "paper_reference_rack_frame_and_manifold_mass_kg":None,
           "paper_reference_per_container_area_from_table2_m2":v["reference_footprint_per_paper_container_including_contextual_clearances_m2"],
           "actual_total_site_footprint_m2":None,
           "source_vessel_mass_is_NOT_virgin_steel_input_kg":True,
           "net_additional_source_upper_inventory_kg":20000,
           "extra_hydrogen_working_capacity_due_to_ceiling_kg":es["withdrawable_h2_between_200_and_20_bara_kg"]-e["withdrawable_h2_between_200_and_20_bara_kg"],
           "incremental_heel_gas_stock_kg":es["residual_heel_kg_at_assumed_20bara_313K"]-e["residual_heel_kg_at_assumed_20bara_313K"],
           "incremental_installed_compressor_equipment_mass_kg":None,
           "incremental_cooling_equipment_mass_kg":None,
           "incremental_BOP_material_manufacturing_mass_kg":None,
           "incremental_operational_station_power_MWh_per_year":None,
           "incremental_native_BAFU_storage_CO2e_kg":None,
           "incremental_installed_storage_CAPEX_eur":None
       },
       "commercial_manufacturer_candidate":{
           "OEM":"heiserTEC",
           "supplier_product":"COSMOS Stationary (PED) 210 BAR 36x87L Type I steel bundles",
           "supplier_source_url":"https://www.heisertec.com/products/bundles/",
           "vendor_published_rated_module_gross_H2_kg":49,
           "vendor_210bar_rated_gross_modules_required_for_20t_at_rated_conditions_only":
                   vendor_nominal_rated_49kg_count_E,
           "vendor_210bar_rated_gross_modules_required_for_40t_at_rated_conditions_only":
                   vendor_nominal_rated_49kg_count_ES,
           "stationary_module_internal_free_volume_m3_from_vendor_36x87L":vendor_water_volume,
           "screened_200bara_313K_max_h2_kg_per_stationary_vendor_module":max_kg,
           "screened_200bara_313K_20bara_usable_h2_kg_per_vendor_module":usable_kg,
           "screened_stationary_vendor_module_count_E_if_RATED_200bara_313K_without_approval":vendor_count_E,
           "screened_stationary_vendor_module_count_EplusS_if_RATED_200bara_313K_without_approval":vendor_count_ES,
           "screened_stationary_vendor_incremental_module_count_if_RATED_200bara_313K_without_approval":vendor_count_ES-vendor_count_E,
           "validity_of_using_210bar_vendor_module_as_certified_200bara_313K_installation":False,
           "stationary_module_empty_mass_kg":None,
           "stationary_module_galvanized_frame_mass_kg":None,
           "stationary_manifold_steel_grade_verified":False,
           "mobile_TPED_935kg_reference_may_be_applied_to_stationary_PED":False,
           "vendor_module_AER_inspection_and_CE_document_for_this_site":None,
           "OEM_commercial_bare_module_quote_eur":None,
           "OEM_source_permitted_for_final_lca_comparative_claim":False
       },
       "2023_source_case_operations_not_station_hardware_sizing":{
           case:{
             "source_reconstructed_duty_2023_kg_h_max_charging":float(d["case_modelled_annual_audit"]["max_charge_kg_h"]),
             "source_reconstructed_duty_2023_kg_h_max_discharging":float(d["case_modelled_annual_audit"]["max_discharge_kg_h"]),
             "source_2023_modelled_compressor_electricity_MWh":float(d["case_modelled_annual_audit"]["annual_compression_electricity_mwh"]),
             "source_nominal_max_charge_kg_h":2200.,
             "source_2023_real_vessel_installation_not_approved":True,
             "source_2023_optimized_hourly_H2_service_SHA256":d["common_hourly_modelled_H2_service_float64_sha256"],
           } for case,d in per_case.items()
       },
       "required_incremental_system_foreground_BOM":lines,
       "known_empty_reference_vessel_hardware_only_kg":delta_shell,
       "unknown_non_vessel_equipment_total_mass_kg":None,
       "complete_source_fabrication_and_installed_mass_kg":None,
       "complete_stationary_steel_content_kg":None,
       "complete_manufacturer_warrantied_typeI_bank_BOM":False,
       "BAFU2026_v11_standalone_typeI_native_LCI_created":False,
       "full_LCA_or_utility_production_cost_ready":False,
    }


def vessel_source_or_error(paper_source):
    # Internal type check keeps accidental swapping of commercial OEM mobile
    # catalogue properties into the peer-reviewed reference vessel impossible.
    if (paper_source["verified_typeI_reference"]["internal_volume_m3"]!=1.8 or
        paper_source["verified_typeI_reference"]["empty_vessel_mass_kg"]!=2400):
        raise IncompletePhysicalStation("IJHE Type I source mass/volume mismatch")
    return paper_source


def make_incremental_stationary_bank_duty_and_bom():
    registry,refs=source_register()
    return {
      "schema_version":SCHEMA,"programme":"OEM-PTX-2026-01",
      "modelled_original_PyNEXUS_year":2023,
      "original_model_E_and_EplusS_archives_source_SHA256":{
           "E":SOURCE_E_SHA,"E_plus_S":SOURCE_ES_SHA},
      "report_date":"2026-11-14",
      "source_evidence_refs":{
        "peer_reviewed_200bar_IJHE":refs["ijhe_adm_2026_table2"]["url"],
        "actual_210bar_stationary_PED_product":refs["heisertec_cosmos_stationary_2026"]["url"],
        "EIGA_2024_safety_equipment":refs["eiga_doc247_2024"]["url"],
        "industrial_H2_compressor_family":refs["burckhardt_HME_2026"]["url"],
        "EU_pressure_equipment_directive":refs["EU_PED_2014_68_2026"]["url"]
      },
      "screening_conditions":{"temperature_K":313.,"max_storage_pressure_bar_absolute":200.,
                              "minimum_H2_delivery_pressure_bar_absolute":20.,
                              "rating_reinterpreted_as_absolute_for_screening_only":True,
                              "source_RVO_compressor_stage_electricity_not_actual_motor_rating":True},
      "two_storage_capacity_semantics_not_combined":True,
      "reported_reference_vessel_mass_is_empty_equipment_not_hydrogen_or_raw_steel_input":True,
      "heiserTEC_stationary_PED_vs_mobile_TPED_confusion_rejected":True,
      "no_vendor_site_validated_cylinder_fatigue_P_and_ID_or_BOM":True,
      "full_project_LCA_TE_A_allowed":False,
      "modes":{mode:case_mode(mode,refs,refs["ijhe_adm_2026_table2"])
               for mode in ("max_inventory","usable_service")}
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    opts=p.parse_args()
    result=make_incremental_stationary_bank_duty_and_bom()
    dest=Path(opts.output)
    if dest.exists():raise FileExistsError("do not overwrite source-registered Type I hydrogen bank screen")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    for mode,r in result["modes"].items():
        inc=r["incremental_only_research_sensitivity"]
        print(mode,"extra peer-reviewed reference empty vessel count",inc["net_additional_published_reference_vessel_count"],
              "extra empty equipment mass kg",inc["net_additional_published_empty_vessel_equipment_mass_kg"])
        print("Supplier stationary bundle EMPTY MASS is not published and ALL installed non-vessel equipment mass is missing.")
    print("F2 reference shell-only quantified; complete manufacturer BOM/BAFU/LCOH blocked.")


if __name__=="__main__":
    main()
