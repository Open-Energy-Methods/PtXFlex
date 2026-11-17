"""F2 conservative two-temperature H2 working-capacity screening.

At a fixed vessel free volume, a hot maximum-pressure fill has less H2
than an isothermal reference; a cold minimum-pressure withdrawal heel retains
more H2. Their difference is a conservative *equilibrium endpoint* capacity
screen, not a thermodynamic trajectory or guaranteed transient bound.

No temperature extrema are inferred from a plant or manufacturer. The user
must supply hypothetical bounds. No equipment certification, pressure-drop,
heat-transfer, fill-rate, compressor or station LCA is implied.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


class ThermalCapacityError(ValueError):
    """Invalid physical assumptions or unavailable real-gas EOS."""


@dataclass(frozen=True)
class ThermalCapacityScreen:
    reference_usable_kg: float
    hot_fill_gross_kg: float
    cold_withdrawal_heel_kg: float
    conservative_usable_kg: float
    loss_vs_isothermal_kg: float
    loss_fraction: float
    temperature_range_k: tuple[float, float]
    endpoint_equilibrium_only: bool = True
    transient_validated: bool = False
    compressor_included: bool = False
    certified_station: bool = False
    native_lca_complete: bool = False


def screen_thermal_working_capacity(
    *, free_volume_m3: float, maximum_pressure_bar_absolute: float,
    minimum_withdrawal_pressure_bar_absolute: float,
    reference_temperature_k: float, cold_temperature_k: float,
    hot_temperature_k: float,
) -> ThermalCapacityScreen:
    """Real-gas hydrogen density screen at two independent thermal endpoints.

    The cold heel and hot fill are separate possible states, not simultaneous
    states. If the cold heel exceeds the hot fill inventory, reject the
    specified pressure/temperature service as having no positive capacity.
    """
    values = (free_volume_m3, maximum_pressure_bar_absolute,
              minimum_withdrawal_pressure_bar_absolute,
              reference_temperature_k, cold_temperature_k, hot_temperature_k)
    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           or not math.isfinite(v) or v <= 0 for v in values):
        raise ThermalCapacityError("all physical inputs must be finite positive numbers")
    if not minimum_withdrawal_pressure_bar_absolute < maximum_pressure_bar_absolute:
        raise ThermalCapacityError("withdrawal pressure must be below maximum pressure")
    if not cold_temperature_k <= reference_temperature_k <= hot_temperature_k:
        raise ThermalCapacityError("reference temperature must lie within cold/hot bounds")
    try:
        from CoolProp.CoolProp import PropsSI
    except ImportError as exc:
        raise ThermalCapacityError("CoolProp hydrogen EOS required; no ideal-gas fallback") from exc

    def inventory(p_bar: float, t_k: float) -> float:
        try:
            rho = float(PropsSI("Dmass", "P", p_bar * 1e5, "T", t_k, "Hydrogen"))
        except (ValueError, OverflowError) as exc:
            raise ThermalCapacityError("hydrogen EOS state unavailable") from exc
        if not math.isfinite(rho) or rho <= 0:
            raise ThermalCapacityError("hydrogen EOS returned invalid density")
        return rho * free_volume_m3

    reference = inventory(maximum_pressure_bar_absolute, reference_temperature_k) - inventory(
        minimum_withdrawal_pressure_bar_absolute, reference_temperature_k)
    hot_gross = inventory(maximum_pressure_bar_absolute, hot_temperature_k)
    cold_heel = inventory(minimum_withdrawal_pressure_bar_absolute, cold_temperature_k)
    conservative = hot_gross - cold_heel
    if reference <= 0 or conservative <= 0:
        raise ThermalCapacityError("no positive withdrawable capacity under stated endpoints")
    loss = reference - conservative
    if loss < -1e-7 * reference:
        raise ThermalCapacityError("EOS violates expected thermal capacity ordering")
    return ThermalCapacityScreen(
        reference_usable_kg=reference, hot_fill_gross_kg=hot_gross,
        cold_withdrawal_heel_kg=cold_heel, conservative_usable_kg=conservative,
        loss_vs_isothermal_kg=max(0.0, loss),
        loss_fraction=max(0.0, loss) / reference,
        temperature_range_k=(cold_temperature_k, hot_temperature_k),
    )
