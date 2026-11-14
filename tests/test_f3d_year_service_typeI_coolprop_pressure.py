"""Source Type-I pressure/charge-power integration; synthetic-only model test.

Requires CoolProp 8; mathematical and EOS fixture, not measured plant data.
"""
import numpy as np
import pytest

CoolProp=pytest.importorskip("CoolProp")

from ptxflex.f3d_year_matched_service import (
    load_source_parameters, physical_duty, select_max_uniform_fraction,
)
from ptxflex.f3_matched_ideal_benchmark import solve_ideal_storage


@pytest.mark.parametrize("mode",("max_inventory","usable_service"))
def test_price_blind_selection_and_same_h2_cost_MILP_with_real_gas_200bar(mode):
    params=load_source_parameters()
    wind=np.array([105.,90.,90.,120.,100.,90.,90.,120.]*3,dtype=float)
    price=np.array([50.,-10.,80.,0.,35.,70.,-30.,90.]*3,dtype=float)
    E=params["E"]
    ES=params["E_plus_S"]
    e_duty=physical_duty(E,mode)
    es_duty=physical_duty(ES,mode)
    selected=select_max_uniform_fraction(
        wind,E,e_duty,testing_only=True,time_limit_s=60)
    target=selected["_target_private"]
    assert selected["selected_fraction_50t_per_day"]>0
    assert selected["source_E_pressure_screen_only"] is True
    assert selected["E_price_neutral_physical_residual_max"]<=2e-4
    assert e_duty.compressor_mw_per_kg_h()>0
    e=solve_ideal_storage(wind,price,target,E,time_limit_s=60,pressure_duty=e_duty)
    es=solve_ideal_storage(wind,price,target,ES,time_limit_s=60,pressure_duty=es_duty)
    assert e["solver_optimal"] and es["solver_optimal"]
    for z in (e,es):
        audit=z["derived_audit"]
        assert audit["pressure_EOS_bounds"]["EOS_hourly_mass_bounds_imply_pressure_limits"] is True
        assert audit["annual_compression_electricity_mwh"]>=0
        assert audit["annual_service_h2_kg"]==pytest.approx(target.sum(),abs=.001)
        assert max(audit["independent_max_physical_residuals"].values())<=2e-4
