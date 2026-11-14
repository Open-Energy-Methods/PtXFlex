"""Actual registered 2023 H2 source-based duty and candidate literature gates."""
import copy
import json
import pytest
from pathlib import Path

from ptxflex.f3_backup_route_screen import (
    evaluate_physical_routes,load_register,CandidateNotVerified,SOURCE_REGISTRY,
)


def test_source_registered_h2_piping_entry_not_exit_design_basis():
    z=evaluate_physical_routes()
    assert z["schema_version"]=="ptxflex.f3_prospective_backup_delivery_design_basis.v1"
    assert z["reference_weather_and_wholesale_price_year"]==2023
    assert z["external_network_architecture_source_year"]==2026
    assert z["prospective_2026_infrastructure_is_not_observed_2023_site_supply"]
    assert not z["physically_verified_common_hourly_service"]
    for mode in ("max_inventory","usable_service"):
        d=z["modes"][mode]
        assert d["source_stageA_proven_minimum_additional_shortage_lower_bound_kg"]>0
        assert not d["environmental_and_tea_comparison_eligible"]
        p=d["pathways"]["contracted_dedicated_H2_pipeline"]
        assert p["hynetwork_2026_general_network_entry_minimum_bar_gauge"]==30.
        assert p["the_30barg_value_is_not_site_customer_exit_pressure"]
        assert p["customer_guaranteed_min_exit_pressure_bar_absolute"] is None
        assert p["customer_h2_impurity_certification"] is None


def test_reference_trailer_optimistic_payload_equivalents_not_vehicle_approvals():
    z=evaluate_physical_routes()
    gross=z["modes"]["max_inventory"]["pathways"]["gaseous_tube_trailer_delivery"]
    usable=z["modes"]["usable_service"]["pathways"]["gaseous_tube_trailer_delivery"]
    assert gross["optimistic_payload_equivalents_at_900kg_per_nominal_load_annual"]==74
    assert gross["optimistic_payload_equivalents_at_900kg_per_nominal_load_peak_24h"]==3
    assert gross["optimistic_payload_equivalents_at_900kg_per_nominal_load_peak_hour"]==2
    assert usable["optimistic_payload_equivalents_at_900kg_per_nominal_load_annual"]==5
    assert usable["optimistic_payload_equivalents_at_900kg_per_nominal_load_peak_24h"]==1
    assert usable["optimistic_payload_equivalents_at_900kg_per_nominal_load_peak_hour"]==1
    assert gross["payload_equivalents_are_not_actual_required_vehicle_trips"]
    assert gross["recovered_usable_H2_from_tank_down_to_20bar_absolute_kg"] is None
    assert usable["actual_deliverable_peak_flow_kg_h"] is None


@pytest.mark.parametrize("f",[
    lambda r:r.update(site_connection_and_contract=True),
    lambda r:r.update(customer_guaranteed_min_exit_pressure_bar_absolute=30),
    lambda r:r.update(external_supply_cost_EUR2023_per_kg=0),
    lambda r:r.update(externally_sourced_h2_specific_GWP_kgCO2e_per_kg=0),
    lambda r:r.update(2023_site_transport_availability=True),
    lambda r:r.update(matched_service_end_use_qualified=True),
    lambda r:r.update(pipeline_reference_not_exit_guarantee=False),
    lambda r:r.update(fixed_dispatch_model_delivery_pressure_bar_absolute=20.2),
    lambda r:r.update(us_doe_composite_trailer_benchmark_max_nominal_payload_kg=1500),
    lambda r:r["source_reference_safety"].update(operator_30_to_50_barg_is_network_entry_not_verified_customer_exit=False),
])
def test_unauthorized_site_supply_or_cost_emissions_are_rejected(tmp_path,f):
    reg=json.loads(SOURCE_REGISTRY.read_text())
    f(reg)
    p=tmp_path/"f3_register.json";p.write_text(json.dumps(reg))
    with pytest.raises(CandidateNotVerified):
        load_register(p)


def test_source_reconciliation_sha_enforced_on_replaced_envelope(tmp_path):
    from ptxflex.f3_backup_route_screen import RESULTS
    src=RESULTS/"F3_2023_original_E_source_hypothetical_backup_usable_service.json"
    out=tmp_path/src.name
    x=json.loads(src.read_text());x["single_incumbent_hypothetical_topup_annual_kg"]=0
    out.write_text(json.dumps(x))
    with pytest.raises((CandidateNotVerified,FileNotFoundError)):
        evaluate_physical_routes(results_directory=tmp_path)
