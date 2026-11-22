"""Independent real OEM 50L PED 330bar cylinder EMPTY mass sensitivity.

heiserTEC's published hydrogen-product table supplies one actual PED
hydrogen cylinder, 50 L water capacity, 330 bar catalogue working class,
85.5 kg empty weight, EN 1964-1. This is NOT its 210bar 36x87L stationary
COSMOS bundle; the bundle has NO published empty mass. Nor is it the mobile
TPED 935kg 12x50L bundle.

Operating this distinct 330bar product at the earlier 200bar ABS and
313K H2 EOS screen is a deliberately hypothetical "derated" mathematical
capacity comparison, not vendor approval, code certification or guaranteed
availability. No 330bar catalogue condition is silently used as a pressure
gauge/absolute conversion or assumed acceptable fatigue duty.

NEN-EN 17533:2025 directly governs stationary hydrogen cylinders but
expressly does NOT cover manifolded assemblies or external pipework.
All other physical balance-of-plant, compliant alloy/materials, installed
cost, supplier operational contract and native BAFU/GWP are still missing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from .hydrogen_physics import hydrogen_density_kg_m3

ROOT=Path(__file__).resolve().parents[2]
REGISTRY=ROOT/"research/F2_L1_INDEPENDENT_OEM_PED_50L_330BAR_H2_CYLINDER_AND_EN17533_SOURCE_v1.json"
PAPER_BOM=ROOT/"data/results/F2_L1_2023_source_incremental_20t_to_40t_stationary_typeI_200bar_BOM_SCOPE_NOT_complete_native_LCI.json"
SOURCE_SHA="1315d1181b9d1eab6d3368425c9571dbe295c3360935d2972403bf3c60e2dc47"
SCHEMA="ptxflex.f2_l1_independent_heiserTEC_330bar_PED_50L_OEM_mass_at_200bara_screen.v1"


class BadOemEngineeringClaim(ValueError):pass


def require(cond,reason):
    if not cond:raise BadOemEngineeringClaim(reason)


def read_oem():
    r=json.loads(REGISTRY.read_text())
    assert r.get("schema_version")=="oem.ptx.f2_l1_stationary_PED_vessel_independent_OEM_product_source.v1"
    c=r["manufacturer"];n=r["local_standards"];a=r["scientific_analog"]
    require(c["product_service"]=="hydrogen" and
            c["cylinder_water_volume_litre"]==50 and
            c["working_pressure_catalogue_bar"]==330 and
            c["catalogue_test_pressure_bar"]==472 and
            c["catalogue_empty_cylinder_weight_kg"]==85.5 and
            c["pressure_category"]=="PED stationary-compatible cylinder candidate" and
            c["catalogue_pressure_basis_gauge_or_absolute_unspecified"] is True,
            "actual manufacturer H2 PED 50L 330bar 85.5kg weight not independently confirmed")
    for field in ("actual_50L_PED_unit_pressure_cycling_certified_for_20bar_to_200bar_313K_site",
                  "material_alloy_grade_certificate_available",
                  "single_cylinder_mass_is_completed_stationary_module_or_BOP",
                  "manufacturer_has_quoted_200bar_suitable_modular_pack_with_this_50L_330bar_cylinder"):
        require(c[field] is False,"supplier OEM station approval or complete mass fabricated: "+field)
    for field in ("carbon_steel_recycled_content","per_cylinder_sales_price_eur",
                  "per_cylinder_site_footprint_and_rack_GA"):
        require(c[field] is None,"actual vendor material split, price or station layout not verified: "+field)
    require(n["name"]=="NEN-EN 17533:2025" and
            n["explicitly_excludes_manifolded_assemblies"] is True and
            n["explicitly_excludes_external_piping"] is True and
            n["compliance_in_this_study_assessed"] is False and
            n["purchased_or_reproduced_full_standard"] is False,
            "EN17533:2025 scope incorrectly asserted to certify plant gas headers")
    require(a["selected_reference_pressure_max_bar_absolute_for_comparison"]==200 and
            a["selected_minimum_delivery_bar_absolute"]==20 and
            a["selected_reference_isothermal_K"]==313 and
            a["OEM_product_is_330bar_CLASS_but_only_USED_TO_CALCULATE_hypothetical_200bara_313K_H2_density"] is True and
            a["retrospective_2023_original_product_field_data"] is False,
            "manufacturer 330bar pressure falsely substituted into source F3 200bar 2023")
    require(r["existing_record"]["source_F2_typeI_200bar_research_BOM_SHA256"]==SOURCE_SHA and
            r["system_complete_manufacturer_BOM_available"] is False and
            r["full_GWP100_or_lifetime_Cost_possible"] is False,
            "reference source BOM mismatched or prematurely released for LCIA")
    raw=PAPER_BOM.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==SOURCE_SHA,"upstream 200bar peer-reviewed Type I reference BOM SHA changed")
    paper=json.loads(raw)
    require(paper["full_project_LCA_TE_A_allowed"] is False and
            paper["heiserTEC_stationary_PED_vs_mobile_TPED_confusion_rejected"] is True,
            "paper Type I and OEM stationary study evidence mismatch")
    return r,paper


def compare_hydrogen_working_mass(r,paper):
    c=r["manufacturer"]
    volume=c["cylinder_water_volume_litre"]/1000.
    maximum=volume*hydrogen_density_kg_m3(200.,313.)
    heel=volume*hydrogen_density_kg_m3(20.,313.)
    withdrawable=maximum-heel
    require(0<heel<maximum and withdrawable>0,"zero or invalid actual real-gas pressure density")
    result={}
    for mode in ("max_inventory","usable_service"):
        denom=maximum if mode=="max_inventory" else withdrawable
        nE=math.ceil(20000/denom)
        nES=math.ceil(40000/denom)
        extra=nES-nE
        require(extra>0 and extra*85.5>20000,"single 50L Type I steel cylinder reference mass/hydrogen confusion")
        p=paper["modes"][mode]
        result[mode]={
           "source_2023_h2_service_capacity_semantics":mode,
           "hypothetical_200bar_abs_313K_H2_max_mass_per_50L_cylinder_kg":maximum,
           "hypothetical_20bar_abs_313K_H2_unrecoverable_heel_per_50L_kg":heel,
           "hypothetical_200bar_to_20bar_abs_313K_withdrawable_H2_per_50L_kg":withdrawable,
           "actual_heiserTEC_330bar_Ped_50L_product_PUBLISHED_empty_mass_kg_each":85.5,
           "hypothetical_200bara_E20t_cylinder_count":nE,
           "hypothetical_200bara_EplusS40t_cylinder_count":nES,
           "hypothetical_extra_cylinders_count":extra,
           "hypothetical_extra_OEM_empty_cylinder_hardware_mass_kg":extra*85.5,
           "reference_IJHE200bar_extra_larger_vessel_count":p["incremental_only_research_sensitivity"]["net_additional_published_reference_vessel_count"],
           "reference_IJHE200bar_extra_larger_vessel_mass_kg":p["incremental_only_research_sensitivity"]["net_additional_published_empty_vessel_equipment_mass_kg"],
           "both_source_candidates_different_cylinder_dimensions_rated_pressure_not_identical_products":True,
           "mobile_TPED_935kg_empty_complete_bundle_weight_used_here":False,
           "vendor_module_frame_manifold_valves_fabrication_mass_kg":None,
           "manufacturer_grade_and_H2_fatigue_conformity_for_actual_200bar_313K_duty":None,
           "actual_installed_2023_site_equipment_exist":False,
           "native_BAFU2026_v1_1_typeI_compatible_manufacturing_GWP_kgCO2e":None,
           "full_tank_inc_CAPEX_EUR":None,
           "actual_completed_manufacturer_BOM":False
        }
    return {
        "schema_version":SCHEMA,
        "experiment":"distinct real OEM published 330bar PED 50L empty steel cylinder weight; conservatively screen gas mass at 200bar(a) and 313K using independent H2 EOS, NOT vendor engineering release",
        "manufacturer_product_url":c["source_url"],
        "manufacturer_source_product_location":c["source_locator"],
        "local_applicable_standard_name":r["local_standards"]["name"],
        "local_applicable_standard_source":r["local_standards"]["url"],
        "standard_for_individual_cylinders_not_manifolded_assemblies":True,
        "original_200bar_paper_F2_source_SHA256":SOURCE_SHA,
        "source_2023_PyNEXUS_project_not_actual_heiserTEC_installation":True,
        "manufacturer_oem_product_330bar_nominal_pressure_not_same_as_200bar_screen":True,
        "OEM_product_working_pressure_basis_gauge_absolute_unverified":True,
        "manufacturer_50L_85_5kg_is_H2_pressure_cylinder_not_mobile_module_frame":True,
        "no_vendor_DCF_LCA_or_PandID_signoff":True,
        "whole_plant_comparison_release_ready":False,
        "modeled_source_inventory_modes":result,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    args=p.parse_args()
    dest=Path(args.output)
    if dest.exists():raise FileExistsError("do not overwrite OEM original source-based sensitivity")
    doc,paper=read_oem()
    obj=compare_hydrogen_working_mass(doc,paper)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    for mode,x in obj["modeled_source_inventory_modes"].items():
        print(mode,"source 330bar-rated 50L PED manufacturer cylinder, operated only hypothetically at 200bar(a) /313K",
              "extra cylinders",x["hypothetical_extra_cylinders_count"],
              "extra nominal empty cylinder hardware kg",x["hypothetical_extra_OEM_empty_cylinder_hardware_mass_kg"])
    print("Manufacturer frame/valves/steel composition/PED site approval missing; no price, BAFU-LCA, DCF or 2023 actual plant.")
if __name__=="__main__":main()
