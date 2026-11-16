"""F2/L3-E: incremental 20t→40t original Type I OEM quote evidence intake.

Emit an auditable PRIVATE manufacturer request FOR EACH original source BOM
category, not claimed vendor costs. Public screening can cite the 802 *paper
reference* extra 2400kg EMPTY equipment vessels, NEVER claim that a vendor
has quoted or certified that count, pressure vessel wall thickness, installed
material/steel kg, actual supplier bill or native BAFU process.

Accounting allocation rules avoid double counting: an alloy/material grade
specification is NOT separately billable if already in vessel quote; annual
inspection/maintenance is not capitalized silently; decommission is terminal;
civil construction and installation are initial BoP, replacements require
a distinct future date, cost and independent evidence. Any category legitimately
NOT APPLICABLE needs an engineering rationale and a signed source reference,
not a fabricated EUR0 price.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"data/results/F2_L1_2023_source_incremental_20t_to_40t_stationary_typeI_200bar_BOM_SCOPE_NOT_complete_native_LCI.json"
SOURCE_GIT_BLOB="424a8f738cb9caa2d05c1ec5c22cbf6cdd601b82"
SCHEMA="ptxflex.f2l3e_H30_incremental_typeI_20t_to_40t_supplier_installed_cost_evidence_intake.v1"
OUT="F2L3E_H30_INCREMENTAL_20t_40t_TYPEI_OEM_BOM_COST_EVIDENCE_INTAKE_NOT_QUOTES_v1.json"
MODE="max_inventory"

COST_ROLES={
    "steel_alloy_material_grade_and_inclusions":"design_material_specification_not_separate_capex_without_justification",
    "inspections_fatigue_cycle_testing":"recurring_opex_and_planned_replacement_duty",
    "decommission_and_EOL":"terminal_decommission_and_end_of_life",
    "installation_and_transport":"initial_incremental_all_in_site_capex",
    "civil_foundations_and_construction":"initial_incremental_all_in_site_capex",
}


class VendorEvidenceBlocked(ValueError):
    pass


def need(cond,why):
    if not cond:
        raise VendorEvidenceBlocked("F2/L3-E OEM evidence: "+why)


def sha1blob(raw):
    # Git stores the published UTF-8 JSON with LF. Windows Git can expose
    # CRLF in older working-tree files; normalize ONLY text newline bytes,
    # never scientific numbers or original equipment scope fields.
    canonical=raw.replace(b"\r\n",b"\n")
    return hashlib.sha1(
        b"blob "+str(len(canonical)).encode("ascii")+b"\0"+canonical
    ).hexdigest()


def original():
    need(SOURCE.is_file() and not SOURCE.is_symlink(),
         "original source-locked published Type I research reference unavailable")
    raw=SOURCE.read_bytes()
    need(sha1blob(raw)==SOURCE_GIT_BLOB,
         "F2 original published 19-line BOM Git source changed")
    d=json.loads(raw.decode("utf-8"))
    need(d.get("full_project_LCA_TE_A_allowed") is False and
         d.get("schema_version")==
         "ptxflex.f2_l1_typeI_200bar_incremental_stationary_h2_equipment_requirements.v1",
         "source physical requirements are incorrectly certified")
    modes=d.get("modes")
    need(type(modes) is dict and set(modes)=={"max_inventory","usable_service"},
         "source model capacity interpretations are not separate")
    data=modes[MODE]
    ref=data.get("incremental_only_research_sensitivity",{})
    need(data.get("complete_manufacturer_warrantied_typeI_bank_BOM") is False and
         ref.get("net_additional_published_reference_vessel_count")==802 and
         ref.get("net_additional_published_empty_vessel_equipment_mass_kg")==1924800 and
         ref.get("source_vessel_mass_is_NOT_virgin_steel_input_kg") is True and
         ref.get("incremental_installed_storage_CAPEX_eur") is None and
         ref.get("incremental_native_BAFU_storage_CO2e_kg") is None,
         "reference count/equipment mass wrongly promoted to quoted costs or LCA")
    lines=data.get("required_incremental_system_foreground_BOM")
    need(type(lines) is list and len(lines)==19 and
         len({r.get("line_id") for r in lines})==19,
         "source 19-row incremental bank/BoP/replacement ledger changed")
    return lines


def make():
    lines=original()
    questionnaire=[]
    for x in lines:
        label=x["line_id"]
        ref=label=="typeI_200bar_bare_reference_vessels"
        questionnaire.append({
            "line_id":label,
            "original_system_scope":x["system"],
            "original_requirement_source":x["source_ref_id"],
            "manufacturer_model_number":None,
            "manufacturer_legal_entity":None,
            "manufacturer_specification_revision":None,
            "signed_specification_file_sha256":None,
            "signed_quote_file_sha256":None,
            "quote_issue_date":None,
            "quote_valid_until_date":None,
            "quote_currency":None,
            "quote_currency_price_date_and_location":None,
            "quoted_installation_scope_and_double_counting_exclusions":None,
            "pressure_design_basis_absolute_vs_gauge":None,
            "pressure_design_range_bar":None,
            "design_temperature_range_kelvin":None,
            "certified_hydrogen_service_or_PED_document_SHA256":None,
            "site_layout_and_P_and_ID_evidence_SHA256":None,
            "manufacturer_installed_actual_quantity":None,
            "manufacturer_installed_unit":None,
            "manufacturer_total_quoted_incremental_CAPEX_eur":None,
            "manufacturer_individual_component_masses_kg":None,
            "manufacturer_actual_virgin_material_input_kg":None,
            "fabrication_and_scrap_yields":None,
            "replacement_years_and_cost_eur":None,
            "incremental_annual_maintenance_OPEX_eur":None,
            "terminal_decommission_liability_eur":None,
            "terminal_EOL_recovery_credit_eur":None,
            "reason_category_is_omitted_with_signed_engineering_source":None,
            "cost_role":COST_ROLES.get(
                label,"initial_incremental_all_in_site_capex_and_possible_replacement"),
            "paper_reference_empty_hardware_vessel_count_NOT_OEM":
                802 if ref else None,
            "paper_reference_empty_equipment_mass_kg_NOT_steel_input":
                1924800 if ref else None,
            "actual_supplier_quote_present":False,
            "design_pressure_certification_verified":False,
            "BAFU_original_native_v11_manufacturing_flow_verified":False,
            "costs_valid_for_exogenous_H30_source_year_2022_or_2024":False,
        })
    return {
        "schema_version":SCHEMA,
        "source_F2_modelled_2023_geometry_reference_Git_blob":SOURCE_GIT_BLOB,
        "applicable_source_years_for_hypothetical_H30_economics":[2022,2024],
        "capacity_semantics":MODE,
        "nominal_reference_storage_delta_kg_H2":20000.,
        "commercially_qualified_typeI_20_200bar_stationary_bank":False,
        "source_reference_802_vessels_not_vendor_installed_count":True,
        "source_reference_1924800kg_is_empty_equipment_not_material_input":True,
        "manufacturer_quote_aggregated_all_in_incremental_installed_CAPEX_eur":None,
        "incremental_annual_OPEX_EUR_per_year":None,
        "incremental_replacements_and_decommissioning":None,
        "native_BAFU_2026_original_v11_inventory_or_LCIA_certified":False,
        "pricing_and_site_inspection_evidence_has_been_authenticated":False,
        "no_assumption_that_NA_categories_are_zero_cost":True,
        "actual_investment_viability_established":False,
        "nineteen_required_supplier_and_site_intake_lines":questionnaire,
    }


def review_private_ledger(ledger):
    """Incomplete fields remain unknown. Never turn populated JSON into OEM certification."""
    need(type(ledger) is dict and ledger.get("schema_version")==SCHEMA and
         ledger.get("source_F2_modelled_2023_geometry_reference_Git_blob")==SOURCE_GIT_BLOB and
         ledger.get("capacity_semantics")==MODE,
         "supplier form not matched to original F2 pressure requirements")
    registered=make()
    rows=ledger.get("nineteen_required_supplier_and_site_intake_lines")
    expected=registered["nineteen_required_supplier_and_site_intake_lines"]
    need(type(rows) is list and len(rows)==19 and
         [r.get("line_id") for r in rows]==[r["line_id"] for r in expected],
         "supplier quote ledger has missing/misaligned source BOM items")
    missing=[]
    malformed=[]
    complete=0
    for row,ref in zip(rows,expected):
        line=row["line_id"]
        role=ref["cost_role"]
        if row.get("cost_role")!=role:
            malformed.append(line+":cost_allocation_treatment_changed")
        # A material specification can already be IN the vessel quote.
        # Inspections are annual OPEX, EOL is a terminal liability; they
        # MUST NOT be forced to quote another upfront CAPEX line.
        if role=="design_material_specification_not_separate_capex_without_justification":
            fields=("signed_specification_file_sha256","manufacturer_specification_revision")
            evidence_ready=all(row.get(f) for f in fields)
        elif role=="recurring_opex_and_planned_replacement_duty":
            fields=("incremental_annual_maintenance_OPEX_eur","signed_quote_file_sha256")
            evidence_ready=all(row.get(f) is not None for f in fields)
        elif role=="terminal_decommission_and_end_of_life":
            fields=("terminal_decommission_liability_eur","signed_quote_file_sha256")
            evidence_ready=all(row.get(f) is not None for f in fields)
        else:
            fields=("manufacturer_total_quoted_incremental_CAPEX_eur","signed_quote_file_sha256")
            evidence_ready=all(row.get(f) is not None for f in fields)
        if not evidence_ready:
            missing.append(line)
        else:
            complete+=1
        for key in ("manufacturer_total_quoted_incremental_CAPEX_eur",
                    "incremental_annual_maintenance_OPEX_eur",
                    "terminal_decommission_liability_eur",
                    "terminal_EOL_recovery_credit_eur"):
            val=row.get(key)
            if val is not None and (
                type(val) not in (int,float) or not math.isfinite(val) or val<0
            ):
                malformed.append(line+":invalid_nonnegative_"+key)
        quote_used=any(row.get(k) is not None for k in (
            "manufacturer_total_quoted_incremental_CAPEX_eur",
            "incremental_annual_maintenance_OPEX_eur",
            "terminal_decommission_liability_eur",
        ))
        if quote_used and not row.get("signed_quote_file_sha256"):
            malformed.append(line+":quote_file_hash_missing")
        for key in ("manufacturer_total_quoted_incremental_CAPEX_eur",
                    "incremental_annual_maintenance_OPEX_eur",
                    "terminal_decommission_liability_eur"):
            if row.get(key)==0 and not row.get(
                "reason_category_is_omitted_with_signed_engineering_source"):
                malformed.append(line+":zero_price_requires_engineer_exclusion")
        if row.get("manufacturer_actual_virgin_material_input_kg") is not None and (
            row.get("manufacturer_individual_component_masses_kg") is None or
            row.get("signed_specification_file_sha256") is None
        ):
            malformed.append(line+":manufacturing_mass_requires_signed_specification")
    return {
        "schema_version":"ptxflex.f2l3e_H30_vendor_ledger_COMPLETENESS_only.v1",
        "source_F2_original_Git_blob_SHA1":SOURCE_GIT_BLOB,
        "complete_supplier_cost_quote_line_count":complete,
        "unquoted_or_unpriced_line_ids":missing,
        "malformed_vendor_cost_evidence_line_reasons":malformed,
        "maintenance_cost_and_terminal_decommission_NOT_forced_into_initial_CAPEX":True,
        "can_calculate_verified_actual_full_installed_CAPEX":False,
        "can_calculate_verified_actual_incremental_annual_OPEX":False,
        "manufacturer_document_external_signature_authenticated":False,
        "manufacturer_PED_or_ATEX_certified_design_admitted":False,
        "native_BAFU_original_LCIA_accepted":False,
        "scientific_v1_0_qualified":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(argv)
    out=a.output
    need(out.parent.is_dir() and not out.is_symlink(),
         "supplier research intake output parent missing or symlinked")
    data=json.dumps(make(),indent=2,sort_keys=True,allow_nan=False)+"\n"
    need(not out.exists() or
         (out.is_file() and out.read_text(encoding="utf-8")==data),
         "cannot overwrite non-identical supplier research scope")
    if not out.exists():
        with out.open("x",encoding="utf-8",newline="\n") as f:
            f.write(data)
    print("F2L3E_ORIGINAL_2023_REFERENCED_19_LINE_MANUFACTURER_QUOTE_SCOPE_CREATED",
          "802 hypothetical Type I vessel reference positions only; 0 vendor prices quoted")


if __name__=="__main__":
    main()
