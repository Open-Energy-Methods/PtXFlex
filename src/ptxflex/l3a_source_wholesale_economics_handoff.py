"""PtXFlex L3-A independent source handoff: ONLY 2023 F3-C net WHOLESALE savings.

Mirrors the identical source fingerprints and strictly separates historical
original E/E+S physically screened equal-hourly operating certificate from
prospective real EUR future CAPEX/OPEX modelling performed in PtXLens.
No 2023 market price scenario is claimed future-realizable; no storage OEM
installation exists. This module intentionally DOES NOT perform full-plant
DCF or actual vendor-economic assessment in PtXFlex.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"research/L3_A_2023_source_locked_incremental_wholesale_DCF_handoff_v1.json"
F3C=ROOT/"data/results/F3_C_2023_source_real_gas_equal_H2_hour_E_vs_ES_Lens_operational_bridge.json"
F2=ROOT/"data/results/F2_L1_2023_source_incremental_20t_to_40t_stationary_typeI_200bar_BOM_SCOPE_NOT_complete_native_LCI.json"
F3C_SHA="dddd07d5c0a3d4f276e80af44e28cf3cfdbc93421107fb5d9e39843a0d1d90e2"
F2_SHA="1315d1181b9d1eab6d3368425c9571dbe295c3360935d2972403bf3c60e2dc47"
SOURCE_MODE_HASHES={
  "max_inventory":"8e0d55994c7fe5f1abd952771a1b169336893d12698147fb3a93cb61a4ee7a16",
  "usable_service":"6a30baf00ddb065cd906dedd711db7cbf67504c50b4fda5809c5dfd29b23fa87",
}
SCHEMA="ptxflex.l3a_2023_8760hour_e_vs_es_real_eur_wholesale_annual_evidence_handoff.v1"


class UnsupportedFutureCostClaim(ValueError):pass


def req(ok,msg):
    if not ok:raise UnsupportedFutureCostClaim(msg)


def _load_sha(path,digest):
    raw=Path(path).read_bytes()
    req(hashlib.sha256(raw).hexdigest()==digest,"source-2023 E/ES matched H2 operation or physical equipment source SHA changed")
    return json.loads(raw)


def make_handoff():
    manifest=json.loads(MANIFEST.read_text())
    req(manifest.get("schema_version")=="oem.ptx.l3a_2023_physical_hourly_service_wholesale_savings_handoff.v1"
        and manifest.get("f3c_sha256")==F3C_SHA and
        manifest.get("f2_typeI_bom_sha256")==F2_SHA and
        manifest.get("strict_modes")==["max_inventory","usable_service"] and
        manifest.get("source_research_release_full_v1_allowed") is False and
        manifest.get("not_qualified_claims") and
        all(x is False for x in manifest["not_qualified_claims"].values()),
        "L3-A programme cannot misrepresent wholesale-only 2023 historical source as full LCOH or vendor costs")
    operating=_load_sha(F3C,F3C_SHA)
    hardware=_load_sha(F2,F2_SHA)
    req(operating["source_year"]==2023 and
        operating["source_2023_weather_observations_and_NL_A44_original_matched"] is True and
        operating["two_capacity_interpretations_are_distinct_experiments_not_cross_comparable"] is True and
        operating["l1_l2_l3_v1_0_RELEASE_PASSED"] is False and
        hardware["full_project_LCA_TE_A_allowed"] is False,
        "2023 original-source model/physical system eligibility incorrectly promoted")
    result={}
    for mode,hashval in SOURCE_MODE_HASHES.items():
        o=operating["modes"][mode];b=hardware["modes"][mode]
        req(o["reference_common_hourly_H2_float64_sha256"]==hashval and
            o["operational_saving_can_be_compared_within_mode_not_across_modes"] is True and
            o["original_full_demand_kg"]==18250000 and
            o["actual_economic_preference_or_full_plant_LCA_claim_permitted"] is False and
            b["capacity_semantics"]==mode and
            b["complete_manufacturer_warrantied_typeI_bank_BOM"] is False,
            "source 2023 F3C same-hour H2/20t vs40t interpretation changed")
        v=o["EplusS_2023_wholesale_saving_eur"]
        lo,hi=o["EplusS_saving_interval_mip_bounds_eur"]
        req(all(math.isfinite(n) for n in (v,lo,hi)) and
            0<lo<=v<=hi and hi-lo<100,
            "source solver optimum bounds not permitted as a hardware cost forecast")
        inc=b["incremental_only_research_sensitivity"]
        req(inc["incremental_installed_storage_CAPEX_eur"] is None and
            inc["incremental_native_BAFU_storage_CO2e_kg"] is None and
            inc["source_vessel_mass_is_NOT_virgin_steel_input_kg"] is True,
            "steel/reference shell mass cannot become 2023 installed cash cost")
        count=inc["net_additional_published_reference_vessel_count"]
        mass=inc["net_additional_published_empty_vessel_equipment_mass_kg"]
        req(count>0 and mass==count*2400 and count==
            (802 if mode=="max_inventory" else 902),
            "source pressure swing empty vessel hardware count inconsistent")
        result[mode]={
          "registered_source_mode":mode,
          "source_original_year":2023,
          "original_E_modelled_feasible_not_maximum_same_hourly_H2_hash":hashval,
          "same_hourly_reduced_modelled_H2_kg_year":o["reference_common_annual_modelled_service_kg"],
          "unserved_original_full_H2_contract_kg_year":o["remaining_unserved_original_full_contract_kg"],
          "2023_wholesale_only_annual_saving_eur":v,
          "source_solver_proved_annual_wholesale_saving_bounds_eur":[lo,hi],
          "source_2023_wholesale_difference_is_NOT_2026_future_revenue_forecast":True,
          "source_literature_extra_empty_typeI_200bar_vessel_count":count,
          "source_literature_extra_empty_typeI_200bar_vessel_equipment_mass_kg":mass,
          "vendor_installed_actual_INCREMENTAL_CAPEX_eur":None,
          "true_extra_annual_OPEX_and_maintenance_eur":None,
          "verified_future_site_market_prices_forecast":None,
          "approved_full_source_steel_PandID_BAUF_LCIA":None,
          "source_cross_repo_input_hand_off_ONLY":True
        }
    return {
      "schema_version":SCHEMA,
      "programme":"OEM-PTX-2026-01",
      "source_registered_F3C_2023_original_sha256":F3C_SHA,
      "source_registered_F2_200bar_313K_empty_shell_sha256":F2_SHA,
      "model_hydrogen_data_year":2023,
      "true_plant_vendor_financial_result_or_full_LCOH_permitted":False,
      "distinct_source_capacity_interpretations":result
    }
