"""L3-F: exogenous H30 stationary Type I pressure/thermal free-volume study.

Independent published F2 reference: original 2023 max_inventory +20,000 kg
*maximum inventory* delta, NOT an extra 20,000 kg withdrawable, 17,784.92485
kg pressure-swing working reference, 802 source-reference cylinders with 1.8 m3
INTERNAL free volume and 2400 kg EMPTY equipment each. No vendor certification.

Use CoolProp real-gas hydrogen EOS to calculate:
- volume needed to contain +20,000 kg at assumed hot filled 200 bar(a);
- volume needed for 17,784.92485 kg conservative *endpoint* withdrawal,
  from 200bar(a) hot fill to 20bar(a) cold heel;
- discrete paper cylinder positions for BOTH distinct requirements, forward
  EOS sanity check of rounded-up counts, and comparative reference quantity.

This is strictly screening; actual installed geometry, P&ID, bank isolation,
fatigue cycles, temperature history, flows, compressor operating envelope,
pressure losses, relief, real grid, OEM installed cost and PED qualification
are not certified. The hot and cold EOS endpoints are NOT a transient.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

from .f2l3e_exogenous_vendor_cost_intake import original, sha1blob, SOURCE, SOURCE_GIT_BLOB
from .f2_thermal_working_capacity import screen_thermal_working_capacity, ThermalCapacityError
from .f2_required_free_volume import solve_required_free_volume

ROOT=Path(__file__).resolve().parents[2]
SCHEMA="ptxflex.l3f_stationary_typeI_h30_max_inventory_thermal_endpoint_volume_screen.v1"
OUT_JSON="L3F_H30_TYPEI_REFERENCE_20t_INCREMENTAL_FREE_VOLUME_THERMAL_DISCRETE_SCREEN_NOT_OEM_v1.json"
OUT_MD="L3F_H30_TYPEI_REFERENCE_THERMAL_PRESSURE_DESIGN_SCOPE_NOT_OEM_v1.md"
SOURCE_MODE="max_inventory"
REQUIRED_ORIGINAL_DELTA_MAX_KG=20000.
REFERENCE_ORIGINAL_WORKING_KG=17784.924849614785
REFERENCE_PAPER_COUNT=802
REFERENCE_PAPER_VESSEL_FREE_VOLUME_M3=1.8
REFERENCE_PAPER_VESSEL_EMPTY_EQUIPMENT_KG=2400.
MAX_BAR_ABS=200.
HEEL_BAR_ABS=20.
REFERENCE_K=313.
THERMAL_STATES=(
    ("reference_isothermal_313K",313.,313.),
    ("hypothetical_moderate_303K_323K",303.,323.),
    ("hypothetical_wide_293K_333K",293.,333.),
)


class L3FQualificationError(ValueError):
    pass


def need(ok,why):
    if not ok:
        raise L3FQualificationError("L3-F pressure/thermal screen: "+why)


def finite_pos(x,label):
    need(type(x) in (int,float) and math.isfinite(x) and x>0,
         label+" must be positive finite, not bool, zero, or missing")
    return float(x)


def source_reference():
    # Verify original source F2 evidence and get all its original quantities.
    lines=original()
    raw=SOURCE.read_bytes()
    need(sha1blob(raw)==SOURCE_GIT_BLOB,
         "published F2 source Git blob mismatch")
    d=json.loads(raw.decode("utf-8"))
    b=d["modes"][SOURCE_MODE]
    s=b["incremental_only_research_sensitivity"]
    v=lines[0]
    need(v["line_id"]=="typeI_200bar_bare_reference_vessels" and
         v["quantity"]==REFERENCE_PAPER_COUNT and
         v["per_unit_reference_internal_volume_m3"]==REFERENCE_PAPER_VESSEL_FREE_VOLUME_M3 and
         v["empty_vessel_reference_per_unit_kg"]==REFERENCE_PAPER_VESSEL_EMPTY_EQUIPMENT_KG and
         s["net_additional_source_upper_inventory_kg"]==REQUIRED_ORIGINAL_DELTA_MAX_KG and
         s["extra_hydrogen_working_capacity_due_to_ceiling_kg"]==REFERENCE_ORIGINAL_WORKING_KG and
         s["net_additional_published_reference_vessel_count"]==REFERENCE_PAPER_COUNT and
         s["net_additional_published_empty_vessel_equipment_mass_kg"]==
         REFERENCE_PAPER_COUNT*REFERENCE_PAPER_VESSEL_EMPTY_EQUIPMENT_KG and
         s["source_vessel_mass_is_NOT_virgin_steel_input_kg"] is True and
         d["screening_conditions"]["max_storage_pressure_bar_absolute"]==MAX_BAR_ABS and
         d["screening_conditions"]["minimum_H2_delivery_pressure_bar_absolute"]==HEEL_BAR_ABS and
         d["screening_conditions"]["temperature_K"]==REFERENCE_K,
         "original gross H2 vs usable H2, source vessel size or thermal reference changed")
    need(len(lines)==19,"original equipment scope no longer 19 lines")
    return {
        "original_F2_source_git_blob_sha1":SOURCE_GIT_BLOB,
        "capacity_semantics":SOURCE_MODE,
        "extra_gross_H2_at_maximum_kg":REQUIRED_ORIGINAL_DELTA_MAX_KG,
        "original_pressure_swing_extra_withdrawable_H2_kg":REFERENCE_ORIGINAL_WORKING_KG,
        "published_extra_empty_reference_vessel_positions":REFERENCE_PAPER_COUNT,
        "published_reference_one_vessel_internal_FREE_volume_m3":
            REFERENCE_PAPER_VESSEL_FREE_VOLUME_M3,
        "published_empty_equipment_mass_PER_paper_vessel_kg":
            REFERENCE_PAPER_VESSEL_EMPTY_EQUIPMENT_KG,
        "published_original_empty_equipment_mass_kg":
            REFERENCE_PAPER_COUNT*REFERENCE_PAPER_VESSEL_EMPTY_EQUIPMENT_KG,
        "original_19_component_scope_ids":[r["line_id"] for r in lines],
        "reference_vessel_is_not_supplier_certified":True,
    }


def screen_one(*, max_inventory_kg, usable_kg,
               vessel_free_volume_m3, maximum_pressure_bar_absolute,
               withdrawal_heel_bar_absolute, reference_temperature_k,
               cold_temperature_k, hot_temperature_k):
    gross=finite_pos(max_inventory_kg,"incremental nominal max H2")
    working=finite_pos(usable_kg,"incremental usable H2")
    vessel=finite_pos(vessel_free_volume_m3,"paper vessel internal free volume")
    max_p=finite_pos(maximum_pressure_bar_absolute,"max pressure abs")
    min_p=finite_pos(withdrawal_heel_bar_absolute,"heel pressure abs")
    ref=finite_pos(reference_temperature_k,"reference temperature K")
    cold=finite_pos(cold_temperature_k,"cold endpoint K")
    hot=finite_pos(hot_temperature_k,"hot endpoint K")
    need(min_p<max_p and cold<=ref<=hot,
         "absolute pressure order or temperature envelope invalid")
    # One cubic metre real-gas forward calculation supplies hot-fill density.
    unit=screen_thermal_working_capacity(
        free_volume_m3=1.,
        maximum_pressure_bar_absolute=max_p,
        minimum_withdrawal_pressure_bar_absolute=min_p,
        reference_temperature_k=ref,
        cold_temperature_k=cold,
        hot_temperature_k=hot,
    )
    usable_volume=solve_required_free_volume(
        target_usable_kg=working,
        maximum_pressure_bar_absolute=max_p,
        minimum_withdrawal_pressure_bar_absolute=min_p,
        reference_temperature_k=ref,
        cold_temperature_k=cold,
        hot_temperature_k=hot,
    ).required_free_volume_m3
    gross_volume=gross/unit.hot_fill_gross_kg
    req_volume=max(gross_volume,usable_volume)
    count=max(1,math.ceil(req_volume/vessel-1e-12))
    rounded_volume=count*vessel
    verify=screen_thermal_working_capacity(
        free_volume_m3=rounded_volume,
        maximum_pressure_bar_absolute=max_p,
        minimum_withdrawal_pressure_bar_absolute=min_p,
        reference_temperature_k=ref,
        cold_temperature_k=cold,
        hot_temperature_k=hot,
    )
    need(verify.hot_fill_gross_kg+1e-7>=gross and
         verify.conservative_usable_kg+1e-7>=working,
         "rounded vessel positions fail one of two independent targets")
    # A single fewer paper vessel MUST fail at least one target.
    if count>1:
        prior=(count-1)*vessel
        check=screen_thermal_working_capacity(
            free_volume_m3=prior,
            maximum_pressure_bar_absolute=max_p,
            minimum_withdrawal_pressure_bar_absolute=min_p,
            reference_temperature_k=ref,
            cold_temperature_k=cold,
            hot_temperature_k=hot,
        )
        need(check.hot_fill_gross_kg<gross+1e-7 or
             check.conservative_usable_kg<working+1e-7,
             "rounded paper count is not minimal")
    return {
        "hot_fill_temperature_K":hot,
        "cold_withdrawal_temperature_K":cold,
        "reference_temperature_K":ref,
        "maximum_pressure_bar_absolute":max_p,
        "minimum_withdrawal_pressure_bar_absolute":min_p,
        "distinct_incremental_MAX_inventory_target_kg":gross,
        "distinct_incremental_withdrawable_working_target_kg":working,
        "per_m3_hot_fill_gross_H2_kg":unit.hot_fill_gross_kg,
        "per_m3_conservative_working_H2_kg":unit.conservative_usable_kg,
        "required_FREE_volume_for_MAX_inventory_m3":gross_volume,
        "required_FREE_volume_for_WORKING_service_m3":usable_volume,
        "required_FREE_volume_for_BOTH_m3":req_volume,
        "paper_assumed_cylinder_INTERNAL_volume_m3":vessel,
        "mathematical_minimum_discrete_paper_positions_for_BOTH":count,
        "extra_paper_positions_vs_original_F2_802_REFERENCE_ONLY":count-802,
        "rounded_paper_FREE_volume_m3":rounded_volume,
        "independently_forward_EOS_hot_gross_kg":verify.hot_fill_gross_kg,
        "independently_forward_EOS_conservative_working_kg":verify.conservative_usable_kg,
        "actual_OEM_vessel_count":None,
        "actual_INSTALLED_steel_mass_kg":None,
        "actual_site_footprint_m2":None,
        "actual_compressor_and_BOP_ratings":None,
        "satisfies_a_certified_hourly_service_profile":False,
        "pressure_design_certified_under_EU_PED":False,
        "real_temperature_distribution_measured":False,
        "endpoints_not_dynamic_or_adiabatic_trajectory":True,
        "this_is_NOT_manufacturer_bill_of_materials_or_virgin_steel_kg":True,
    }


def build():
    ref=source_reference()
    states=[]
    for name,cold,hot in THERMAL_STATES:
        v=screen_one(
            max_inventory_kg=ref["extra_gross_H2_at_maximum_kg"],
            usable_kg=ref["original_pressure_swing_extra_withdrawable_H2_kg"],
            vessel_free_volume_m3=ref["published_reference_one_vessel_internal_FREE_volume_m3"],
            maximum_pressure_bar_absolute=MAX_BAR_ABS,
            withdrawal_heel_bar_absolute=HEEL_BAR_ABS,
            reference_temperature_k=REFERENCE_K,
            cold_temperature_k=cold,hot_temperature_k=hot,
        )
        states.append({"scenario":name,"engineering_temperature_bounds_measured":False,**v})
    need(len(states)==3 and
         states[0]["mathematical_minimum_discrete_paper_positions_for_BOTH"]>=1 and
         states[2]["required_FREE_volume_for_BOTH_m3"]>=states[1]["required_FREE_volume_for_BOTH_m3"]>=states[0]["required_FREE_volume_for_BOTH_m3"],
         "thermal engineering sensitivity ordering changed")
    return {
        "schema_version":SCHEMA,
        "origin":ref,
        "functional_unit":"2022 and 2024 source-year E20t/EplusS40t same 30t/day H2; here paper bank sizing only",
        "original_study_2022_2024_source_h2_per_hour_kg":1250.,
        "interpretation_gross_inventory_vs_withdrawable_usable_separated":True,
        "thermal_endpoints_are_hypothetical":True,
        "input_pressure_unit":"bar absolute, NOT PED gauge-pressure rating",
        "PED_2014_68_EU_stationary_conformity_required":True,
        "EIGA_DOC15_and_DOC247_H2_installation_review_required":True,
        "OEM_qualified_specific_station":False,
        "actual_site_design_temperature_bounds":None,
        "dynamic_pressure_losses_and_flow_performance":None,
        "real_helium_hydrogen_leak_test_and_hazard_design":None,
        "native_BAFU_2026_v11_manufacturing_inventory":None,
        "installed_incremental_CAPEX_eur":None,
        "scenarios":states,
    }


def markdown(d):
    lines=[
        "# L3-F: stationary Type I original 20t→40t H2 reference sizing, NOT OEM qualification",
        "",
        "Original max_inventory extension has DISTINCT source F2 gross **20,000kg** "
        "and pressure-swing withdrawable **17,784.925kg** at the original 313K "
        "screening reference. Never re-label maximum bank gas inventory as "
        "withdrawable H2.",
        "",
        "These are only hypothetical Hot-fill 200bar absolute / Cold-heel 20bar "
        "absolute endpoint EQ states using real-gas CoolProp; they do not "
        "represent plant temperature observations or certified manufacturer "
        "gas/vessel pressure limits.",
        "",
        "| Non-certified temperature envelope | Free volume for BOTH (m3) | "
        "Discrete 1.8m3 paper positions | Delta from original 802 paper |",
        "|---|---:|---:|---:|",
    ]
    for c in d["scenarios"]:
        lines.append(f"| {c['scenario']} | "
                     f"{c['required_FREE_volume_for_BOTH_m3']:,.2f} | "
                     f"{c['mathematical_minimum_discrete_paper_positions_for_BOTH']:,} | "
                     f"{c['extra_paper_positions_vs_original_F2_802_REFERENCE_ONLY']:+,} |")
    lines.extend([
        "",
        "The 802 × 2400kg = 1,924,800kg original paper reference is EMPTY "
        "equipment mass, NOT a manufacturer-verified 2022/2024 vessel quantity, "
        "installed bank mass, virgin steel or BAFU raw input quantity.",
        "",
        "Before physical release: genuine PED conformity assessment and "
        "design pressure/gauge-vs-absolute verification; site-specific "
        "thermal envelope and pressure drops; cycle/fatigue, relief, ESD, "
        "vent and hazard analysis; complete P&ID, compressor and "
        "cooling duty, actual vessel internal volume and product BOM, "
        "supplier quotes, commissioning/inspection and lifecycle native "
        "BAFU process mapping. None are established here.",
        "",
    ])
    return "\n".join(lines)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",type=Path,default=ROOT/"data/results")
    a=p.parse_args(argv)
    out=Path(a.output_dir)
    need(out.is_dir() and not out.is_symlink(),"expected public research output dir")
    doc=build()
    files=[
        (out/OUT_JSON,json.dumps(doc,sort_keys=True,indent=2,allow_nan=False)+"\n"),
        (out/OUT_MD,markdown(doc)),
    ]
    for path,body in files:
        need(not path.is_symlink() and
             (not path.exists() or
              (path.is_file() and path.read_text(encoding="utf-8")==body)),
             "immutable thermal screening result differs; no overwrite")
    for path,body in files:
        if not path.exists():
            with path.open("x",encoding="utf-8",newline="\n") as f:
                f.write(body)
    print("L3F_TYPEI_H30_20t_INCREMENT_GROSS_VS_USABLE_THERMAL_ENDPOINT_PHYSICS_COMPLETE",
          "paper positions only; OEM and PED NOT certified; supplier volume and pressure duty UNKNOWN")


if __name__=="__main__":
    main()
