"""Synthetic 8760-hour traces only; genuine source handled by hash-locked CI."""
import copy
import numpy as np
import pytest
from ptxflex.f3_backup_hourly_envelope import (
    source_hourly_backup_envelope, BackupEnvelopeError,
    TARGET,FULL,SOURCE_E,SOURCE_ES,
)


def fixture():
    a=[0.]*8760
    a[0:3]=[1.,2.,3.]
    a[100]=4.
    lo,hi=3.,10.
    cert={
        "schema_version":"ptxflex.f3_stage_a_adequacy_certificates.v1",
        "original_source_E_sha256":SOURCE_E,
        "original_source_EplusS_sha256":SOURCE_ES,
        "reference_service_kg":TARGET,"full_original_demand_kg":FULL,
        "physical_installation_BOM_LCIA_TEA_complete":False,
        "not_a_matched_service_cost_or_environmental_comparison":True,
        "cases":{"max_inventory":{"E":{
            "status":"BOUNDED_INCUMBENT_MINIMUM_UNPROVEN",
            "minimum_shortfall_certified":False,
            "positive_minimum_shortfall_proven":True,
            "shortfall_lower_bound_kg":lo,"shortfall_upper_bound_kg":hi,
            "incumbent_shortfall_hours_only":4,
            "annual_operating_cost_eur":None,
            "native_full_system_GWP_kgCO2e":None}}}
    }
    trace={"derived_source_not_original_raw_prices_or_wind":True,
           "source_E_delivered_reference_profile_is_modelled":True,
           "hourly_additional_shortfall_kg":a}
    return cert,trace


def test_source_case_restore_requires_declared_external_backup_not_fake_LCA():
    c,t=fixture()
    r=source_hourly_backup_envelope(c,t,"max_inventory")
    assert r["stageA_original_MILP_min_shortage_certified_lower_bound_kg"]==3
    assert r["single_incumbent_hypothetical_topup_annual_kg"]==10
    assert r["single_incumbent_hypothetical_topup_max_kg_per_hour"]==4
    assert r["single_incumbent_hypothetical_topup_24h_peak_kg"]==6
    assert r["single_incumbent_hypothetical_topup_occupied_hours"]==4
    assert r["single_incumbent_contiguous_event_count"]==2
    assert r["single_incumbent_longest_event_hours"]==3
    assert not r["external_H2_pressure_regulation_and_transport_verified"]
    assert r["incremental_backup_H2_kgCO2e_per_kg"] is None
    assert not r["matched_service_LCA_TEA_comparison_permitted"]


@pytest.mark.parametrize("mutate",[
    lambda c,t:c.update(original_source_E_sha256="bad"),
    lambda c,t:c.update(reference_service_kg=17_000_000),
    lambda c,t:c["cases"]["max_inventory"]["E"].update(shortfall_lower_bound_kg=0),
    lambda c,t:c["cases"]["max_inventory"]["E"].update(shortfall_upper_bound_kg=12),
    lambda c,t:c["cases"]["max_inventory"]["E"].update(incumbent_shortfall_hours_only=3),
    lambda c,t:c["cases"]["max_inventory"]["E"].update(annual_operating_cost_eur=0),
    lambda c,t:c["cases"]["max_inventory"]["E"].update(status="PROVEN_MINIMUM"),
    lambda c,t:t.update(derived_source_not_original_raw_prices_or_wind=False),
    lambda c,t:t["hourly_additional_shortfall_kg"].append(5.),
    lambda c,t:t["hourly_additional_shortfall_kg"].__setitem__(10,float("nan")),
    lambda c,t:t["hourly_additional_shortfall_kg"].__setitem__(100,-10.),
])
def test_reject_tampered_or_synthetic_as_real_pressure_backup(mutate):
    c,t=fixture();mutate(c,t)
    with pytest.raises(BackupEnvelopeError):
        source_hourly_backup_envelope(c,t,"max_inventory")


def test_source_case_semantics_and_20tonne_only_enforced():
    c,t=fixture()
    with pytest.raises(BackupEnvelopeError,match="capacity semantics"):
        source_hourly_backup_envelope(c,t,"unknown")
    with pytest.raises(BackupEnvelopeError,match="20t"):
        source_hourly_backup_envelope(c,t,"usable_service")
