"""Reconcile four certified 2023 Stage A shortage bounds with two zero-service witnesses.

All six derived files are checked against their pinned source models and each
other. The pairwise 20t/40t pressure-screened systems DO NOT deliver equal
reference service, so this report cannot authorize comparative LCA or cost.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

E_SHA = "069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051"
ES_SHA = "cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9"
TARGET = 16335279.317376737
FULL = 18250000.0
MODES = ("max_inventory", "usable_service")
CASES = ("E", "E_plus_S")


class ReconciliationError(ValueError):
    pass


def _finite(x, name):
    if isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x):
        raise ReconciliationError(name + " must be a finite real number")
    return float(x)


def _read(path):
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def reconcile(stage_a, witnesses):
    """stage_a[(mode,case)] = (dict, SHA); witnesses[mode]=(dict,SHA)."""
    if set(stage_a) != {(m,c) for m in MODES for c in CASES} or set(witnesses) != set(MODES):
        raise ReconciliationError("exactly four original-source shortage certificates and two witnesses are required")
    report = {
        "schema_version": "ptxflex.f3_2023_pressure_adequacy_reconciled.v1",
        "source_original_E_zip_sha256": E_SHA,
        "source_original_EplusS_zip_sha256": ES_SHA,
        "reference_E_delivered_hourly_target_total_kg": TARGET,
        "full_original_2023_demand_total_kg": FULL,
        "original_E_modelled_source_shortfall_before_pressure_kg": FULL - TARGET,
        "first_modelled_reference_service_is_not_original_full_contract": True,
        "laboratory_or_vendor_equipment_validation": False,
        "full_system_native_BAFU_GWP_or_TEA_available": False,
        "matched_service_E_vs_EplusS_LCA_or_TEA_comparison_eligible": False,
        "pressure_screen_research_only": True,
        "stageA_certificate_input_sha256": {},
        "independent_full_service_witness_sha256": {},
        "modes": {},
    }
    reference_profile_sha = None
    for mode in MODES:
        witness, witness_sha = witnesses[mode]
        if witness.get("schema_version") != "ptxflex.f3_2023_source_zero_additional_shortfall_witness.v1":
            raise ReconciliationError("wrong independent full-service witness schema")
        if (witness.get("source_E_zip_sha256") != E_SHA
                or witness.get("source_EplusS_zip_sha256") != ES_SHA
                or witness.get("source_case") != "E_plus_S"
                or witness.get("capacity_semantics") != mode):
            raise ReconciliationError("full-service witness differs from source/case/capacity scenario")
        if (witness.get("reference_service_hour_count") != 8760
                or abs(_finite(witness.get("reference_modelled_E_hourly_delivery_kg"), "witness service")-TARGET) > .002
                or _finite(witness.get("source_original_full_H2_demand_kg"), "source full demand") != FULL):
            raise ReconciliationError("witness does not apply to original target hours or demand")
        profile_sha = witness.get("source_E_hourly_reference_target_sha256")
        if not isinstance(profile_sha, str) or len(profile_sha) != 64:
            raise ReconciliationError("missing hourly reference profile fingerprint")
        if reference_profile_sha is not None and reference_profile_sha != profile_sha:
            raise ReconciliationError("two storage interpretations used different hourly H2 reference profiles")
        reference_profile_sha = profile_sha
        if (witness.get("pressure_screened_modelled_equal_hourly_delivery_verified") is not True
                or witness.get("stage_A_minimum_additional_shortfall_proven_kg") != 0.0
                or witness.get("zero_additional_shortfall_witness_kg") != 0.0
                or witness.get("not_a_cost_or_environmental_comparative_result") is not True
                or witness.get("native_incremental_storage_LCIA_or_complete_TEA") is not False
                or witness.get("installed_vessel_certification_or_physical_plant_validation") is not False):
            raise ReconciliationError("unsupported zero-shortfall or LCA/TEA claim in witness")
        residuals = witness.get("independently_audited_maximum_residuals")
        pressure = witness.get("witness_audited_pressure_ranges")
        if not isinstance(residuals, dict) or not residuals or any(
                _finite(x,"witness physical residual") > 2e-4 or x < 0 for x in residuals.values()):
            raise ReconciliationError("witness conservation verification failed")
        if not isinstance(pressure, dict) or pressure.get("EOS_hourly_mass_bounds_imply_pressure_limits") is not True:
            raise ReconciliationError("witness actual real-gas EOS pressure check missing")
        report["independent_full_service_witness_sha256"][mode] = witness_sha
        results={}
        for case in CASES:
            cert, source_sha = stage_a[(mode,case)]
            if (cert.get("schema_version") != "ptxflex.f3_stage_a_adequacy_certificates.v1"
                    or cert.get("original_source_E_sha256") != E_SHA
                    or cert.get("original_source_EplusS_sha256") != ES_SHA
                    or cert.get("not_a_matched_service_cost_or_environmental_comparison") is not True
                    or cert.get("physical_installation_BOM_LCIA_TEA_complete") is not False):
                raise ReconciliationError("incompatible Stage A independent certificate")
            if abs(_finite(cert.get("reference_service_kg"), "Stage A target")-TARGET)>0.002 or _finite(
                    cert.get("full_original_demand_kg"),"Stage A full demand")!=FULL:
                raise ReconciliationError("Stage A original 2023 source delivery changed")
            if set(cert.get("cases", {})) != {mode} or set(cert["cases"][mode]) != {case}:
                raise ReconciliationError("one and only one matching independently executed scenario per source artifact")
            r=cert["cases"][mode][case]
            lo=_finite(r.get("shortfall_lower_bound_kg"),"certified MILP lower")
            hi=_finite(r.get("shortfall_upper_bound_kg"),"certified MILP upper")
            if lo < 0 or hi < 0 or lo > hi+.01 or hi>TARGET+.01:
                raise ReconciliationError("mathematically impossible shortage bound")
            if r.get("native_full_system_GWP_kgCO2e") is not None or r.get("annual_operating_cost_eur") is not None:
                raise ReconciliationError("Stage A not an LCA/TEA cost result")
            if case == "E":
                if r.get("status") not in ("BOUNDED_INCUMBENT_MINIMUM_UNPROVEN","PROVEN_MINIMUM"):
                    raise ReconciliationError("E needs certified feasible MILP interval")
                if lo<=.01 or r.get("positive_minimum_shortfall_proven") is not True:
                    raise ReconciliationError("20t physical screen positive minimum shortage not proven")
                final_lo,final_hi=lo,hi
                proof="HiGHS MILP dual bound plus independently audited feasible incumbent"
            else:
                if lo > .01:
                    raise ReconciliationError("solver reports positive lower shortage contrary to independent zero-service witness")
                if r.get("status") not in ("BOUNDED_INCUMBENT_MINIMUM_UNPROVEN","PROVEN_MINIMUM"):
                    raise ReconciliationError("40t Stage A case was not numerically certified")
                final_lo=final_hi=0.0
                proof="independently audited full-hourly-service zero-shortfall witness; Stage A nonnegative slack"
            results[case]={
                "minimum_additional_modelled_H2_shortfall_lower_bound_kg": final_lo,
                "minimum_additional_modelled_H2_shortfall_upper_bound_kg": final_hi,
                "minimum_positive_shortfall_proven": final_lo > .01,
                "zero_shortfall_feasible_and_optimal_proven": final_hi == 0,
                "original_full_demand_shortfall_lower_bound_kg": FULL-TARGET+final_lo,
                "original_full_demand_shortfall_upper_bound_kg": FULL-TARGET+final_hi,
                "proof_basis": proof,
                "source_stageA_uncorrected_feasible_incumbent_shortfall_kg": hi,
                "native_full_plant_GWP_kgCO2e": None,
                "complete_project_annual_cost_eur": None,
            }
            report["stageA_certificate_input_sha256"][mode+"_"+case] = source_sha
        report["modes"][mode] = {
            "cases": results,
            "mathematically_proven_unequal_delivery_service": True,
            "eligible_for_direct_20t_vs_40t_cost_or_GWP_comparison": False,
            "service_equivalence_option_requires_sourced_backup_or_common_target": True,
        }
    report["reference_profile_fingerprint_sha256"] = reference_profile_sha
    return report


def main():
    p=argparse.ArgumentParser()
    for m in MODES:
        for c in CASES:
            p.add_argument("--stageA-"+m+"-"+c,required=True,dest=m+"_"+c)
        p.add_argument("--witness-"+m,required=True,dest="witness_"+m)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    output=Path(a.output)
    if output.exists(): raise FileExistsError("never overwrite a completed source-linked F3 study")
    stages={(m,c):_read(getattr(a,m+"_"+c)) for m in MODES for c in CASES}
    witnesses={m:_read(getattr(a,"witness_"+m)) for m in MODES}
    report=reconcile(stages,witnesses)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    for mode,d in report["modes"].items():
        for case,r in d["cases"].items():
            print("RECONCILED", mode,case,"optimal minimum additional shortage bounds (kg):",
                  r["minimum_additional_modelled_H2_shortfall_lower_bound_kg"],
                  r["minimum_additional_modelled_H2_shortfall_upper_bound_kg"])
    print("DIRECT E / E+S cost and GWP comparison BLOCKED: different modelled delivery service")


if __name__=="__main__":main()
