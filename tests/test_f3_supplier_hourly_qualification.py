"""Source-model hourly shortfall, two H2 agreements and synthetic pressure negative controls."""
import math
import pytest
from ptxflex.f3_supplier_hourly_qualification import (
    UnqualifiedContractEvidence,_source_registry,_source_demand,
    check_no_buffer_interface,_illustration,source_only_boundary_tests,
)

@pytest.mark.parametrize("mode,hrs,annual,peak",[
 ("max_inventory",176,66524.31653871357,1029.0279027902793),
 ("usable_service",91,3720.371002091906,183.60901388726026),
])
def test_actual_frozen_2023_H2_hourly_load_and_network_HHV_study_conversion(mode,hrs,annual,peak):
    a=check_no_buffer_interface(mode)
    assert a["source_positive_need_hours"]==hrs
    assert math.isclose(a["source_mode_feasible_incumbent_annual_shortage_kg"],annual,abs_tol=.002)
    assert math.isclose(a["source_mode_feasible_incumbent_max_hour_kg_h"],peak,abs_tol=.002)
    assert math.isclose(a["source_mode_peak_HHV_from_HNS_2026_CSA_kWh_h"],
                        peak*12.74/.090/3.6,abs_tol=1e-3)
    assert a["numerical_flow_only_result"].startswith("NOT_ASSESSABLE")
    assert a["modelled_unmet_backup_need_kg"] is None
    assert not a["supplier_professionally_qualified"]
    assert a["HNS_network_transport_not_molecule_supplier"]
    assert a["exit_CDS_pressure_and_firm_flow_not_proved"]
    assert not a["full_matched_service_LCA_or_TEA_allowed"]
    assert a["financial_cost_EUR_per_kg"] is None

@pytest.mark.parametrize("mode",["max_inventory","usable_service"])
def test_2023_source_each_hour_mathematical_no_buffer_flow_pressure_reliability_quality(mode):
    perfect=check_no_buffer_interface(mode,_illustration(mode,"EXACT_PEAK_FLOW_20BARA_PERFECT_UPTIME"))
    assert perfect["modelled_unmet_backup_need_kg"]==0.
    assert perfect["modelled_unmet_backup_hours"]==0
    assert not perfect["supplier_professionally_qualified"]
    assert not perfect["full_matched_service_LCA_or_TEA_allowed"]
    for scenario,why in (
      ("BELOW_PEAK_FLOW_ONE_HALF","insufficient_supplier_flow_hours"),
      ("LOW_PRESSURE_AT_CUSTOMER_NODE","low_customer_product_pressure_hours"),
      ("EXIT_OR_SUPPLIER_OFFLINE_AT_PEAK_HOUR","supplier_or_exit_connection_offline_hours"),
      ("PRODUCT_QUALITY_FAILED_AT_PEAK_HOUR","product_quality_rejected_hours"),
    ):
        x=check_no_buffer_interface(mode,_illustration(mode,scenario))
        assert x["modelled_unmet_backup_need_kg"]>0
        assert x["modelled_unmet_backup_hours"]>0
        assert x["failed_condition_hour_counts_overlap_not_additive"][why]>0
        assert not x["full_matched_service_LCA_or_TEA_allowed"]

def test_explicit_no_mislocation_offshore_wind_grid_vs_pipeline_exit_and_no_hns_gas_supply():
    d=_source_registry()
    assert d["original_PyNEXUS_annual_config"]["original_ERA5_wind_resource_location"]=={
        "lat":52.5,"lon":3.5,
        "description":"Approximate offshore North Sea resource grid; NOT actual industrial H2 customer/electrolyser or delivery connection"
    }
    assert d["original_PyNEXUS_annual_config"]["industrial_H2_delivered_site_lat_lon"] is None
    assert d["commercial_and_technical_roles"]["hynetwork_is_not_H2_molecule_supply_guarantor"]
    assert len(d["official_operator_sources"])>=7
    assert d["hynetwork_study_HHV_kWh_per_kg_derived"]>39.0

def test_2023_2026_split_and_no_synthetic_supplier_certification_even_when_flow_passes():
    d=source_only_boundary_tests()
    assert d["model_year"]==2023
    assert d["source_2026_Hynetwork_operator_terms_are_not_actual_2023_gas_supply"]
    assert d["supplier_contract_exit_connection_contract_both_missing"]
    assert d["native_BAFU_full_comparative_GWP"] is None
    assert not d["comparative_E_vs_ES_matched_service_permitted"]
    for mode,v in d["modes"].items():
        assert v["actual_connection_total_peak_HHV_kWh_h"] is None
        assert len(v["mathematical_boundary_cases"])==5
        assert all(not x["physical_supplier_verified"] and not x["full_lca_tea_eligible"]
                   for x in v["mathematical_boundary_cases"].values())

@pytest.mark.parametrize("edit",[
 lambda x: x.pop("supplier_kg_h"),
 lambda x: x["supplier_kg_h"].pop(),
 lambda x: x["transport_nomination_kg_h"].__setitem__(3,float("nan")),
 lambda x: x["station_capacity_kg_h"].__setitem__(3,-5),
 lambda x: x["product_quality_acceptable"].__setitem__(3,1),
 lambda x: x.update(timebase="2023-01-01-LOCAL-CLOCK-DST-ASSUMED"),
 lambda x: x.update(pressure_basis="Hynetwork-30-50-barg-NOT-customer-node"),
 lambda x: x.update(scenario_class="SIGNED_ACTUAL_PLANT_H2_SUPPLY_WITHOUT_EVIDENCE"),
])
def test_no_unchecked_8760_hour_or_signed_contract_fabrications(edit):
    p=_illustration("usable_service","EXACT_PEAK_FLOW_20BARA_PERFECT_UPTIME")
    edit(p)
    with pytest.raises(UnqualifiedContractEvidence):
        check_no_buffer_interface("usable_service",p)
