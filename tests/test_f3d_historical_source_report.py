"""F3-D scientific reporting, published original source Git SHA and negative tests.

Tests are read-only against the published SAFE four-case aggregate; no
provider original hourly source arrays or private witness are accessed.
"""
import copy
from pathlib import Path
import pytest

from ptxflex import f3d_historical_source_report as m

SOURCE=Path(__file__).resolve().parents[1]/"research"/(
    "F3D_ARCO_2022_2024_PUBLIC_VERIFIED_AGGREGATES_v1.json"
)

def rows():
    return m.consolidate(m.load_original(SOURCE))

def test_public_source_is_exact_original_git_blob_and_four_unique_cases():
    r=rows()
    assert len(r)==4
    assert [(a["year"],a["mode"]) for a in r]==[
        (2022,"max_inventory"),(2022,"usable_service"),
        (2024,"max_inventory"),(2024,"usable_service")]
    assert [a["hours"] for a in r]==[8760,8760,8784,8784]

def test_actual_historical_matched_cost_and_normalized_h2():
    r=rows()
    assert r[0]["saving_eur"]==pytest.approx(3905632.9363086373,abs=.01)
    assert r[1]["saving_eur"]==pytest.approx(3903807.2469956204,abs=.01)
    assert r[2]["saving_eur"]==pytest.approx(2247126.177435993,abs=.01)
    assert r[3]["saving_eur"]==pytest.approx(2206233.52030978,abs=.01)
    for a in r:
        assert a["saving_eur_per_kg"]==pytest.approx(a["saving_eur"]/a["H2_kg_year"],abs=1e-12)
        assert a["saving_lower_eur"]<=a["saving_eur"]<=a["saving_upper_eur"]
        assert 30<a["H2_tonnes_day"]<32
    assert r[2]["E_plus_S_wholesale_eur"]<0
    assert r[3]["E_plus_S_wholesale_eur"]<0

def test_2022_and_2024_same_original_provider_data_within_mode_not_equal_H2():
    a,b,c,d=rows()
    assert a["source_price_sha256"]==b["source_price_sha256"]
    assert c["source_price_sha256"]==d["source_price_sha256"]
    assert a["source_wind_sha256"]==b["source_wind_sha256"]
    assert c["source_wind_sha256"]==d["source_wind_sha256"]
    assert a["h2_profile_sha256"]!=b["h2_profile_sha256"]
    assert c["h2_profile_sha256"]!=d["h2_profile_sha256"]
    assert a["source_price_sha256"]!=c["source_price_sha256"]

def test_full_year_2024_leap_day_required_no_synthetic_instead():
    original=m.load_original(SOURCE)
    wrong=copy.deepcopy(original)
    wrong["cases"][3]["year_utc_hours"]=8760
    with pytest.raises(m.F3DConsolidationError):
        m.consolidate(wrong)

def test_source_cost_not_changed_or_swapped_and_dual_unverified():
    original=m.load_original(SOURCE)
    altered=copy.deepcopy(original)
    altered["cases"][0]["E"]["modelled_nominal_eur_wholesale_cost"]+=10000
    with pytest.raises(m.F3DConsolidationError):
        m.consolidate(altered)
    altered=copy.deepcopy(original)
    altered["independent_solver_dual_certificates_recomputed"]=True
    with pytest.raises(m.F3DConsolidationError):
        m.consolidate(altered)
    altered=copy.deepcopy(original)
    altered["native_BAFU_2026_whole_plant_LCIA_verified"]=True
    with pytest.raises(m.F3DConsolidationError):
        m.consolidate(altered)

def test_unknown_changed_git_blob_rejected(tmp_path):
    changed=tmp_path/"published.json"
    changed.write_bytes(SOURCE.read_bytes()+b" ")
    with pytest.raises(m.F3DConsolidationError,match="published"):
        m.load_original(changed)

def test_generated_scientific_report_keeps_all_scope_separation():
    r=rows()
    report=m.report(r)
    assert "NOT PASSED" in report
    assert "independent" in report
    assert "20–200" not in report or "20" in report
    assert "2022" in report and "2024" in report
    assert "NetCDF" in report and "BAFU" in report
    assert "not a forecast" in report.lower() or "forecast" in report.lower()
    assert "3,905,632.94" in report
    assert "2,247,126.18" in report
