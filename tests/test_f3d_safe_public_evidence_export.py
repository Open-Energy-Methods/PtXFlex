"""Hermetic safety contract of the public F3-D aggregate exporter.

No private source, no provider network, no 8,760h sample and no expensive MILP.
The real exporter replays 4 privately archived reviews before publishing.
"""
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"scripts"/"f3d_publish_verified_aggregate_evidence.py"
SPEC=importlib.util.spec_from_file_location("f3d_safe_evidence_exporter",SOURCE)
m=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def mock_aggregate():
    cases=[]
    for year in (2022,2024):
        for mode in ("max_inventory","usable_service"):
            cases.append({
                "year":year,
                "storage_capacity_semantics":mode,
                "year_utc_hours":m.EXPECTED_HOURS[year],
                "price_neutral_E_uniform_hydrogen_service":{
                    "modelled_delivered_h2_tonnes_per_day":30.5,
                    "modelled_delivered_h2_kg_per_year":m.EXPECTED_HOURS[year]*30500/24,
                },
                "matched_service_annual_operational_savings_nominal_eur":1200000.,
                "savings_modelled_nominal_eur_per_kg_of_same_h2_service":1.,
                "solver_reported_savings_lower_eur":1199999.5,
                "solver_reported_savings_upper_eur":1200000.5,
            })
    return {"schema_version":m.SCHEMA,
            "private_hourly_primal_witnesses_released":False,
            "source_original_hourly_arrays_released":False,
            "scientific_v1_0_release_allowed":False,
            "cases":cases}


def test_public_evidence_whitelist_accepts_short_synthetic_scalar_report():
    record=mock_aggregate()
    m.require_safe_output_structure(record)
    document=m.make_report(record)
    assert "2024" in document and "2022" in document
    assert "EUR/kg" in document
    assert "NOT" in document or "not" in document


@pytest.mark.parametrize("bad",[
    lambda x:x.update(target_hourly_kg=list(range(8760))),
    lambda x:x.update(cost_optimum_hourly_states=[{"p":1} for _ in range(500)]),
    lambda x:x.update(private_secret_api_key="never"),
    lambda x:x.update(original_xml="ENTSOE original raw XML"),
    lambda x:x.update(big_array=[1,2,3,4,5]),
    lambda x:x.update(malicious_text="unbounded provider data\n"*100),
])
def test_export_rejects_original_data_or_witness_or_unbounded_array(bad):
    record=mock_aggregate()
    bad(record)
    with pytest.raises(m.PublicExportError):
        m.require_safe_output_structure(record)


def test_writer_is_exact_reproducible_and_rejects_changed_existing_evidence(tmp_path):
    repo=tmp_path/"repo"
    repo.mkdir()
    (repo/"pyproject.toml").write_text("[build-system]\nrequires=[]\n")
    out=repo/"research"
    out.mkdir()
    record=mock_aggregate()
    m.write_outputs(record,out)
    m.write_outputs(record,out)
    j=out/m.PUBLIC_JSON
    t=out/m.PUBLIC_MD
    assert j.is_file() and t.is_file()
    assert json.loads(j.read_text())["cases"][0]["year"]==2022
    text=j.read_text()
    j.write_text(text+"\n")
    with pytest.raises(m.PublicExportError,match="existing published aggregate differs"):
        m.write_outputs(record,out)


def test_missing_or_unverified_reviewer_fails_before_publication():
    receipt={
        "year":2024,"mode":"usable_service",
        "original_year_UTC_hours":8784,
        "E_source_year_price_blind_service_primal_recomputed":True,
        "E_source_year_E_and_ES_full_hourly_primal_mass_energy_cost_recomputed":True,
        "20_200bar_CoolProp_independent_EOS_extrema_recomputed":True,
        "cost_bounds_and_price_neutral_alpha_global_dual_reoptimized_independently":False,
        "source_hourly_primal_arrays_NOT_in_this_report":True,
        "on_site_industrial_or_native_BAFU_LCA_full_release":False,
        "case_audits":{"E":{},"E_plus_S":{}},
    }
    m.verify_review_receipt(receipt,2024,"usable_service")
    for changes in (
        {"original_year_UTC_hours":8760},
        {"E_source_year_E_and_ES_full_hourly_primal_mass_energy_cost_recomputed":False},
        {"source_hourly_primal_arrays_NOT_in_this_report":False},
        {"cost_bounds_and_price_neutral_alpha_global_dual_reoptimized_independently":True},
        {"case_audits":{"E":{}}},
    ):
        bad={**receipt,**changes}
        with pytest.raises(m.PublicExportError):
            m.verify_review_receipt(bad,2024,"usable_service")


def test_missing_evidence_cannot_publish_unverified_synthetic_outputs(tmp_path):
    root=tmp_path/"PRIVATE_DOES_NOT_EXIST"
    with pytest.raises(FileNotFoundError):
        m.build(root)
