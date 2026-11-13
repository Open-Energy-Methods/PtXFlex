"""Certified shortage intervals for F3 Stage A pressure-screened H2 dispatch.

Stage A minimizes additional unserved hydrogen against a frozen historical
E-delivered reference, not the original full industrial demand. For minimization
MILPs: max(0, dual bound) <= true optimum <= feasible incumbent. An
incumbent-only result is NOT a proven minimum. No cost/GWP conclusions follow.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SCHEMA = "ptxflex.f3_stage_a_adequacy_certificates.v1"
SOURCE_E = "069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051"
SOURCE_ES = "cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9"
SOURCE_TARGET_KG = 16335279.317376737
FULL_DEMAND_KG = 18250000.0
BOUND_TOL_KG = 0.01


class InvalidAdequacyCertificate(ValueError):
    """An upstream result cannot support an auditable shortage interval."""


def _number(value, name, *, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidAdequacyCertificate(name + " must be numeric")
    n = float(value)
    if not math.isfinite(n) or (minimum is not None and n < minimum):
        raise InvalidAdequacyCertificate(name + " is nonfinite/out of bounds")
    return n


def certify_stage_a(summary):
    if summary.get("source_E_sha256") != SOURCE_E or summary.get("source_EplusS_sha256") != SOURCE_ES:
        raise InvalidAdequacyCertificate("original source archive SHA mismatch")
    if summary.get("source_electricity_NL_A44_and_wind_ERA5_real_hydrogen_modelled") is not True:
        raise InvalidAdequacyCertificate("historical source provenance not confirmed")
    if summary.get("plant_validation") is not False or summary.get("complete_installation_BOM_LCA_and_TEA") is not False:
        raise InvalidAdequacyCertificate("screening result misrepresented as validated plant")
    target = _number(summary.get("source_hourly_E_delivered_target_kg"), "annual reference service", minimum=0)
    full = _number(summary.get("original_full_2023_H2_demand_kg"), "annual full demand", minimum=0)
    if not math.isclose(target, SOURCE_TARGET_KG, rel_tol=0, abs_tol=0.002) or not math.isclose(full, FULL_DEMAND_KG, rel_tol=0, abs_tol=0.002):
        raise InvalidAdequacyCertificate("original annual reference service changed")
    if target > full:
        raise InvalidAdequacyCertificate("source E delivered more than original demand")
    cases = summary.get("scenario_results")
    if not isinstance(cases, dict) or not cases:
        raise InvalidAdequacyCertificate("missing solved scenario results")
    output = {
        "schema_version": SCHEMA,
        "original_source_E_sha256": SOURCE_E,
        "original_source_EplusS_sha256": SOURCE_ES,
        "reference_service_kg": target,
        "full_original_demand_kg": full,
        "preexisting_source_E_shortfall_kg": full - target,
        "lower_bound_definition": "Valid MILP dual bound (or nonnegative slack) on optimal additional shortage",
        "upper_bound_definition": "Independently audited feasible MILP incumbent additional shortage",
        "model_assumptions_not_vendor_validated": True,
        "not_a_matched_service_cost_or_environmental_comparison": True,
        "physical_installation_BOM_LCIA_TEA_complete": False,
        "cases": {},
    }
    for mode, rows in cases.items():
        if mode not in ("max_inventory", "usable_service") or not isinstance(rows, dict) or not rows:
            raise InvalidAdequacyCertificate("unregistered physical capacity interpretation")
        result_cases = {}
        for case, r in rows.items():
            if case not in ("E", "E_plus_S") or not isinstance(r, dict):
                raise InvalidAdequacyCertificate("unregistered F3 case")
            status = r.get("status")
            if status == "NOT_CERTIFIED":
                if not isinstance(r.get("reason"), str) or not r["reason"]:
                    raise InvalidAdequacyCertificate("uncertified scenario must explain why")
                result_cases[case] = {
                    "status": "NOT_CERTIFIED",
                    "reason": r["reason"][:400],
                    "shortfall_lower_bound_kg": None,
                    "shortfall_upper_bound_kg": None,
                    "minimum_shortfall_certified": False,
                }
                continue
            expected = ("VERIFIED_STAGE_A_MIN_ADDITIONAL_SOURCE_SHORTFALL",
                        "FEASIBLE_INCUMBENT_NOT_PROVEN_MINIMUM")
            if status not in expected:
                raise InvalidAdequacyCertificate("LP or unknown result is not an executable MILP")
            certified = r.get("solver_optimal")
            if not isinstance(certified, bool) or certified != (status == expected[0]):
                raise InvalidAdequacyCertificate("contradictory MILP optimality or incumbent classification")
            gap = _number(r.get("solver_gap"), "solver relative MIP gap", minimum=0)
            if certified and gap > 1e-6 + 1e-10:
                raise InvalidAdequacyCertificate("unproven MILP gap labeled optimal")
            short = _number(r.get("additional_shortfall_kg"), "incumbent shortage", minimum=0)
            delivered = _number(r.get("achievable_annual_h2_under_screen_kg"), "incumbent delivered", minimum=0)
            if short > target + BOUND_TOL_KG or abs(short + delivered - target) > 1e-4:
                raise InvalidAdequacyCertificate("annual delivered-service mass closure failed")
            independent = r.get("audit", {}).get("independent_max_physical_residuals")
            pressures = r.get("audit", {}).get("pressure_EOS_bounds")
            if not isinstance(independent, dict) or not independent or not isinstance(pressures, dict):
                raise InvalidAdequacyCertificate("missing independently audited physics evidence")
            if any(_number(v, "physics residual", minimum=0) > 2e-4 for v in independent.values()):
                raise InvalidAdequacyCertificate("physical conservation check did not pass")
            if pressures.get("EOS_hourly_mass_bounds_imply_pressure_limits") is not True:
                raise InvalidAdequacyCertificate("EOS pressure certification missing")
            dual = r.get("solver_best_bound_unserved_kg")
            if dual is None:
                lower, basis = 0.0, "nonnegative_slack_only"
            else:
                dual = _number(dual, "MILP certified dual lower bound")
                lower, basis = max(0.0, dual), "solver_MIP_dual_bound"
            if lower > short + BOUND_TOL_KG:
                raise InvalidAdequacyCertificate("solver lower bound exceeds feasible incumbent")
            # For a zero-shortfall incumbent the nonnegative-slack bound proves
            # optimality without relying on any solver-reported relative gap.
            zero_proven = short <= 1e-7 and lower <= short + BOUND_TOL_KG
            result_cases[case] = {
                "status": "PROVEN_MINIMUM" if certified or zero_proven else "BOUNDED_INCUMBENT_MINIMUM_UNPROVEN",
                "original_solver_status": status,
                "shortfall_lower_bound_kg": min(lower, short),
                "shortfall_upper_bound_kg": short,
                "shortfall_optimality_interval_width_kg": max(0.0, short - lower),
                "lower_bound_basis": basis,
                "solver_reported_relative_MIP_gap": gap,
                "minimum_shortfall_certified": bool(certified or zero_proven),
                "positive_minimum_shortfall_proven": lower > BOUND_TOL_KG,
                "original_E_reference_delivery_lower_bound_kg": target - short,
                "original_E_reference_delivery_upper_bound_kg": target - min(lower, short),
                "full_original_demand_shortfall_lower_bound_kg": full - target + min(lower, short),
                "full_original_demand_shortfall_upper_bound_kg": full - target + short,
                "incumbent_shortfall_hours_only": r.get("shortfall_hour_count"),
                "annual_operating_cost_eur": None,
                "native_full_system_GWP_kgCO2e": None,
            }
        output["cases"][mode] = result_cases
    return output


def main():
    parser = argparse.ArgumentParser(description="Validate and bound source-locked Stage A shortage evidence")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    destination = Path(args.output)
    if destination.exists():
        raise FileExistsError("never overwrite prior source-derived adequacy certificates")
    source = json.loads(Path(args.input).read_text(encoding="utf-8"))
    certified = certify_stage_a(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(certified, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for mode, rows in certified["cases"].items():
        for case, row in rows.items():
            print(mode, case, row["status"], "additional H2 shortage interval (kg):",
                  row["shortfall_lower_bound_kg"], row["shortfall_upper_bound_kg"])


if __name__ == "__main__":
    main()
