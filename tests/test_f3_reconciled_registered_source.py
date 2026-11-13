"""Real source-derived F3 final reconciliation is hash-locked to six CI artifacts.

The report is a scenario-screen result only, not an independent validation
of industrial hardware or source of native tank manufacturing emissions.
"""
from pathlib import Path
import hashlib
import json

DATA=Path(__file__).resolve().parents[1]/"data/results/F3_2023_reconciled_research_evidence.json"
EXPECTED="5dead18cfa0c3fecf15562f423e01044bcc6ad4ba4f5212dfb44a010b0d1a0d3"


def test_real_2023_derived_reconciled_evidence_unchanged_and_mathematically_consistent():
    data=DATA.read_bytes()
    assert hashlib.sha256(data).hexdigest()==EXPECTED
    x=json.loads(data)
    assert x["schema_version"]=="ptxflex.f3_2023_pressure_adequacy_reconciled.v1"
    assert x["source_original_E_zip_sha256"]=="069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051"
    assert x["source_original_EplusS_zip_sha256"]=="cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9"
    assert len(x["stageA_certificate_input_sha256"])==4
    assert len(x["independent_full_service_witness_sha256"])==2
    assert not x["matched_service_E_vs_EplusS_LCA_or_TEA_comparison_eligible"]
    for mode in ("max_inventory","usable_service"):
        E=x["modes"][mode]["cases"]["E"]
        ES=x["modes"][mode]["cases"]["E_plus_S"]
        assert E["minimum_additional_modelled_H2_shortfall_lower_bound_kg"]>0
        assert E["minimum_additional_modelled_H2_shortfall_lower_bound_kg"]<=E["minimum_additional_modelled_H2_shortfall_upper_bound_kg"]
        assert ES["minimum_additional_modelled_H2_shortfall_lower_bound_kg"]==0
        assert ES["minimum_additional_modelled_H2_shortfall_upper_bound_kg"]==0
        assert E["native_full_plant_GWP_kgCO2e"] is None
        assert ES["complete_project_annual_cost_eur"] is None
