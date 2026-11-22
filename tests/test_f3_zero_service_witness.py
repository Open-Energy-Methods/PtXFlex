"""Contract/negative tests use mocks, never count as original 2023 dispatch proof."""
import pytest
import numpy as np
from scripts import f3_zero_service_witness_2023 as w
from ptxflex.f3_matched_ideal_benchmark import SOURCE_SHA, SourceLockedDispatchError


def sample_payload():
    target=np.full(8760,100.)
    params={"capacity_kg":40000.,"source_bafu_PEM_pressure_bar":30.,
            "source_pipeline_min_delivery_pressure_bar":20.}
    original={"registered_sha":SOURCE_SHA["E"],"wind":np.zeros(8760),
              "price":np.zeros(8760)}
    es={"registered_sha":SOURCE_SHA["E+S"]}
    return original,es,target,params,params


def test_reconciliation_witness_is_zero_optimally_by_nonnegative_shortfall(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(w,"load_matched_pilot",lambda *a:sample_payload())
    monkeypatch.setattr(w,"build_screened_pressure_duty",lambda *a,**kw:SimpleNamespace(
        vessel_id="I_200bar",gas_maximum_absolute_bar=200.,gas_minimum_absolute_bar=20.,
        vessel_count=1605,bank_empty_vessel_mass_kg=3852000.,gas_heel_kg=4425.,
        compressor_electrical_kwh_per_kg_charged=1.13655))
    audit={
        "strict_reference_hourly_delivery_profile_is_matched":True,
        "pressure_EOS_bounds":{"EOS_hourly_mass_bounds_imply_pressure_limits":True},
        "independent_max_physical_residuals":{"electrical":0.,"H2_delivered":0.,"storage":0.},
        "annual_service_h2_kg":876000.,"annual_compression_electricity_mwh":4.}
    monkeypatch.setattr(w,"solve_ideal_storage",lambda *a,**kw:{
        "solver_status":1,"pressure_vessel_eos_screened":True,
        "source_RVO_compressor_upper_pressure_work_included":True,
        "derived_audit":audit,"hourly_solved_states":np.zeros((8760,8)).tolist(),
        "modelled_hourly_delivered_kg":np.full(8760,100.).tolist(),
        "mip_relative_gap":0.9})
    z=w.certify_zero_shortfall_witness("a","b","max_inventory")
    assert z["stage_A_minimum_additional_shortfall_proven_kg"]==0
    assert z["witness_solver_status"]==1
    assert z["solver_cost_optimality_not_required_for_zero_shortfall_proof"]
    assert not z["native_incremental_storage_LCIA_or_complete_TEA"]


def test_wrong_capacity_interpretation_rejected_before_sources():
    with pytest.raises(SourceLockedDispatchError,match="unregistered"):
        w.certify_zero_shortfall_witness("a","b","nameplate_equals_usable")
