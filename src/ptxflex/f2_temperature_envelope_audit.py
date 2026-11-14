"""Independent F2 pressure/temperature sensitivity audit (screening only).

Uses CoolProp hydrogen EOS directly, independently of the production
pressure_storage_duty pressure conversion. The audit evaluates a specified
rectangular mass/temperature envelope, not an operating trajectory. Its
sampled extrema are NOT mathematical guarantees between samples and cannot
establish certified vessel temperature, fatigue or pressure suitability.
No vendor temperature range or site observations are inferred.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


class EnvelopeInputError(ValueError):
    """Nonphysical or unsupported screening envelope."""


@dataclass(frozen=True)
class PressureEnvelope:
    minimum_sampled_bar_absolute: float
    maximum_sampled_bar_absolute: float
    minimum_allowed_bar_absolute: float
    maximum_allowed_bar_absolute: float
    sampled_grid_points: int
    all_sampled_points_within_bounds: bool
    exhaustive_continuous_domain_proof: bool = False
    certified_equipment_design: bool = False


def audit_pressure_temperature_envelope(
    *, minimum_total_h2_kg: float, maximum_total_h2_kg: float,
    free_volume_m3: float, minimum_temperature_k: float,
    maximum_temperature_k: float, minimum_pressure_bar_absolute: float,
    maximum_pressure_bar_absolute: float, grid_points_per_axis: int = 9,
) -> PressureEnvelope:
    """Check a bounded *hypothetical* EOS envelope with explicit limitations.

    Gas masses are GROSS, including any residual heel. Temperatures are
    hypothetical uniform equilibrium gas temperatures, not site data.
    This does not model stratification, thermal transients, filling heat,
    compressor/cooling systems, pressure drops or mechanical stress.
    """
    vals=(minimum_total_h2_kg,maximum_total_h2_kg,free_volume_m3,
          minimum_temperature_k,maximum_temperature_k,
          minimum_pressure_bar_absolute,maximum_pressure_bar_absolute)
    if not all(math.isfinite(v) and v>0 for v in vals):
        raise EnvelopeInputError("all masses, temperatures, volume and pressures must be finite positive")
    if (minimum_total_h2_kg>maximum_total_h2_kg
        or minimum_temperature_k>maximum_temperature_k
        or minimum_pressure_bar_absolute>=maximum_pressure_bar_absolute):
        raise EnvelopeInputError("inverted or degenerate physical envelope")
    if isinstance(grid_points_per_axis,bool) or not isinstance(grid_points_per_axis,int) or not 2<=grid_points_per_axis<=101:
        raise EnvelopeInputError("grid points per axis must be an integer from 2 to 101")
    try:
        from CoolProp.CoolProp import PropsSI
    except ImportError as exc:
        raise EnvelopeInputError("CoolProp hydrogen EOS is required; no ideal-gas fallback") from exc
    pressures=[]
    for i in range(grid_points_per_axis):
        mass=minimum_total_h2_kg+(maximum_total_h2_kg-minimum_total_h2_kg)*i/(grid_points_per_axis-1)
        for j in range(grid_points_per_axis):
            temperature=minimum_temperature_k+(maximum_temperature_k-minimum_temperature_k)*j/(grid_points_per_axis-1)
            p=float(PropsSI("P","Dmass",mass/free_volume_m3,"T",temperature,"Hydrogen"))/1e5
            if not math.isfinite(p) or p<=0:
                raise EnvelopeInputError("EOS returned invalid absolute pressure")
            pressures.append(p)
    lo=min(pressures)
    hi=max(pressures)
    return PressureEnvelope(
        minimum_sampled_bar_absolute=lo,
        maximum_sampled_bar_absolute=hi,
        minimum_allowed_bar_absolute=minimum_pressure_bar_absolute,
        maximum_allowed_bar_absolute=maximum_pressure_bar_absolute,
        sampled_grid_points=len(pressures),
        all_sampled_points_within_bounds=(
            lo>=minimum_pressure_bar_absolute and hi<=maximum_pressure_bar_absolute
        ),
    )
