"""L3-F station PED/site documentary gate, no false certification claims."""
import pytest
from ptxflex import f2l3f_stationary_site_evidence_gate as m


def test_original_source_13_domains_and_19_equipment_lines_remain_unverified():
    d=m.make_contract()
    assert d["schema_version"]==m.SCHEMA
    assert len(d["engineering_domains_to_review"])==13
    assert len(d["original_19_equipment_qualification_lines"])==19
    assert d["model_pressure_high_BAR_ABSOLUTE_NOT_automatic_PED_gauge_MAWP"]==200.
    assert d["actual_OEM_allowable_gauge_pressure_MAWP_bar_gauge"] is None
    assert d["actual_2022_2024_full_hourly_peak_compressor_charging_flow_kg_h"] is None
    assert d["actual_2022_2024_full_hourly_peak_hydrogen_withdrawal_flow_kg_h"] is None
    assert d["site_pressure_design_engineering_qualified"] is False
    assert d["OEM_and_supplier_all_in_installed_cost_admitted"] is False


def test_no_external_documents_cannot_be_self_certified():
    x=m.review_candidate_metadata(m.make_contract())
    assert len(x["unverified_or_missing_documentary_domains"])==13
    assert x["original_equipment_requirement_categories"]==19
    assert x["physical_hydrogen_station_approved"] is False
    assert x["scientific_v1_0_authorized"] is False


def test_synthetic_hashes_cannot_make_P_and_ID_or_PED_certified():
    d=m.make_contract()
    for row in d["engineering_domains_to_review"]:
        row["original_signed_engineering_record_sha256"]="a"*64
        row["original_verified_manufacturer_attestation_sha256"]="b"*64
        row["qualified_engineer_independent_review_receipt_sha256"]="c"*64
        row["project_and_design_basis_concordance_reviewed"]=True
    x=m.review_candidate_metadata(d)
    assert x["unverified_or_missing_documentary_domains"]==[]
    assert x["authenticated_external_OEM_P_and_ID_and_PED_classification"] is False
    assert x["physical_hydrogen_station_approved"] is False


def test_missing_manufacturer_hash_for_admitted_installed_quantity_fails():
    d=m.make_contract()
    d["original_19_equipment_qualification_lines"][0][
        "actual_qualified_installed_quantity"]=802
    x=m.review_candidate_metadata(d)
    assert any("physical_quantity_without_signed_source" in z
               for z in x["internally_contradictory_evidence_claims"])


def test_material_manufacturing_lci_claim_requires_material_mass():
    d=m.make_contract()
    d["original_19_equipment_qualification_lines"][0][
        "BAFU_manufacturing_materials_specified"]=True
    x=m.review_candidate_metadata(d)
    assert any("native_lci_claim_without_source_material_mass" in z
               for z in x["internally_contradictory_evidence_claims"])


def test_wrong_source_19_requirements_or_storage_semantics_rejected():
    d=m.make_contract()
    d["original_19_equipment_qualification_lines"].pop()
    with pytest.raises(m.L3FDocumentaryGateError):
        m.review_candidate_metadata(d)
    d=m.make_contract()
    d["storage_cap_semantics"]="usable_service"
    with pytest.raises(m.L3FDocumentaryGateError):
        m.review_candidate_metadata(d)


def test_readable_evidence_requirements_do_not_claim_vendor_certification():
    x=m.markdown(m.make_contract())
    assert "PED" in x
    assert "gauge" in x
    assert "no" in x.lower()
    assert "NO" in x
