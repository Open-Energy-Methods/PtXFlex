"""L3-A PtXFlex source 2023 F3C and F2 financial handoff contract tests.

Models only immutable 2023 original H2 equal-hourly wholesale electricity
difference (2023 real EUR basis) and reference Type I hardware unit mass.
Vendor all-in storage cost, true annual OPEX, taxes and whole-plant LCOH
MUST remain unknown: future cashflow frontiers belong to PtXLens L3-A.
"""
import json
import math
import pytest
import ptxflex.l3a_source_wholesale_economics_handoff as l3


def test_original_source_h2_modes_are_reconciled_with_hardware_and_not_commercial_benchmark():
    a=l3.make_handoff()
    assert a["schema_version"]==l3.SCHEMA
    assert a["model_hydrogen_data_year"]==2023
    assert a["source_registered_F3C_2023_original_sha256"]==l3.F3C_SHA
    assert a["source_registered_F2_200bar_313K_empty_shell_sha256"]==l3.F2_SHA
    assert a["true_plant_vendor_financial_result_or_full_LCOH_permitted"] is False
    assert set(a["distinct_source_capacity_interpretations"])==set(l3.SOURCE_MODE_HASHES)
    for mode,d in a["distinct_source_capacity_interpretations"].items():
        assert d["original_E_modelled_feasible_not_maximum_same_hourly_H2_hash"]==l3.SOURCE_MODE_HASHES[mode]
        assert d["same_hourly_reduced_modelled_H2_kg_year"]<18250000
        assert d["unserved_original_full_H2_contract_kg_year"]>1914720
        assert d["2023_wholesale_only_annual_saving_eur"]>1e6
        assert 0<d["source_solver_proved_annual_wholesale_saving_bounds_eur"][0]<=d["2023_wholesale_only_annual_saving_eur"]<=d["source_solver_proved_annual_wholesale_saving_bounds_eur"][1]
        assert d["source_2023_wholesale_difference_is_NOT_2026_future_revenue_forecast"] is True
        assert d["source_literature_extra_empty_typeI_200bar_vessel_equipment_mass_kg"]==d["source_literature_extra_empty_typeI_200bar_vessel_count"]*2400
        assert d["vendor_installed_actual_INCREMENTAL_CAPEX_eur"] is None
        assert d["true_extra_annual_OPEX_and_maintenance_eur"] is None
        assert d["verified_future_site_market_prices_forecast"] is None
        assert d["approved_full_source_steel_PandID_BAUF_LCIA"] is None
        assert d["source_cross_repo_input_hand_off_ONLY"]


def test_gross_vs_usable_mode_source_numbers_and_sign_correct():
    a=l3.make_handoff()["distinct_source_capacity_interpretations"]
    assert a["max_inventory"]["source_literature_extra_empty_typeI_200bar_vessel_count"]==802
    assert a["max_inventory"]["source_literature_extra_empty_typeI_200bar_vessel_equipment_mass_kg"]==1924800
    assert a["max_inventory"]["2023_wholesale_only_annual_saving_eur"]==pytest.approx(1124332.2692838833,abs=.02)
    assert a["usable_service"]["source_literature_extra_empty_typeI_200bar_vessel_count"]==902
    assert a["usable_service"]["source_literature_extra_empty_typeI_200bar_vessel_equipment_mass_kg"]==2164800
    assert a["usable_service"]["2023_wholesale_only_annual_saving_eur"]==pytest.approx(1103463.7287309095,abs=.02)
    assert a["max_inventory"]["original_E_modelled_feasible_not_maximum_same_hourly_H2_hash"]!=a["usable_service"]["original_E_modelled_feasible_not_maximum_same_hourly_H2_hash"]


@pytest.mark.parametrize("key,bad",[
 ("f3c_sha256","0"*64),
 ("f2_typeI_bom_sha256","0"*64),
 ("strict_modes",["usable_service"]),
 ("source_research_release_full_v1_allowed",True),
])
def test_source_manifest_handoff_2023_and_physical_capex_not_alterable(tmp_path,monkeypatch,key,bad):
    d=json.loads(l3.MANIFEST.read_text(encoding="utf-8"));d[key]=bad
    path=tmp_path/"manifest.json";path.write_text(json.dumps(d))
    monkeypatch.setattr(l3,"MANIFEST",path)
    with pytest.raises(l3.UnsupportedFutureCostClaim):
        l3.make_handoff()


def test_original_source_electricity_savings_not_recast_as_actual_future_plant_cost(tmp_path,monkeypatch):
    d=json.loads(l3.MANIFEST.read_text(encoding="utf-8"))
    d["not_qualified_claims"]["actual_vendor_capex_known"]=True
    path=tmp_path/"manifest.json";path.write_text(json.dumps(d))
    monkeypatch.setattr(l3,"MANIFEST",path)
    with pytest.raises(l3.UnsupportedFutureCostClaim):
        l3.make_handoff()


def test_tampered_source_MIP_2023_verification_result_rejected_before_cashflow(tmp_path,monkeypatch):
    d=json.loads(l3.F3C.read_text(encoding="utf-8"))
    d["modes"]["max_inventory"]["EplusS_2023_wholesale_saving_eur"]=99999999
    path=tmp_path/"source_f3c.json";path.write_text(json.dumps(d))
    monkeypatch.setattr(l3,"F3C",path)
    with pytest.raises(l3.UnsupportedFutureCostClaim,match="source-2023 E/ES matched H2"):
        l3.make_handoff()
