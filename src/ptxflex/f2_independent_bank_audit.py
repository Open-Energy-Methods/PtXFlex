"""Independent algebraic F2 vessel-bank audit (no EOS calls or plant certification).

Uses independently supplied EOS densities, rather than reusing the production
bank-sizing implementation. The caller must independently establish density
provenance and pressure basis. Passing this audit is NOT F2 gate approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite


class BankAuditError(ValueError):
    pass


@dataclass(frozen=True)
class BankAudit:
    minimum_vessels: int
    per_vessel_gross_kg: float
    per_vessel_heel_kg: float
    per_vessel_working_kg: float
    total_gross_kg: float
    total_heel_kg: float
    total_working_kg: float
    target_semantics: str
    source_pressure_basis_confirmed: bool = False
    installed_equipment_complete: bool = False
    industrial_design_validated: bool = False


def independent_bank_audit(
    *, target_kg: float, free_volume_m3: float,
    density_at_max_kg_m3: float, density_at_min_kg_m3: float,
    capacity_semantics: str, reported_vessel_count: int
) -> BankAudit:
    """Check minimal integer vessel count and gross/heel/working conservation.

    Inputs are deliberately primitive: no published per-vessel nominal H2 mass
    is substituted for the independently evaluated pressure-swing inventory.
    """
    vals = (target_kg, free_volume_m3, density_at_max_kg_m3,
            density_at_min_kg_m3)
    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           or not isfinite(v) for v in vals):
        raise BankAuditError("finite numeric inputs required")
    if target_kg <= 0 or free_volume_m3 <= 0 or density_at_min_kg_m3 <= 0:
        raise BankAuditError("target, volume and residual density must be positive")
    if density_at_max_kg_m3 <= density_at_min_kg_m3:
        raise BankAuditError("maximum-pressure density must exceed minimum")
    if capacity_semantics not in ("max_inventory", "usable_service"):
        raise BankAuditError("explicit inventory semantics required")
    if isinstance(reported_vessel_count, bool) or not isinstance(reported_vessel_count, int):
        raise BankAuditError("integer vessel count required")
    gross = free_volume_m3 * density_at_max_kg_m3
    heel = free_volume_m3 * density_at_min_kg_m3
    working = gross - heel
    basis = gross if capacity_semantics == "max_inventory" else working
    minimum = ceil(target_kg / basis)
    if reported_vessel_count != minimum:
        raise BankAuditError(f"reported count {reported_vessel_count} != minimal {minimum}")
    total_gross = reported_vessel_count * gross
    total_heel = reported_vessel_count * heel
    total_working = reported_vessel_count * working
    if not total_gross > total_heel > 0:
        raise BankAuditError("nonphysical bank mass balance")
    if total_gross - total_heel < total_working - 1e-8 * total_gross:
        raise BankAuditError("mass balance violation")
    return BankAudit(minimum, gross, heel, working, total_gross, total_heel,
                     total_working, capacity_semantics)
