"""Independent numerical verification of F3 matched-service ideal source model.

Synthetic arrays are exclusively deterministic mathematical verification
fixtures; they are not empirical 2023 inputs or published plant cases.
The actual 2023 8760h source runs require pinned original source archives.
"""
import numpy as np
import pytest
from ptxflex.f3_matched_ideal_benchmark import (
    DIM,P,U,G,C,S,CH,DIS,Z,SourceLockedDispatchError,
    solve_ideal_storage,independently_audit,SCHEMA
)


def small_parameters(cap=10000,loss=0):
    return {
        "capacity_kg":float(cap),"initial_kg":float(cap/2),
        "terminal_kg":float(cap/2),
        "charge_max_kg_h":2200.,"discharge_max_kg_h":2200.,
        "loss_fraction_per_hour":float(loss),
        "rated_mw":125.,"min_load_fraction":.1,"max_load_fraction":1.,
        "ramp_mw_h":50.,"grid_max_mw":50.,
        "h2_coefficient_kg_mwh":20.,
        "delivery_limit_kg_h":7200.,
        "source_bafu_PEM_pressure_bar":30.,
        "source_pipeline_min_delivery_pressure_bar":20.
    }


def test_equal_hydrogen_service_actual_milp_and_independent_bounds():
    inp=np.array([100.,100.,100.,100.])
    price=np.array([15.,-5.,20.,7.])
    target=np.array([1000.,1000.,1000.,1000.])
    res=solve_ideal_storage(inp,price,target,small_parameters(),time_limit_s=30,mip_rel_gap=1e-8)
    assert res["model_schema"]==SCHEMA
    assert res["solver_optimal"] is True
    x=np.asarray(res["hourly_solved_states"])
    assert x.shape==(4,DIM)
    assert np.allclose(20*x[:,P]-x[:,CH]+x[:,DIS],target,atol=1e-5)
    assert res["derived_audit"]["strict_reference_hourly_delivery_profile_is_matched"] is True
    assert res["complete_physical_storage_compression_and_BAU_LCA"] is False
    assert res["valid_for_environmental_superiority_claim"] is False
    assert res["derived_audit"]["max_storage_state_kg"]<=10000+1e-6


def test_two_capacities_share_exact_h2_delivery_profile_even_if_cost_differs():
    price=np.array([70.,40.,20.,90.,-10.,30.])
    wind=np.array([70.,95.,90.,120.,80.,120.])
    service=np.array([1000.,1000.,1000.,1000.,1000.,1000.])
    first=solve_ideal_storage(wind,price,service,small_parameters(5000),time_limit_s=30)
    second=solve_ideal_storage(wind,price,service,small_parameters(10000),time_limit_s=30)
    assert first["solver_optimal"] and second["solver_optimal"]
    assert first["derived_audit"]["annual_service_h2_kg"]==6000
    assert second["derived_audit"]["annual_service_h2_kg"]==6000
    # A larger storage feasible set must never increase the mathematical
    # MINIMUM cost when all other source parameters and initial/terminal
    # inventory are identical. Here initial inventory is capacity/2, so
    # different initial states invalidate this assertion; only verify service.
    assert first["derived_audit"]["max_storage_state_kg"]<=5000+1e-5
    assert second["derived_audit"]["max_storage_state_kg"]<=10000+1e-5


def test_independent_storage_and_electricity_audit_catches_tampering():
    p=small_parameters()
    wind=np.array([100.,100.,100.])
    prices=np.array([5.,5.,5.])
    delivered=np.array([1000.,1000.,1000.])
    r=solve_ideal_storage(wind,prices,delivered,p,time_limit_s=30)
    x=np.asarray(r["hourly_solved_states"]).copy()
    x[0,S]+=1
    with pytest.raises(SourceLockedDispatchError,match="independent mass/energy/feasibility/cost audit failed"):
        independently_audit(x,wind,prices,delivered,p,source_cost=r["derived_audit"]["total_wholesale_net_grid_eur2023"])


@pytest.mark.parametrize("modifier",[
    ("delivery_limit_kg_h",10.),
    ("capacity_kg",-100.),
    ("loss_fraction_per_hour",2.),
])
def test_invalid_original_study_constraints_are_rejected(modifier):
    p=small_parameters()
    p[modifier[0]]=modifier[1]
    with pytest.raises(SourceLockedDispatchError):
        solve_ideal_storage([100,100],[10,10],[1000,1000],p,time_limit_s=10)


def test_input_timeseries_with_negative_weather_power_rejected():
    with pytest.raises(SourceLockedDispatchError,match="negative wind"):
        solve_ideal_storage([100,-1],[10,10],[1000,1000],small_parameters())
