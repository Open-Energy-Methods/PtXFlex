"""Mathematical synthetic source-artifact structures; never historical results."""
import copy
import pytest
from ptxflex.f3_reconciled_evidence import (
    reconcile, ReconciliationError, E_SHA, ES_SHA, TARGET, FULL, MODES, CASES,
)


def fixtures():
    stages={}
    witnesses={}
    for m in MODES:
        for c in CASES:
            lo,hi=(10.,20.) if c=="E" else (0.,3.)
            cert={
               "schema_version":"ptxflex.f3_stage_a_adequacy_certificates.v1",
               "original_source_E_sha256":E_SHA,"original_source_EplusS_sha256":ES_SHA,
               "reference_service_kg":TARGET,"full_original_demand_kg":FULL,
               "not_a_matched_service_cost_or_environmental_comparison":True,
               "physical_installation_BOM_LCIA_TEA_complete":False,
               "cases":{m:{c:{
                   "shortfall_lower_bound_kg":lo,"shortfall_upper_bound_kg":hi,
                   "status":"BOUNDED_INCUMBENT_MINIMUM_UNPROVEN",
                   "positive_minimum_shortfall_proven":c=="E",
                   "annual_operating_cost_eur":None,"native_full_system_GWP_kgCO2e":None}}}}
            stages[(m,c)]=(cert,"c"*64)
        witnesses[m]=({
          "schema_version":"ptxflex.f3_2023_source_zero_additional_shortfall_witness.v1",
          "source_E_zip_sha256":E_SHA,"source_EplusS_zip_sha256":ES_SHA,
          "source_case":"E_plus_S","capacity_semantics":m,
          "reference_service_hour_count":8760,
          "reference_modelled_E_hourly_delivery_kg":TARGET,
          "source_original_full_H2_demand_kg":FULL,
          "source_E_hourly_reference_target_sha256":"a"*64,
          "pressure_screened_modelled_equal_hourly_delivery_verified":True,
          "stage_A_minimum_additional_shortfall_proven_kg":0.,
          "zero_additional_shortfall_witness_kg":0.,
          "not_a_cost_or_environmental_comparative_result":True,
          "native_incremental_storage_LCIA_or_complete_TEA":False,
          "installed_vessel_certification_or_physical_plant_validation":False,
          "independently_audited_maximum_residuals":{"energy":0.,"hydrogen":0.},
          "witness_audited_pressure_ranges":{"EOS_hourly_mass_bounds_imply_pressure_limits":True}}, "d"*64)
    return stages,witnesses


def test_combine_independent_hydrogen_screen_certificates():
    s,w=fixtures()
    x=reconcile(s,w)
    assert not x["matched_service_E_vs_EplusS_LCA_or_TEA_comparison_eligible"]
    for mode in MODES:
        cases=x["modes"][mode]["cases"]
        assert cases["E"]["minimum_additional_modelled_H2_shortfall_lower_bound_kg"]==10
        assert cases["E"]["minimum_additional_modelled_H2_shortfall_upper_bound_kg"]==20
        assert cases["E_plus_S"]["source_stageA_uncorrected_feasible_incumbent_shortfall_kg"]==3
        assert cases["E_plus_S"]["minimum_additional_modelled_H2_shortfall_upper_bound_kg"]==0
        assert cases["E_plus_S"]["zero_shortfall_feasible_and_optimal_proven"]


@pytest.mark.parametrize("mutator",[
    lambda s,w: s[("max_inventory","E")][0]["cases"]["max_inventory"]["E"].update(shortfall_lower_bound_kg=0),
    lambda s,w: s[("max_inventory","E_plus_S")][0]["cases"]["max_inventory"]["E_plus_S"].update(shortfall_lower_bound_kg=1),
    lambda s,w: w["max_inventory"][0].update(source_E_zip_sha256="0"*64),
    lambda s,w: w["usable_service"][0].update(source_E_hourly_reference_target_sha256="f"*64),
    lambda s,w: w["usable_service"][0].update(stage_A_minimum_additional_shortfall_proven_kg=2),
    lambda s,w: w["usable_service"][0]["independently_audited_maximum_residuals"].update(energy=1.),
    lambda s,w: s[("usable_service","E")][0]["cases"]["usable_service"]["E"].update(annual_operating_cost_eur=0),
])
def test_reject_false_shortage_proof_or_mismatched_historical_inputs(mutator):
    s,w=fixtures();mutator(s,w)
    with pytest.raises(ReconciliationError):
        reconcile(s,w)


def test_needs_all_six_certificates():
    s,w=fixtures()
    del s[("usable_service","E")]
    with pytest.raises(ReconciliationError,match="exactly four"):
        reconcile(s,w)
