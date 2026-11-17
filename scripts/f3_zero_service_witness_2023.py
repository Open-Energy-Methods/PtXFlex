"""Independent zero-additional-shortfall witness for source-based 2023 F3.

A verified full-hourly-service dispatch, with every pressure and H2/electric
constraint audited, proves the Stage A minimum shortage is zero because Stage A
shortage is constrained nonnegative. Optimizing wholesale settlement is only
a way to find a feasible witness; its cost optimality is not needed to prove
zero shortage. This is a modelled pressure-screen witness, not real plant
adequacy or full 50t/day service.
"""
from __future__ import annotations

from dataclasses import asdict
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from ptxflex.f3_matched_ideal_benchmark import (
    load_matched_pilot, solve_ideal_storage, SourceLockedDispatchError, SOURCE_SHA
)
from ptxflex.pressure_storage_duty import build_screened_pressure_duty


def certify_zero_shortfall_witness(E_original, ES_original, mode, *, limit_seconds=300):
    if mode not in ("max_inventory", "usable_service"):
        raise SourceLockedDispatchError("unregistered pressure bank capacity semantics")
    original_E, original_ES, target, pE, pES = load_matched_pilot(E_original, ES_original)
    params = pES
    if original_E["registered_sha"] != SOURCE_SHA["E"] or original_ES["registered_sha"] != SOURCE_SHA["E+S"]:
        raise SourceLockedDispatchError("frozen real-source 2023 evidence changed")
    duty = build_screened_pressure_duty(
        "I_200bar", params["capacity_kg"], capacity_semantics=mode,
        source_PEM_outlet_bar_absolute=params["source_bafu_PEM_pressure_bar"],
        delivery_min_bar_absolute=params["source_pipeline_min_delivery_pressure_bar"]
    )
    solved = solve_ideal_storage(
        original_E["wind"], original_E["price"], target, params,
        time_limit_s=limit_seconds, pressure_duty=duty
    )
    if solved["solver_status"] not in (0, 1):
        raise SourceLockedDispatchError("full-year feasibility witness solver status invalid")
    audit = solved["derived_audit"]
    if (not solved["pressure_vessel_eos_screened"]
            or not solved["source_RVO_compressor_upper_pressure_work_included"]
            or audit["strict_reference_hourly_delivery_profile_is_matched"] is not True
            or audit["pressure_EOS_bounds"]["EOS_hourly_mass_bounds_imply_pressure_limits"] is not True):
        raise SourceLockedDispatchError("full-hourly-service EOS witness not independently verified")
    residuals = audit["independent_max_physical_residuals"]
    if not residuals or max(residuals.values()) > 2e-4:
        raise SourceLockedDispatchError("zero shortfall witness violates independent conservation")
    x = np.asarray(solved["hourly_solved_states"], dtype=float)
    delivered = np.asarray(solved["modelled_hourly_delivered_kg"], dtype=float)
    if x.shape != (8760, 8) or delivered.shape != (8760,) or not np.allclose(delivered, target, atol=0, rtol=0):
        raise SourceLockedDispatchError("full-year strict hour-by-hour 2023 service mismatch")
    if not math.isclose(audit["annual_service_h2_kg"], float(np.sum(target)), rel_tol=0, abs_tol=1e-4):
        raise SourceLockedDispatchError("annual service witness mismatch")
    return {
        "schema_version": "ptxflex.f3_2023_source_zero_additional_shortfall_witness.v1",
        "source_E_zip_sha256": SOURCE_SHA["E"],
        "source_EplusS_zip_sha256": SOURCE_SHA["E+S"],
        "source_E_hourly_reference_target_sha256": hashlib.sha256(target.tobytes()).hexdigest(),
        "reference_service_hour_count": 8760,
        "reference_modelled_E_hourly_delivery_kg": float(np.sum(target)),
        "source_original_full_H2_demand_kg": 18250000.0,
        "source_case": "E_plus_S",
        "capacity_semantics": mode,
        "source_vessel_id": duty.vessel_id,
        "screening_pressure_max_bar_absolute": duty.gas_maximum_absolute_bar,
        "screening_pressure_min_bar_absolute": duty.gas_minimum_absolute_bar,
        "physical_vessel_count": duty.vessel_count,
        "vessel_empty_equipment_mass_kg": duty.bank_empty_vessel_mass_kg,
        "EOS_heel_gas_kg": duty.gas_heel_kg,
        "compressor_electrical_kwh_per_kg_charged": duty.compressor_electrical_kwh_per_kg_charged,
        "source_time_series_hashes_not_measured_H2": True,
        "pressure_screened_modelled_equal_hourly_delivery_verified": True,
        "zero_additional_shortfall_witness_kg": 0.0,
        "stage_A_minimum_additional_shortfall_proven_kg": 0.0,
        "proof_logic": "feasible 8760h fixed-service MILP with identical constraints implies Stage A shortage=0, and shortage >=0",
        "full_original_50t_per_day_service_met": False,
        "native_incremental_storage_LCIA_or_complete_TEA": False,
        "installed_vessel_certification_or_physical_plant_validation": False,
        "solver_cost_optimality_not_required_for_zero_shortfall_proof": True,
        "witness_solver_status": solved["solver_status"],
        "witness_cost_mip_gap": solved["mip_relative_gap"],
        "independently_audited_maximum_residuals": residuals,
        "witness_audited_pressure_ranges": audit["pressure_EOS_bounds"],
        "witness_compressor_electricity_MWh": audit["annual_compression_electricity_mwh"],
        "not_a_cost_or_environmental_comparative_result": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--E", required=True)
    parser.add_argument("--ES", required=True)
    parser.add_argument("--mode", required=True, choices=("max_inventory", "usable_service"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--time-limit", type=float, default=300)
    args = parser.parse_args()
    dest=Path(args.output)
    if dest.exists():
        raise FileExistsError("never overwrite an existing source-derived pressure witness")
    witness=certify_zero_shortfall_witness(
        args.E,args.ES,args.mode,limit_seconds=args.time_limit)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(witness,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("VERIFIED 2023 modelled E+S",args.mode,"zero additional shortage witness",
          witness["stage_A_minimum_additional_shortfall_proven_kg"])


if __name__ == "__main__":
    main()
