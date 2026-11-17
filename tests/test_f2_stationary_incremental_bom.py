"""Manufacturer-grounded *scope*, NOT a falsely completed stationary H2 BOM.

Original IJHE 200bar Type I vessel mass, actual heiserTEC PED stationary
bundle rated capacity (but unknown empty weight), and EIGA/Burckhardt
equipment scope. CoolProp 313K 20-200bar(a) is a SCREEN, not an approved
pressure plate. F3-C source-locked operation does not create hardware mass.
"""
from pathlib import Path
import json
import math
import pytest
pytest.importorskip("CoolProp")

from ptxflex.f2_stationary_incremental_bom import (
    SCHEMA,IncompletePhysicalStation,source_register,
    compute_bank,case_mode,make_incremental_stationary_bank_duty_and_bom
)


def test_public_sources_include_REAL_stationary_heisertec_PED_but_no_stated_empty_weight():
    source,refs=source_register()
    station=refs["heisertec_cosmos_stationary_2026"]["vendor_example"]
    mobile=refs["heisertec_cosmos_mobile_not_stationary_mass"]["mobile_example"]
    paper=refs["ijhe_adm_2026_table2"]["verified_typeI_reference"]
    assert station["application"]=="stationary_PED_not_mobile_TPED"
    assert station["pressure_class_nominal_bar"]==210
    assert station["cylinders_per_stationary_bundle"]==36
    assert station["water_volume_per_cylinder_l"]==87
    assert station["reported_hydrogen_gross_kg_at_vendor_nominal_conditions_per_bundle"]==49
    assert station["stationary_module_nominal_empty_mass_kg"] is None
    assert mobile["nominal_empty_mobile_complete_bundle_kg"]==935
    assert mobile["stationary_application_or_PED_product"] is False
    assert paper["empty_vessel_mass_kg"]==2400
    assert paper["internal_volume_m3"]==1.8
    assert source["assumed_steel_manufacturing_kgCO2e_per_kg"] is None
    assert source["installation_BOM_complete"] is False


@pytest.mark.parametrize("mode",["max_inventory","usable_service"])
def test_20t_to_40t_steel_shell_reference_mass_distinct_from_hydrogen_and_unknown_bop(mode):
    reg,refs=source_register()
    doc=make_incremental_stationary_bank_duty_and_bom()
    assert doc["schema_version"]==SCHEMA
    assert doc["two_storage_capacity_semantics_not_combined"] is True
    assert doc["full_project_LCA_TE_A_allowed"] is False
    d=doc["modes"][mode]
    a,b=d["source_case_E_20t"],d["source_case_EplusS_40t"]
    inc=d["incremental_only_research_sensitivity"]
    delta=b["reference_vessels"]-a["reference_vessels"]
    assert a["source_model_capacity_kg"]==20000 and b["source_model_capacity_kg"]==40000
    assert delta>700
    assert inc["net_additional_published_reference_vessel_count"]==delta
    assert inc["net_additional_published_empty_vessel_equipment_mass_kg"]==delta*2400
    assert inc["net_additional_source_upper_inventory_kg"]==20000
    assert inc["net_additional_published_empty_vessel_equipment_mass_kg"]>20000
    assert inc["source_vessel_mass_is_NOT_virgin_steel_input_kg"] is True
    assert inc["incremental_installed_compressor_equipment_mass_kg"] is None
    assert inc["incremental_cooling_equipment_mass_kg"] is None
    assert inc["incremental_BOP_material_manufacturing_mass_kg"] is None
    assert inc["incremental_native_BAFU_storage_CO2e_kg"] is None
    assert inc["incremental_installed_storage_CAPEX_eur"] is None
    assert inc["actual_total_site_footprint_m2"] is None
    assert inc["paper_reference_full_rack_incremental_positions_if_all_filled"]>=delta-24
    for z in (a,b):
        assert z["residual_heel_kg_at_assumed_20bara_313K"]>0
        assert z["actual_gas_max_kg_at_assumed_200bara_313K"]>z["withdrawable_h2_between_200_and_20_bara_kg"]
    assert not d["full_LCA_or_utility_production_cost_ready"]


def test_usable_gas_capacity_requires_more_steel_shells_than_original_gross_max_model():
    d=make_incremental_stationary_bank_duty_and_bom()
    for source_case in ("source_case_E_20t","source_case_EplusS_40t"):
        gross=d["modes"]["max_inventory"][source_case]
        usable=d["modes"]["usable_service"][source_case]
        assert usable["reference_vessels"]>gross["reference_vessels"]
        assert gross["withdrawable_h2_between_200_and_20_bara_kg"]<gross["source_model_capacity_kg"]
        assert usable["withdrawable_h2_between_200_and_20_bara_kg"]>=usable["source_model_capacity_kg"]
        assert usable["paper_empty_vessels_total_equipment_kg"]>gross["paper_empty_vessels_total_equipment_kg"]


