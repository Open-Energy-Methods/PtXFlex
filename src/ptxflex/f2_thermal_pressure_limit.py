"""F2 inverse pressure feasibility at explicit thermal endpoint states.

An equilibrium screening tool, not a certified design or dynamic trajectory.
All pressures are absolute. CoolProp is mandatory; no ideal-gas substitution.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from .f2_thermal_working_capacity import ThermalCapacityError, screen_thermal_working_capacity

@dataclass(frozen=True)
class WithdrawalPressureLimit:
    maximum_permissible_heel_bar_absolute: float
    usable_kg_at_limit: float
    target_usable_kg: float
    pressure_tolerance_bar: float
    equilibrium_endpoint_only: bool = True
    equipment_qualified: bool = False
    compressor_and_bop_included: bool = False
    native_lca_complete: bool = False

def solve_maximum_heel_pressure(*, target_usable_kg: float,
    free_volume_m3: float, maximum_pressure_bar_absolute: float,
    minimum_search_pressure_bar_absolute: float,
    reference_temperature_k: float, cold_temperature_k: float,
    hot_temperature_k: float, pressure_tolerance_bar: float = 1e-5
) -> WithdrawalPressureLimit:
    """Highest heel pressure supporting target capacity in assumed hot/cold states.

    Rejects targets not attainable at the stated minimum pressure; never
    silently enlarges vessels or reduces the requested hydrogen service.
    """
    v = (target_usable_kg, free_volume_m3, maximum_pressure_bar_absolute,
         minimum_search_pressure_bar_absolute, reference_temperature_k,
         cold_temperature_k, hot_temperature_k, pressure_tolerance_bar)
    if any(isinstance(x, bool) or not isinstance(x, (int, float))
           or not math.isfinite(x) or x <= 0 for x in v):
        raise ThermalCapacityError("all inputs must be positive finite numbers")
    if minimum_search_pressure_bar_absolute >= maximum_pressure_bar_absolute:
        raise ThermalCapacityError("pressure search interval is empty")
    if not cold_temperature_k <= reference_temperature_k <= hot_temperature_k:
        raise ThermalCapacityError("reference temperature outside thermal envelope")
    def usable(p):
        return screen_thermal_working_capacity(
            free_volume_m3=free_volume_m3,
            maximum_pressure_bar_absolute=maximum_pressure_bar_absolute,
            minimum_withdrawal_pressure_bar_absolute=p,
            reference_temperature_k=reference_temperature_k,
            cold_temperature_k=cold_temperature_k,
            hot_temperature_k=hot_temperature_k).conservative_usable_kg
    low = minimum_search_pressure_bar_absolute
    at_low = usable(low)
    if target_usable_kg > at_low:
        raise ThermalCapacityError("target infeasible at minimum allowed heel pressure")
    # Exact feasibility is required: a relative allowance here could return a\n    # pressure with less H2 than the requested service, especially at the\n    # minimum heel boundary. Solver pressure tolerance is separate.\n    # EOS density is increasing with pressure in the specified single-phase gas
    # domain. A monotonicity check rejects an unexpected EOS region.
    high = maximum_pressure_bar_absolute
    for _ in range(100):
        if high - low <= pressure_tolerance_bar:
            break
        mid = (low + high) / 2
        try:
            at_mid = usable(mid)
        except ThermalCapacityError as exc:
            if "no positive withdrawable" not in str(exc):
                raise
            at_mid = 0.0
        if at_mid > at_low * (1 + 1e-9):
            raise ThermalCapacityError("nonmonotone EOS capacity; no certified inverse")
        if at_mid >= target_usable_kg:
            low, at_low = mid, at_mid
        else:
            high = mid
    return WithdrawalPressureLimit(low, at_low, target_usable_kg, pressure_tolerance_bar)
