"""F2 source-pressure-basis ambiguity sensitivity, not a certified vessel rating.

The IJHE reference reports a nominal pressure in bar without a reconciled
gauge/absolute convention in this programme. This module compares two
explicit *hypotheses* for that reference: 200 bar(a) and 200 bar(g) at a
declared 1.01325 bar ambient. It never alters the source vessel registry,
frozen 2023 dispatch or installed equipment assumptions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from .hydrogen_physics import hydrogen_density_kg_m3
from .f2_bank_count_independent import independent_bank_count
from .storage_reference_vessels import PUBLISHED_VESSELS

@dataclass(frozen=True)
class PressureBasisCase:
    pressure_hypothesis: str
    upper_absolute_bar: float
    lower_absolute_bar: float
    temperature_k: float
    capacity_semantics: str
    target_kg: float
    vessel_count: int
    gross_hydrogen_kg: float
    heel_hydrogen_kg: float
    withdrawable_hydrogen_kg: float
    empty_reference_vessel_hardware_kg: float
    certified_design: bool = False
    installed_station_mass_kg: None = None
    native_manufacturing_gwp_kg_co2e: None = None

def pressure_basis_sensitivity(*, vessel_id="I_200bar", target_kg=20_000.,
                               lower_absolute_bar=20., temperature_k=313.,
                               ambient_absolute_bar=1.01325,
                               capacity_semantics="usable_service"):
    """Compare hypotheses with fixed absolute outlet gate and constant T.

    Only the nominal *upper* pressure interpretation changes. No claim that
    gauge pressure is the correct interpretation or vendor approval.
    """
    if vessel_id not in PUBLISHED_VESSELS:
        raise ValueError("unknown reference vessel")
    if capacity_semantics not in ("max_inventory", "usable_service"):
        raise ValueError("invalid capacity semantics")
    from math import isfinite
    values=(target_kg,lower_absolute_bar,temperature_k,ambient_absolute_bar)
    if not all(isinstance(v,(float,int)) and not isinstance(v,bool) and isfinite(v) and v>0 for v in values):
        raise ValueError("inputs must be positive finite numeric quantities")
    vessel=PUBLISHED_VESSELS[vessel_id]
    if lower_absolute_bar>=vessel.max_reference_pressure_bar:
        raise ValueError("withdrawal pressure must be below both upper hypotheses")
    cases=[]
    for label,pmax in (("nominal_bar_assumed_absolute",vessel.max_reference_pressure_bar),
                       ("nominal_bar_assumed_gauge",vessel.max_reference_pressure_bar+ambient_absolute_bar)):
        rho_hi=hydrogen_density_kg_m3(pmax,temperature_k)
        rho_lo=hydrogen_density_kg_m3(lower_absolute_bar,temperature_k)
        cert=independent_bank_count(
            target_kg=target_kg,vessel_volume_m3=vessel.internal_volume_m3,
            rho_upper_kg_m3=rho_hi,rho_lower_kg_m3=rho_lo,
            empty_vessel_mass_kg=vessel.empty_vessel_mass_kg,
            semantics=capacity_semantics)
        cases.append(asdict(PressureBasisCase(
            pressure_hypothesis=label,upper_absolute_bar=pmax,
            lower_absolute_bar=lower_absolute_bar,temperature_k=temperature_k,
            capacity_semantics=capacity_semantics,target_kg=target_kg,
            vessel_count=cert.actual_vessels,
            gross_hydrogen_kg=float(cert.gross_mass_kg),
            heel_hydrogen_kg=float(cert.heel_mass_kg),
            withdrawable_hydrogen_kg=float(cert.withdrawable_mass_kg),
            empty_reference_vessel_hardware_kg=float(cert.empty_vessel_hardware_kg))))
    return {
        "schema_version":"ptxflex.f2.pressure_basis_ambiguity.v1",
        "reference_doi":vessel.original_source_doi,
        "reference_vessel_id":vessel_id,
        "ambient_absolute_bar_assumption":ambient_absolute_bar,
        "published_pressure_basis_resolved":False,
        "source_model_modified":False,
        "certified_installed_storage":False,
        "complete_lca":False,
        "cases":cases,
        "delta_gauge_minus_absolute_vessels":cases[1]["vessel_count"]-cases[0]["vessel_count"],
        "interpretation":"Two conditional screening hypotheses only; neither is a verified OEM rating."
    }
