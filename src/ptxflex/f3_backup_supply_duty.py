"""F3 backup source-hourly supply engineering envelope (not a supplier design).

Pure deterministic postprocessing of already SHA-verified 8760h modelled
shortage values. Peak flow and ramp numbers describe *one incumbent*,
not globally necessary hardware ratings. No invented observations.
"""
from __future__ import annotations
import math
import numpy as np

WINDOWS_H=(1,6,24,72,168)

def derive_incumbent_supply_envelope(hourly_shortage_kg):
    a=np.asarray(hourly_shortage_kg,dtype=float)
    if a.shape!=(8760,) or not np.isfinite(a).all() or np.min(a)<0:
        raise ValueError("requires finite nonnegative 8760h verified source sequence")
    annual=float(math.fsum(map(float,a)))
    if annual<=0:
        raise ValueError("positive certified shortage incumbent required")
    windows={}
    # Prefix sums and direct convolution are mathematically independent
    # implementations of the rolling-hour aggregate.
    prefix=np.r_[0.,np.cumsum(a,dtype=np.float64)]
    for n in WINDOWS_H:
        rolling=prefix[n:]-prefix[:-n]
        direct=np.convolve(a,np.ones(n,dtype=float),mode="valid")
        if not np.allclose(rolling,direct,rtol=0,atol=1e-6):
            raise ValueError("rolling-window independent mass closure failed")
        i=int(np.argmax(direct))
        windows[str(n)]={
            "window_hours":n,
            "peak_contiguous_window_kg":float(direct[i]),
            "first_peak_window_start_hour_index_0_based":i,
            "first_peak_window_end_hour_index_0_based_inclusive":i+n-1,
            "average_supply_kg_h_within_peak_window":float(direct[i]/n),
            "global_minimum_constant_flow_kg_h_for_this_fixed_incumbent_trace":
                float(direct[i]/n),
            "not_a_global_dispatch_or_equipment_minimum":True
        }
    # These boundary differences assume zero supply outside 2023. Those
    # boundaries are *not* an observed source shutdown, hence report only
    # within-year adjacent-hour changes.
    changes=np.diff(a)
    ramp_up=float(np.max(np.maximum(changes,0)))
    ramp_down=float(np.max(np.maximum(-changes,0)))
    if not math.isclose(annual,float(np.sum(a)),abs_tol=1e-6):
        raise ValueError("annual numerical mass summation mismatch")
    if not math.isclose(windows["1"]["peak_contiguous_window_kg"],float(np.max(a)),abs_tol=1e-9):
        raise ValueError("hourly peak cross-check mismatch")
    if not math.isclose(windows["24"]["peak_contiguous_window_kg"],
                        float(np.max(np.convolve(a,np.ones(24),mode="valid"))),abs_tol=1e-6):
        raise ValueError("24h independent rolling cross-check mismatch")
    return {
        "schema_version":"ptxflex.F3_2023_incumbent_H2_backup_supply_duty.v0.1",
        "evidence_class":"source-derived modelled feasible-incumbent shortage only",
        "source_year":2023,"source_hours":8760,
        "annual_hypothetical_topup_kg":annual,
        "annual_average_kg_h":annual/8760,
        "windows":windows,
        "max_positive_adjacent_hour_increase_kg_h_per_hour":ramp_up,
        "max_negative_adjacent_hour_decrease_kg_h_per_hour":ramp_down,
        "peak_kg_h":float(np.max(a)),
        "nonzero_source_shortage_hours":int(np.count_nonzero(a>1e-5)),
        "minimum_physical_supplier_flow_rating_proven":False,
        "minimum_annual_backup_shortage_from_MILP_dual_not_derived_here":True,
        "external_H2_supplier_or_storage_buffer_specified":False,
        "delivery_pressure_purity_and_transport_verified":False,
        "backup_LCA_TEA_or_real_plant_validation":False,
        "meaning":"Requirements to reproduce this one fixed feasible incumbent hourly top-up profile without an upstream buffer; not a global minimum, physical supplier rating, or guaranteed supply."
    }
