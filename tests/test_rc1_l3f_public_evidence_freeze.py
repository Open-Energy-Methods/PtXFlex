"""RC1 freeze: exact four public L3-F evidence records, not station approval."""
import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
REPORTS = {
    "L3F_H30_TYPEI_REFERENCE_20t_INCREMENTAL_FREE_VOLUME_THERMAL_DISCRETE_SCREEN_NOT_OEM_v1.json":
        "de683b92a50daeab7ae656b0ccb5c3accf06ca47bc06964e7d239575ae8cdab4",
    "L3F_H30_TYPEI_REFERENCE_THERMAL_PRESSURE_DESIGN_SCOPE_NOT_OEM_v1.md":
        "fba7c19ed9cc33732cd038c7472c3dbb212fa3cdd0c969899719b5badd510370",
    "L3F_H30_TYPEI_20t_40t_SITE_PED_P_AND_ID_OEM_QUALIFICATION_REQUIREMENTS_NOT_APPROVED_v1.json":
        "82a7d79066a6b683d5bffec694a727ad699a52f7bc1b82b5887382ce24a6107e",
    "L3F_H30_SITE_DESIGN_AND_MANUFACTURER_EVIDENCE_GAPS_NOT_APPROVED_v1.md":
        "f2597107584fa4f055c0b17a2c2cf38cdaa071a6694fbf17c16cac01a2f373db",
}


def test_l3f_published_evidence_is_byte_frozen_without_site_certification():
    assert len(REPORTS) == 4
    for name, expected_sha in REPORTS.items():
        path = ROOT / "data" / "results" / name
        data = path.read_bytes()
        assert data and b"\r" not in data and b"\x00" not in data
        assert hashlib.sha256(data).hexdigest() == expected_sha, (
            "Original published F2/L3-F source evidence changed: " + name)
    thermal = json.loads((ROOT / "data/results" / next(
        x for x in REPORTS if "THERMAL_DISCRETE" in x)).read_text(encoding="utf-8"))
    site = json.loads((ROOT / "data/results" / next(
        x for x in REPORTS if "SITE_PED_" in x)).read_text(encoding="utf-8"))
    assert thermal["origin"]["extra_gross_H2_at_maximum_kg"] == 20000.
    assert thermal["origin"]["original_pressure_swing_extra_withdrawable_H2_kg"] == pytest.approx(
        17784.924849614785)
    assert thermal["OEM_qualified_specific_station"] is False
    assert len(thermal["scenarios"]) == 3
    assert len(site["engineering_domains_to_review"]) == 13
    assert len(site["original_19_equipment_qualification_lines"]) == 19
    assert site["site_pressure_design_engineering_qualified"] is False
    assert site["OEM_and_supplier_all_in_installed_cost_admitted"] is False


def test_full_science_release_lock_and_windows_line_endings_preserved():
    data = json.loads((ROOT / "research/gates-v1.0.json").read_text(encoding="utf-8"))
    ids = [x["id"] for x in data["work_packages"]]
    assert len(ids) == len(set(ids)) == 12
    assert all(x["gate_result"] == "NOT_PASSED" for x in data["work_packages"])
    assert data["release_readiness"]["hydrogen_core_v1_allowed"] is False
    assert data["release_readiness"]["full_methanol_v1_allowed"] is False
    assert data["release_readiness"]["independent_scientific_peer_review_passed"] is False
    attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "data/results/L3F_*.json text eol=lf" in attrs.splitlines()
    assert "data/results/L3F_*.md text eol=lf" in attrs.splitlines()
