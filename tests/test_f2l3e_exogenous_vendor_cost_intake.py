"""F2/L3-E OEM quote intake honors published original Type I reference only.

All OEM actual CAPEX/OPEX/material/pressure quantities deliberately remain
UNKNOWN. This is evidence/role intake, not a price estimator.
"""
import copy
import json

import pytest

from ptxflex import f2l3e_exogenous_vendor_cost_intake as m


def test_source_locked_19_BOM_scope_and_reference_only_hardware():
    intake=m.make()
    assert intake["source_F2_modelled_2023_geometry_reference_Git_blob"]==\
           m.SOURCE_GIT_BLOB
    rows=intake["nineteen_required_supplier_and_site_intake_lines"]
    assert len(rows)==19
    assert len({row["line_id"] for row in rows})==19
    assert rows[0]["paper_reference_empty_hardware_vessel_count_NOT_OEM"]==802
    assert rows[0]["paper_reference_empty_equipment_mass_kg_NOT_steel_input"]==1924800
    assert rows[0]["manufacturer_installed_actual_quantity"] is None
    assert intake["manufacturer_quote_aggregated_all_in_incremental_installed_CAPEX_eur"] is None
    assert intake["native_BAFU_2026_original_v11_inventory_or_LCIA_certified"] is False


def test_actual_18_BOP_scopes_require_vendor_and_pressure_evidence():
    x=m.make()["nineteen_required_supplier_and_site_intake_lines"]
    for row in x:
        assert row["manufacturer_total_quoted_incremental_CAPEX_eur"] is None
        assert row["manufacturer_actual_virgin_material_input_kg"] is None
        assert row["manufacturer_individual_component_masses_kg"] is None
        assert row["certified_hydrogen_service_or_PED_document_SHA256"] is None
        assert row["quote_currency_price_date_and_location"] is None
        assert row["BAFU_original_native_v11_manufacturing_flow_verified"] is False
    assert all(row["paper_reference_empty_equipment_mass_kg_NOT_steel_input"] is None
               for row in x[1:])


def test_prevent_overlapping_initial_material_maintenance_and_decommission_cost():
    x={r["line_id"]:r for r in m.make()["nineteen_required_supplier_and_site_intake_lines"]}
    assert x["steel_alloy_material_grade_and_inclusions"]["cost_role"]==(
        "design_material_specification_not_separate_capex_without_justification")
    assert x["inspections_fatigue_cycle_testing"]["cost_role"]==(
        "recurring_opex_and_planned_replacement_duty")
    assert x["decommission_and_EOL"]["cost_role"]==(
        "terminal_decommission_and_end_of_life")
    assert x["civil_foundations_and_construction"]["cost_role"]==(
        "initial_incremental_all_in_site_capex")


def test_no_vendor_quote_must_not_result_in_zero_qualified_capex():
    r=m.review_private_ledger(m.make())
    assert r["complete_supplier_cost_quote_line_count"]==0
    assert len(r["unquoted_or_unpriced_line_ids"])==19
    assert r["can_calculate_verified_actual_full_installed_CAPEX"] is False
    assert r["native_BAFU_original_LCIA_accepted"] is False


def test_fabricated_zero_cost_without_signed_exclusion_rejected():
    d=m.make()
    r=d["nineteen_required_supplier_and_site_intake_lines"][0]
    r["manufacturer_total_quoted_incremental_CAPEX_eur"]=0
    r["signed_quote_file_sha256"]="0"*64
    x=m.review_private_ledger(d)
    assert any("zero_price_requires_engineer_exclusion" in s
               for s in x["malformed_vendor_cost_evidence_line_reasons"])


def test_false_price_without_vendor_document_and_material_without_spec_rejected():
    d=m.make()
    r=d["nineteen_required_supplier_and_site_intake_lines"][0]
    r["manufacturer_total_quoted_incremental_CAPEX_eur"]=100000.
    r["manufacturer_actual_virgin_material_input_kg"]=1900000.
    x=m.review_private_ledger(d)
    assert any("quote_file_hash_missing" in s for s in x[
        "malformed_vendor_cost_evidence_line_reasons"])
    assert any("manufacturing_mass_requires_signed_specification" in s
               for s in x["malformed_vendor_cost_evidence_line_reasons"])
    assert x["can_calculate_verified_actual_full_installed_CAPEX"] is False


def test_deceptive_omission_and_out_of_scope_source_fail_closed():
    d=m.make()
    d["nineteen_required_supplier_and_site_intake_lines"].pop()
    with pytest.raises(m.VendorEvidenceBlocked,match="missing/misaligned"):
        m.review_private_ledger(d)
    d=m.make()
    d["source_F2_modelled_2023_geometry_reference_Git_blob"]="fake"
    with pytest.raises(m.VendorEvidenceBlocked,match="original F2"):
        m.review_private_ledger(d)


def test_supplier_intake_remains_json_serializable_but_unqualified():
    d=m.make()
    y=json.loads(json.dumps(d,sort_keys=True,allow_nan=False))
    assert y==d
    assert y["actual_investment_viability_established"] is False
    assert m.review_private_ledger(y)["manufacturer_PED_or_ATEX_certified_design_admitted"] is False


def test_role_separated_maintenance_EOL_and_material_specs_are_not_capex_double_counted():
    # Synthetic evidence only. Populating a questionnaire never constitutes
    # authenticated vendor cost or a certified source plant.
    d=m.make()
    rows={r["line_id"]:r for r in d["nineteen_required_supplier_and_site_intake_lines"]}
    maint=rows["inspections_fatigue_cycle_testing"]
    maint["incremental_annual_maintenance_OPEX_eur"]=15000.
    maint["signed_quote_file_sha256"]="a"*64
    eol=rows["decommission_and_EOL"]
    eol["terminal_decommission_liability_eur"]=75000.
    eol["signed_quote_file_sha256"]="b"*64
    spec=rows["steel_alloy_material_grade_and_inclusions"]
    spec["signed_specification_file_sha256"]="c"*64
    spec["manufacturer_specification_revision"]="fictitious test only"
    result=m.review_private_ledger(d)
    assert result["complete_supplier_cost_quote_line_count"]==3
    assert result["maintenance_cost_and_terminal_decommission_NOT_forced_into_initial_CAPEX"] is True
    assert maint["manufacturer_total_quoted_incremental_CAPEX_eur"] is None
    assert eol["manufacturer_total_quoted_incremental_CAPEX_eur"] is None
    assert spec["manufacturer_total_quoted_incremental_CAPEX_eur"] is None
    assert result["can_calculate_verified_actual_full_installed_CAPEX"] is False
    assert result["can_calculate_verified_actual_incremental_annual_OPEX"] is False
    assert result["manufacturer_document_external_signature_authenticated"] is False


def test_unjustified_zero_annual_maintenance_and_terminal_costs_rejected():
    d=m.make()
    rows={r["line_id"]:r for r in d["nineteen_required_supplier_and_site_intake_lines"]}
    maint=rows["inspections_fatigue_cycle_testing"]
    maint["incremental_annual_maintenance_OPEX_eur"]=0.
    maint["signed_quote_file_sha256"]="d"*64
    eol=rows["decommission_and_EOL"]
    eol["terminal_decommission_liability_eur"]=0.
    eol["signed_quote_file_sha256"]="e"*64
    result=m.review_private_ledger(d)
    assert sum("zero_price_requires_engineer_exclusion" in issue
               for issue in result["malformed_vendor_cost_evidence_line_reasons"])==2
    assert result["native_BAFU_original_LCIA_accepted"] is False
