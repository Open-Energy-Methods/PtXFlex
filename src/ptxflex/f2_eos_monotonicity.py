"""Independent sampled thermodynamic-ordering check for an F2 gas EOS.

A necessary screening check, not a sufficient proof of stability, continuous
monotonicity, vessel approval, or the operating temperature trajectory.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class OrderingAudit:
    points_checked: int
    density_order_violations: int
    temperature_order_violations: int
    minimum_pressure_pa: float
    maximum_pressure_pa: float
    passed_sampled_ordering: bool
    continuous_domain_proven: bool = False
    certified_vessel: bool = False


def audit_sampled_eos_ordering(pressure_pa, *, density_min, density_max,
                               temperature_min_k, temperature_max_k, n=9,
                               relative_tolerance=1e-10):
    """Test positive pressure and nondecreasing P(rho,T) on a rectangular grid.

    pressure_pa(density_kg_m3, temperature_k) must be an independently
    supplied EOS evaluator. Does not infer phase stability or vendor ratings.
    """
    values = (density_min, density_max, temperature_min_k,
              temperature_max_k, relative_tolerance)
    if (not all(isinstance(x, (int, float)) and not isinstance(x, bool)
                and math.isfinite(x) for x in values)
        or density_min <= 0 or density_max <= density_min
        or temperature_min_k <= 0 or temperature_max_k < temperature_min_k
        or relative_tolerance < 0 or relative_tolerance >= 0.01
        or isinstance(n, bool) or not isinstance(n, int) or n < 3 or n > 101):
        raise ValueError('invalid physical sampling domain')
    grid = []
    for i in range(n):
        rho = density_min + (density_max-density_min)*i/(n-1)
        row=[]
        for j in range(n):
            temp = temperature_min_k + (temperature_max_k-temperature_min_k)*j/(n-1)
            try:
                p=float(pressure_pa(rho,temp))
            except Exception as exc:
                raise ValueError('EOS evaluation failed') from exc
            if not math.isfinite(p) or p <= 0:
                raise ValueError('EOS returned nonpositive or nonfinite pressure')
            row.append(p)
        grid.append(row)
    density_bad=0
    temperature_bad=0
    for i in range(n-1):
        for j in range(n):
            a,b=grid[i][j],grid[i+1][j]
            if b < a-relative_tolerance*max(a,b):
                density_bad+=1
    for i in range(n):
        for j in range(n-1):
            a,b=grid[i][j],grid[i][j+1]
            if b < a-relative_tolerance*max(a,b):
                temperature_bad+=1
    flat=[p for row in grid for p in row]
    return OrderingAudit(n*n,density_bad,temperature_bad,min(flat),max(flat),
                         density_bad==0 and temperature_bad==0)