def test_actual_ped_stationary_module_candidate_is_DIFFERENT_210bar_technology():
    d=make_incremental_stationary_bank_duty_and_bom()
    for mode,r in d["modes"].items():
        c=r["commercial_manufacturer_candidate"]
        assert c["OEM"]=="heiserTEC"
        assert c["stationary_module_internal_free_volume_m3_from_vendor_36x87L"]==pytest.approx(3.132)
        assert c["screened_200bara_313K_max_h2_kg_per_stationary_vendor_module"]>c["screened_200bara_313K_20bara_usable_h2_kg_per_vendor_module"]>0
        assert c["screened_stationary_vendor_incremental_module_count_if_RATED_200bara_313K_without_approval"]>0
        assert c["validity_of_using_210bar_vendor_module_as_certified_200bara_313K_installation"] is False
        assert c["stationary_module_empty_mass_kg"] is None
        assert c["stationary_module_galvanized_frame_mass_kg"] is None
        assert c["mobile_TPED_935kg_reference_may_be_applied_to_stationary_PED"] is False
        assert c["OEM_commercial_bare_module_quote_eur"] is None
        if mode=="max_inventory":
            assert c["vendor_210bar_rated_gross_modules_required_for_20t_at_rated_conditions_only"]==409
            assert c["vendor_210bar_rated_gross_modules_required_for_40t_at_rated_conditions_only"]==817
        else:
            assert c["vendor_210bar_rated_gross_modules_required_for_20t_at_rated_conditions_only"] is None
            assert c["vendor_210bar_rated_gross_modules_required_for_40t_at_rated_conditions_only"] is None


def test_bom_scope_has_nonzero_unknown_component_types_NOT_falsely_zero_materials():
    d=make_incremental_stationary_bank_duty_and_bom()
    required={
       "steel_alloy_material_grade_and_inclusions",
       "rack_frames_and_anchors",
       "high_pressure_headers_and_interconnects",
       "isolation_valves_and_actuators",
       "non_return_valves_and_filters",
       "pressure_relief_and_vent_stack",
       "pressure_regulation_delivery_header",
       "compressor_recips_and_seals",
       "compressor_motor_drive_VFD",
       "intercooler_aftercooler_heat_exchange",
       "cooling_pumps_and_fans",
       "gas_quality_dryer_and_sample_system",
       "pressure_temperature_flow_metering",
       "hydrogen_leak_detection_ESD_ATEX",
       "civil_foundations_and_construction",
       "inspections_fatigue_cycle_testing",
       "installation_and_transport",
       "decommission_and_EOL"
    }
    for mode,r in d["modes"].items():
        items=r["required_incremental_system_foreground_BOM"]
        assert len(items)==len(required)+1
        assert {x["line_id"] for x in items[1:]}==required
        assert items[0]["line_id"]=="typeI_200bar_bare_reference_vessels"
        assert items[0]["empty_mass_kg"]>1e6
        assert items[0]["raw_virgin_steel_mass_kg"] is None
        assert all(x["quantity"] is None and x["empty_mass_kg"] is None
                   and x["manufacturer_quote_eur"] is None
                   and x["contribution_to_full_LCI"]=="UNRESOLVED_NONZERO_NOT_ASSUMED_ZERO"
                   for x in items[1:])
        assert r["unknown_non_vessel_equipment_total_mass_kg"] is None
        assert r["complete_source_fabrication_and_installed_mass_kg"] is None
        assert r["complete_manufacturer_warrantied_typeI_bank_BOM"] is False


def test_2023_F3C_source_peak_charge_duty_is_input_not_an_installed_compressor_offer():
    x=make_incremental_stationary_bank_duty_and_bom()
    for mode,data in x["modes"].items():
        a=data["2023_source_case_operations_not_station_hardware_sizing"]
        assert a["E"]["source_2023_optimized_hourly_H2_service_SHA256"]==a["E_plus_S"]["source_2023_optimized_hourly_H2_service_SHA256"]
        for case in ("E","E_plus_S"):
            assert a[case]["source_2023_real_vessel_installation_not_approved"] is True
            assert 0<a[case]["source_reconstructed_duty_2023_kg_h_max_charging"]<=2200+1e-5
            assert 0<a[case]["source_reconstructed_duty_2023_kg_h_max_discharging"]<=2200+1e-5
            assert a[case]["source_2023_modelled_compressor_electricity_MWh"]>0
            assert a[case]["source_nominal_max_charge_kg_h"]==2200.


@pytest.mark.parametrize("mutate",[
 lambda d: d["source_references"][1]["vendor_example"].update(stationary_module_nominal_empty_mass_kg=935),
 lambda d: d["source_references"][2]["mobile_example"].update(stationary_application_or_PED_product=True),
 lambda d: d["source_references"][0]["verified_typeI_reference"].update(empty_vessel_mass_kg=26),
 lambda d: d.update(assumed_steel_manufacturing_kgCO2e_per_kg=2.0),
 lambda d: d.update(installation_BOM_complete=True),
 lambda d: d.update(screened_upper_pressure_bar_absolute=210),
])
def test_fabricated_OEM_mass_or_bafu_factor_or_pressure_plate_cannot_be_accepted(tmp_path,monkeypatch,mutate):
    import ptxflex.f2_stationary_incremental_bom as module
    doc,_=source_register()
    mutate(doc)
    p=tmp_path/"source.json"
    p.write_text(json.dumps(doc),encoding="utf-8")
    monkeypatch.setattr(module,"REGISTER",p)
    with pytest.raises(IncompletePhysicalStation):
        module.source_register()
