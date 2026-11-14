"""Mathematical leap-calendar regression; never authentic ERA5/A44 observations.

Exercise the full 8784-column-block matrix build with a stub optimizer.
This is NOT a real 2024 dispatch solve, provider data, or plant validation.
"""
from types import SimpleNamespace
import numpy as np
import pytest

import ptxflex.f3_matched_ideal_benchmark as model


@pytest.mark.parametrize("year, hours", [(2022, 8760), (2024, 8784)])
def test_registered_external_year_has_exact_utc_full_year_and_explicit_status(year, hours):
    assert model.validate_dispatch_calendar(
        hours, year, "synthetic_calendar_regression_only") == hours


@pytest.mark.parametrize("hours", [8760, 8783, 8785])
def test_2024_never_silently_drops_february_29_or_accepts_extra_hours(hours):
    with pytest.raises(model.SourceLockedDispatchError, match="exact UTC annual hours"):
        model.validate_dispatch_calendar(hours, 2024, "synthetic_calendar_regression_only")


def test_new_year_without_disclosed_evidence_class_is_rejected():
    with pytest.raises(model.SourceLockedDispatchError, match="NON-certified input class"):
        model.validate_dispatch_calendar(8784, 2024)
    with pytest.raises(model.SourceLockedDispatchError, match="NON-certified input class"):
        model.validate_dispatch_calendar(8784, 2024, "independently_verified_observed_2024")
    with pytest.raises(model.SourceLockedDispatchError, match="unregistered"):
        model.validate_dispatch_calendar(8760, 2025, "synthetic_calendar_regression_only")


def test_legacy_2023_short_synthetic_windows_remain_supported():
    assert model.validate_dispatch_calendar(4) == 8760
    with pytest.raises(model.SourceLockedDispatchError, match="at most 8760"):
        model.validate_dispatch_calendar(8784)
    with pytest.raises(model.SourceLockedDispatchError, match="at most 8760"):
        model.validate_dispatch_calendar(8760, 2023, "synthetic_calendar_regression_only")


def test_full_leap_8784h_lp_matrix_assembly_and_source_gate(monkeypatch):
    n=8784
    calls=[]
    def fake_solver(*, c, integrality, bounds, constraints, options):
        assert len(c)==n*model.DIM
        assert constraints.A.shape[1]==n*model.DIM
        assert np.all(c==0)
        assert np.all(integrality==0)
        calls.append((len(c),constraints.A.shape[0]))
        # Structural test only: no real solver or empirical 2024 physics.
        return SimpleNamespace(status=0, message="synthetic matrix assembly stub",
                               x=np.zeros(len(c)))
    monkeypatch.setattr(model, "milp", fake_solver)
    params={
        "capacity_kg":10000., "initial_kg":5000., "terminal_kg":5000.,
        "charge_max_kg_h":2000., "discharge_max_kg_h":2000.,
        "loss_fraction_per_hour":0.,
        "rated_mw":125., "min_load_fraction":.1, "max_load_fraction":1.,
        "ramp_mw_h":50., "grid_max_mw":50.,
        "h2_coefficient_kg_mwh":20., "delivery_limit_kg_h":7200.,
    }
    zero=np.zeros(n,dtype=float)
    diagnostic=model.solve_ideal_storage(
        zero,zero,zero,params,source_calendar_year=2024,
        external_year_input_class="synthetic_calendar_regression_only",
        diagnostic_only_lp_relaxation=True,time_limit_s=10)
    assert calls and calls[0][0]==8784*model.DIM
    assert diagnostic["tested_hours"]==8784
    assert diagnostic["source_calendar_year"]==2024
    assert diagnostic["input_class"]=="synthetic_calendar_regression_only"
    assert diagnostic["real_external_historical_provider_pair_independently_verified"] is False
    assert diagnostic["source_2023_reference_H2_service_valid_for_new_calendar"] is False
    assert diagnostic["MILP_feasible_conclusion_permitted_from_LP_status_0"] is False
