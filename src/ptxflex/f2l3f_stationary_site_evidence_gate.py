"""L3-F station engineering qualification/evidence release contract.

This is an offline evidence register, NOT a hydrogen pressure-vessel code,
not an equipment procurement approval, not a released P&ID. A supplier PDF
hash alone is not a signed certificate or technical verification.

Uses original published F2 19-row source requirements and separately computed
thermal endpoint volume screen. The original 200 bar ABSOLUTE model limit is
not a PED certified gauge pressure MAWP; site altitude/ambient barometer,
manufacturer design/test gauge pressures and temperature need separate proof.

Do not reuse the 2023 source dispatch peak charging/discharging duties as
2022/2024 measured or certified compressor/vent/pipe sizing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

from .f2l3e_exogenous_vendor_cost_intake import original, SOURCE_GIT_BLOB, make
from .f2l3f_stationary_thermal_qualification import (
    source_reference, SCHEMA as THERMAL_SCHEMA, ROOT
)

SCHEMA="ptxflex.l3f_h30_stationary_typeI_P_and_ID_PED_site_and_OEM_qualification_contract.v1"
OUT_JSON="L3F_H30_TYPEI_20t_40t_SITE_PED_P_AND_ID_OEM_QUALIFICATION_REQUIREMENTS_NOT_APPROVED_v1.json"
OUT_MD="L3F_H30_SITE_DESIGN_AND_MANUFACTURER_EVIDENCE_GAPS_NOT_APPROVED_v1.md"
HEX_SHA=re.compile(r"^[a-fA-F0-9]{64}$")
DOMAINS=(
    ("pressure_basis","absolute_vs_gauge_design_pressure_and_MAWP"),
    ("temperature","site_temperature_max_min_transients"),
    ("hydrogen_service","30t_day_offtake_purity_and_actual_peak_charge_withdraw"),
    ("mechanical_integrity","H2_materials_fatigue_life_corrosion_protection"),
    ("pressure_containment","stationary_PED_conformity_and_test_reports"),
    ("compressor","recycle_turndown_map_sealing_and_motor_duty"),
    ("cooling","interstage_thermal_load_and_auxiliary_pumps"),
    ("pipework","hydrogen_grade_connections_pressure_drop"),
    ("safety","relief_ESD_detection_ATEX_vent_dispersion_and_HAZOP"),
    ("installation","site_layout_separation_distances_civil_access"),
    ("operations","inspections_replacements_maintenance_and_warranty"),
    ("commercial","signed_vendor_quote_site_terms_scope_and_date"),
    ("environmental","verified_material_manufacture_BAFU_v11_mapping"),
)


class L3FDocumentaryGateError(ValueError):
    pass


def need(ok,message):
    if not ok:
        raise L3FDocumentaryGateError("L3-F station qualification: "+message)


def make_contract():
    src=source_reference()
    old=original()
    intake=make()
    rows=intake["nineteen_required_supplier_and_site_intake_lines"]
    need(len(old)==19 and len(rows)==19 and
         [x["line_id"] for x in old]==[x["line_id"] for x in rows],
         "source physical 19-line and supplier quotation scopes diverge")
    elements=[]
    for x,record in zip(old,rows):
        elements.append({
            "line_id":x["line_id"],
            "source_F2_requirement":x["item_scope"],
            "source_source_reference_id":x["source_ref_id"],
            "economic_cost_role":record["cost_role"],
            "site_specific_specification_revision":None,
            "manufacturer_selected_model_id":None,
            "actual_qualified_installed_quantity":None,
            "actual_site_component_equipment_mass_kg":None,
            "supplier_original_signed_document_sha256":None,
            "supplier_provenance_independently_verified":False,
            "pressure_and_hydrogen_service_conformity_assessed":False,
            "verified_installed_cost_savings_comparability":False,
            "BAFU_manufacturing_materials_specified":False,
        })
    requirements=[]
    for domain,task in DOMAINS:
        requirements.append({
            "domain":domain,
            "necessary_engineering_release_task":task,
            "site_specific_document_revision":None,
            "original_signed_engineering_record_sha256":None,
            "original_verified_manufacturer_attestation_sha256":None,
            "qualified_engineer_independent_review_receipt_sha256":None,
            "project_and_design_basis_concordance_reviewed":False,
            "actual_site_station_PED_design_released":False,
        })
    return {
        "schema_version":SCHEMA,
        "original_published_2023_F2_TypeI_19item_Git_blob_sha1":SOURCE_GIT_BLOB,
        "model_hydrogen_2022_2024_daily_H30_tonnes":30.,
        "original_F2_extra_gross_H2_max_inventory_kg":src["extra_gross_H2_at_maximum_kg"],
        "original_F2_extra_pressure_swing_usable_H2_kg":
            src["original_pressure_swing_extra_withdrawable_H2_kg"],
        "storage_cap_semantics":"max_inventory",
        "model_pressure_high_BAR_ABSOLUTE_NOT_automatic_PED_gauge_MAWP":200.,
        "model_withdrawal_heel_BAR_ABSOLUTE_not_customer_relieving_pressure":20.,
        "actual_local_atmospheric_pressure_bar":None,
        "actual_OEM_allowable_gauge_pressure_MAWP_bar_gauge":None,
        "actual_site_P_and_ID_and_compressor_certified":False,
        "selected_thermal_scenario_is_actual_site_envelope":False,
        "actual_2022_2024_full_hourly_peak_compressor_charging_flow_kg_h":None,
        "actual_2022_2024_full_hourly_peak_hydrogen_withdrawal_flow_kg_h":None,
        "actual_manufacturer_signed_quotation_and_currency_year":None,
        "actual_installed_incremental_economics_comparable_to_2022_or_2024_EUR":
            False,
        "actual_original_native_BAFU_2026_v11_process_flow_linked_LCIA":False,
        "published_802_paper_vessels_NOT_qualified_installed_count":True,
        "H2_codes_and_regulations_source_urls":[
            "https://single-market-economy.ec.europa.eu/sectors/pressure-equipment-and-gas-appliances/pressure-equipment-sector/pressure-equipment-directive_en",
            "https://www.eiga.eu/uploads/documents/DOC015.pdf",
            "https://www.eiga.eu/uploads/documents/DOC247.pdf",
        ],
        "engineering_domains_to_review":requirements,
        "original_19_equipment_qualification_lines":elements,
        "site_pressure_design_engineering_qualified":False,
        "site_operator_reliability_guaranteed":False,
        "OEM_and_supplier_all_in_installed_cost_admitted":False,
        "whole_site_environmental_or_industrial_certification_passed":False,
    }


def review_candidate_metadata(candidate):
    """Strict structural documentary audit; cannot certify the station.

    Document SHA and a checked boolean are insufficient to authenticate OEM
    signatures, assess PED legal category, or validate fatigue/HAZOP or LCIA.
    """
    base=make_contract()
    need(type(candidate) is dict and candidate.get("schema_version")==SCHEMA and
         candidate.get("storage_cap_semantics")=="max_inventory" and
         candidate.get("original_published_2023_F2_TypeI_19item_Git_blob_sha1")==
         SOURCE_GIT_BLOB,
         "source or storage capacity semantics changed")
    domains=candidate.get("engineering_domains_to_review")
    items=candidate.get("original_19_equipment_qualification_lines")
    need(type(domains) is list and type(items) is list and
         [x.get("domain") for x in domains]==[x["domain"] for x in base["engineering_domains_to_review"]] and
         [x.get("line_id") for x in items]==[x["line_id"] for x in base["original_19_equipment_qualification_lines"]],
         "source enumerated site design requirements missing/misaligned")
    unverified=[]
    invalid=[]
    def valid_digest(x):
        return type(x) is str and HEX_SHA.fullmatch(x) is not None
    for row in domains:
        name=row["domain"]
        digest_keys=("original_signed_engineering_record_sha256",
                     "original_verified_manufacturer_attestation_sha256",
                     "qualified_engineer_independent_review_receipt_sha256")
        if not all(valid_digest(row.get(k)) for k in digest_keys):
            unverified.append(name)
        if row.get("project_and_design_basis_concordance_reviewed") is True and name in unverified:
            invalid.append(name+":self_certification_without_verified_document_bytes")
    for row in items:
        if (row.get("actual_qualified_installed_quantity") is not None and
            not valid_digest(row.get("supplier_original_signed_document_sha256"))):
            invalid.append(row["line_id"]+":physical_quantity_without_signed_source")
        if row.get("BAFU_manufacturing_materials_specified") is True and
           row.get("actual_site_component_equipment_mass_kg") is None:
            invalid.append(row["line_id"]+":native_lci_claim_without_source_material_mass")
    return {
        "schema_version":"ptxflex.l3f_documentary_structure_review_NOT_PED_approval.v1",
        "original_13_documentary_domains":len(domains),
        "original_equipment_requirement_categories":len(items),
        "unverified_or_missing_documentary_domains":unverified,
        "internally_contradictory_evidence_claims":invalid,
        "authenticated_external_OEM_P_and_ID_and_PED_classification":False,
        "physical_hydrogen_station_approved":False,
        "installed_supplier_price_certified":False,
        "native_BAFU_reproduced_LCIA":False,
        "scientific_v1_0_authorized":False,
    }


def markdown(x):
    lines=[
        "# L3-F original stationary Type I 20t->40t H2: engineering evidence gate",
        "",
        "Source F2 has 20,000kg extra MAX inventory and ~17,784.925kg "
        "pressure-swing working reference: DIFFERENT physical quantities.",
        "Model maximum 200bar is **absolute**, not a certified pressure "
        "equipment PED gauge design rating. Real site design is not approved.",
        "",
        "| Release requirement | Source evidence present? |",
        "|---|---|",
    ]
    for row in x["engineering_domains_to_review"]:
        lines.append(f"| {row['domain']}: {row['necessary_engineering_release_task']} | NO |")
    lines.extend([
        "",
        "All 19 source BOM/BoP categories require actual supplier technical "
        "specifications, local project design-basis matching and verified "
        "document custody. A 64-hex digest is not proof of the document's "
        "contents or of a manufacturer's certification.",
        "",
        "EU PED 2014/68/EU applies to stationary pressure equipment subject "
        "to its scope; EIGA DOC15/21 and DOC247/24 provide hydrogen-installation "
        "design and safety guidance. Exact national permitting, legal product "
        "categorisation, equipment CE/PED and site-specific technical review "
        "must be performed by responsible specialists.",
        "",
        "Neither compressor peak duty, process P&ID, hazard analysis, "
        "manufacturer quote, native BAFU LCA, bank viability nor real "
        "industrial installed-cost comparison is established.",
    ])
    return "\n".join(lines)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",type=Path,default=ROOT/"data/results")
    a=p.parse_args(argv)
    root=Path(a.output_dir)
    need(root.is_dir() and not root.is_symlink(),"source public research folder unavailable")
    data=make_contract()
    blobs=[
        (root/OUT_JSON,json.dumps(data,sort_keys=True,indent=2,allow_nan=False)+"\n"),
        (root/OUT_MD,markdown(data)),
    ]
    for path,body in blobs:
        need(not path.is_symlink() and
             (not path.exists() or (path.is_file() and path.read_text(encoding="utf-8")==body)),
             "already existing site qualification evidence differs")
    for path,body in blobs:
        if not path.exists():
            with path.open("x",encoding="utf-8",newline="\n") as f:
                f.write(body)
    print("L3F_ORIGINAL_F2_13_SAFETY_PHYSICAL_DESIGN_AND_19_OEM_SCOPE_CONTRACT_CREATED",
          "all real site and OEM PED certification gates remain blocked")


if __name__=="__main__":
    main()
