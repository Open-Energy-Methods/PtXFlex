"""Deterministic mathematical tests; NOT original 2023 data."""
import numpy as np
import pytest
from ptxflex.f3_backup_supply_duty import derive_incumbent_supply_envelope

def test_rolling_windows_and_ramps_independent_known_sparse_math():
    a=np.zeros(8760)
    a[0:3]=[1.,2.,3.]
    a[100]=4.
    d=derive_incumbent_supply_envelope(a)
    assert d["annual_hypothetical_topup_kg"]==10.
    assert d["annual_average_kg_h"]==10/8760
    assert d["peak_kg_h"]==4.
    assert d["windows"]["1"]["peak_contiguous_window_kg"]==4.
    assert d["windows"]["6"]["peak_contiguous_window_kg"]==6.
    assert d["windows"]["24"]["peak_contiguous_window_kg"]==6.
    assert d["windows"]["72"]["peak_contiguous_window_kg"]==6.
    assert d["windows"]["168"]["peak_contiguous_window_kg"]==10.
    assert d["windows"]["168"]["first_peak_window_start_hour_index_0_based"]==0
    assert d["max_positive_adjacent_hour_increase_kg_h_per_hour"]==4.
    assert d["max_negative_adjacent_hour_decrease_kg_h_per_hour"]==4.
    assert not d["minimum_physical_supplier_flow_rating_proven"]
    assert not d["backup_LCA_TEA_or_real_plant_validation"]

def test_rolling_peak_crosses_hour_boundary_and_is_not_calendar_day():
    a=np.zeros(8760)
    a[23]=8.;a[24]=9.
    d=derive_incumbent_supply_envelope(a)
    assert d["windows"]["24"]["peak_contiguous_window_kg"]==17.
    assert d["windows"]["24"]["first_peak_window_start_hour_index_0_based"]==1
    assert d["max_positive_adjacent_hour_increase_kg_h_per_hour"]==8.
    assert d["max_negative_adjacent_hour_decrease_kg_h_per_hour"]==9.

def test_ramp_is_adjacent_hours_not_annual_average():
    a=np.ones(8760)
    a[1]=10.;a[2]=1.
    d=derive_incumbent_supply_envelope(a)
    assert d["max_positive_adjacent_hour_increase_kg_h_per_hour"]==9.
    assert d["max_negative_adjacent_hour_decrease_kg_h_per_hour"]==9.

@pytest.mark.parametrize("bad",[
    np.zeros(8760),
    np.ones(8759),
    np.r_[np.ones(8759),-1.],
    np.r_[np.ones(8759),float("nan")],
    np.r_[np.ones(8759),float("inf")],
])
def test_reject_invalid_source_hourly_inputs(bad):
    with pytest.raises(ValueError):
        derive_incumbent_supply_envelope(bad)
