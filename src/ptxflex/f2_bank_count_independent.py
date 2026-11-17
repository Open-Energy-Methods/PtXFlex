"""Independent arithmetic audit of a published-vessel pressure-swing screen.

Inputs are explicitly labelled externally calculated EOS densities, not
measurements. No pressure rating, manufacturer BOM or LCA is certified here.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING


@dataclass(frozen=True)
class CountAudit:
    lower_bound_vessels: int
    actual_vessels: int
    capacity_margin_kg: Decimal
    preceding_bank_shortfall_kg: Decimal
    gross_mass_kg: Decimal
    heel_mass_kg: Decimal
    withdrawable_mass_kg: Decimal
    empty_vessel_hardware_kg: Decimal
    installed_station_mass_kg: None = None
    native_manufacturing_gwp_kg_co2e: None = None
    certified_design: bool = False


def _positive_decimal(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError(f'{name} must be a positive finite number')
    try:
        d = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f'{name} must be numeric') from exc
    if not d.is_finite() or d <= 0:
        raise ValueError(f'{name} must be a positive finite number')
    return d


def independent_bank_count(*, target_kg, vessel_volume_m3, rho_upper_kg_m3,
                           rho_lower_kg_m3, empty_vessel_mass_kg,
                           semantics):
    """Exact decimal ceiling and N-1 minimality certificate.

    Density is supplied by an independently identified EOS calculation.
    max_inventory means gross stock at upper pressure; usable_service
    means recoverable stock above lower-pressure heel.
    """
    if semantics not in ('max_inventory', 'usable_service'):
        raise ValueError('capacity semantics must be explicit')
    t = _positive_decimal(target_kg, 'target_kg')
    v = _positive_decimal(vessel_volume_m3, 'vessel_volume_m3')
    hi = _positive_decimal(rho_upper_kg_m3, 'rho_upper_kg_m3')
    lo = _positive_decimal(rho_lower_kg_m3, 'rho_lower_kg_m3')
    mass = _positive_decimal(empty_vessel_mass_kg, 'empty_vessel_mass_kg')
    if lo >= hi:
        raise ValueError('upper-pressure EOS density must exceed heel density')
    per = v * (hi if semantics == 'max_inventory' else hi - lo)
    n = int((t / per).to_integral_value(rounding=ROUND_CEILING))
    if not 1 <= n <= 10_000_000:
        raise ValueError('bank vessel count outside audited range')
    margin = n * per - t
    shortfall = t - (n - 1) * per
    if margin < 0 or shortfall <= 0:
        raise ArithmeticError('minimality certificate failed')
    return CountAudit(n, n, margin, shortfall, n*v*hi, n*v*lo,
                      n*v*(hi-lo), n*mass)
