"""F2 inverse free-volume screen for a specified hydrogen service.

Equilibrium endpoint mass balance only. Pressure is absolute, and the
temperature bounds are hypothetical. This does not size an installed station,
certify vessels, establish transient withdrawal, or include compressors/BOP.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .f2_thermal_working_capacity import (
    ThermalCapacityError,
    screen_thermal_working_capacity,
)


@dataclass(frozen=True)
class RequiredFreeVolume:
    required_free_volume_m3: float
    target_usable_kg: float
    usable_kg_per_m3: float
    endpoint_equilibrium_only: bool = True
    certified_vessel_count: bool = False
    compressor_and_bop_included: bool = False
    native_lca_complete: bool = False


def solve_required_free_volume(
    *,
    target_usable_kg: float,
    maximum_pressure_bar_absolute: float,
    minimum_withdrawal_pressure_bar_absolute: float,
    reference_temperature_k: float,
    cold_temperature_k: float,
    hot_temperature_k: float,
) -> RequiredFreeVolume:
    """Find continuous free volume for the stated hot-fill/cold-heel endpoints.

    This is not a discrete vessel count: free volume is not external volume,
    vessel steel mass, station footprint, or certified installed capacity.
    """
    if (isinstance(target_usable_kg, bool)
            or not isinstance(target_usable_kg, (int, float))
            or not math.isfinite(target_usable_kg)
            or target_usable_kg <= 0):
        raise ThermalCapacityError("target_usable_kg must be positive finite")
    per_m3 = screen_thermal_working_capacity(
        free_volume_m3=1.0,
        maximum_pressure_bar_absolute=maximum_pressure_bar_absolute,
        minimum_withdrawal_pressure_bar_absolute=minimum_withdrawal_pressure_bar_absolute,
        reference_temperature_k=reference_temperature_k,
        cold_temperature_k=cold_temperature_k,
        hot_temperature_k=hot_temperature_k,
    ).conservative_usable_kg
    volume = target_usable_kg / per_m3
    if not math.isfinite(volume) or volume <= 0:
        raise ThermalCapacityError("required volume not representable")
    return RequiredFreeVolume(volume, target_usable_kg, per_m3)
