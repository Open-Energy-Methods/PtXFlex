"""F3-D source-year selection tests: synthetic math only, NEVER observed data."""
import csv
from datetime import datetime,timezone,timedelta
import math

import numpy as np
import pytest

from ptxflex.f3d_year_matched_service import (
    SERVICE_CONTRACT_KG_DAY, SEL_SCHEMA, array_sha, certify_cost_case,
    load_private_hourly, load_source_parameters, select_max_uniform_fraction,
    SourceLockedDispatchError,
)
from ptxflex.f3_matched_ideal_benchmark import solve_ideal_storage


def plant():
    r=load_source_parameters()
    e=dict(r["E"])
    e["loss_fraction_per_hour"]=0.
    return e


def test_original_2023_source_plant_params_retained_for_E_and_ES():
    cases=load_source_parameters()
    assert cases["E"]["capacity_kg"]==20000
    assert cases["E_plus_S"]["capacity_kg"]==40000
    for key in set(cases["E"])-{"capacity_kg"}:
        assert cases["E"][key]==cases["E_plus_S"][key]
    assert cases["E"]["h2_coefficient_kg_mwh"]==21.086108610861086
    assert cases["E"]["ramp_mw_h"]==50


def test_source_E_price_independent_max_uniform_fraction_100pct():
    wind=np.full(8,110.0)
    picked=select_max_uniform_fraction(wind,plant(),None,testing_only=True,time_limit_s=30)
    target=picked["_target_private"]
    assert picked["schema_version"]==SEL_SCHEMA
    assert picked["selected_fraction_50t_per_day"]==pytest.approx(1.0,abs=1e-6)
    assert np.array_equal(target,np.full(8,SERVICE_CONTRACT_KG_DAY/24))
    assert picked["selected_h2_target_float64_sha256"]==array_sha(target)
    assert picked["E_price_neutral_physical_residual_max"]<2e-4


def test_price_neutral_selector_reduces_unachievable_uniform_contract_without_mislabel():
    wind=np.zeros(8)
    p=plant()
    selected=select_max_uniform_fraction(wind,p,None,testing_only=True,time_limit_s=30)
    alpha=selected["selected_fraction_50t_per_day"]
    physically_available_per_hour=p["grid_max_mw"]*p["h2_coefficient_kg_mwh"]
    fraction_physical_upper=physically_available_per_hour/(SERVICE_CONTRACT_KG_DAY/24)
    assert 0<alpha<=fraction_physical_upper+1e-6
    assert selected["certified_fraction_upper_bound"]>=alpha-1e-7
    assert selected["modelled_E_annual_h2_service_kg"]<SERVICE_CONTRACT_KG_DAY/3
    assert selected["testing_only"] is True


def test_hourly_matched_case_is_price_optimized_after_independent_target_selection():
    wind=np.array([110.,100.,90.,115.,110.,100.,90.,115.])
    price=np.array([20.,-10.,70.,5.,30.,-20.,40.,60.])
    selected=select_max_uniform_fraction(wind,plant(),None,testing_only=True,time_limit_s=30)
    target=selected["_target_private"]
    a=solve_ideal_storage(wind,price,target,plant(),time_limit_s=30)
    b_params=plant();b_params["capacity_kg"]=40000.
    b=solve_ideal_storage(wind,price,target,b_params,time_limit_s=30)
    assert a["solver_optimal"] and b["solver_optimal"]
    assert a["derived_audit"]["annual_service_h2_kg"]==pytest.approx(float(target.sum()),abs=1e-3)
    assert b["derived_audit"]["annual_service_h2_kg"]==pytest.approx(float(target.sum()),abs=1e-3)


def test_external_2024_cannot_claim_short_or_8760_input():
    with pytest.raises(SourceLockedDispatchError,match="full UTC"):
        select_max_uniform_fraction(np.ones(8760),plant(),None,year=2024,time_limit_s=10)
    with pytest.raises(SourceLockedDispatchError,match="full UTC"):
        select_max_uniform_fraction(np.ones(24),plant(),None,year=2022,time_limit_s=10)


def test_independent_f64_hash_and_nonfinite_rejected():
    with pytest.raises(SourceLockedDispatchError,match="invalid source"):
        array_sha([float("nan")])
    with pytest.raises(SourceLockedDispatchError,match="eligible nonnegative"):
        select_max_uniform_fraction([50,-5,50],plant(),None,testing_only=True)


@pytest.mark.parametrize("year,n",[(2022,8760),(2024,8784)])
def test_synthetic_hourly_csv_calendar_admission_rejects_leap_truncation(tmp_path,year,n):
    path=tmp_path/"synthetic_mathematical_calendar_only.csv"
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.writer(f)
        writer.writerow(["timestamp_utc","day_ahead_eur_mwh"])
        first=datetime(year,1,1,tzinfo=timezone.utc)
        for i in range(n):
            writer.writerow([(first+timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ"),"-50.25" if i==0 else "37.0"])
    out=load_private_hourly(path,year,"day_ahead_eur_mwh")
    assert out.size==n and out[0]==-50.25
    with path.open("a",encoding="utf-8") as f:
        f.write("9999-01-01T00:00:00Z,0\n")
    with pytest.raises(SourceLockedDispatchError,match="excess UTC"):
        load_private_hourly(path,year,"day_ahead_eur_mwh")


def test_empty_and_duplicate_calendar_cannot_pass_source_hour_gate(tmp_path):
    f=tmp_path/"missing.csv"
    f.write_text("timestamp_utc,wind_available_mw\n2024-01-01T00:00:00Z,1\n")
    with pytest.raises(SourceLockedDispatchError,match="incomplete"):
        load_private_hourly(f,2024,"wind_available_mw",nonnegative=True)
    f.write_text("timestamp_utc,wind_available_mw\n2024-01-01T00:00:00Z,1\n2024-01-01T00:00:00Z,1\n")
    with pytest.raises(SourceLockedDispatchError,match="shifted or duplicated"):
        load_private_hourly(f,2024,"wind_available_mw",nonnegative=True)


def test_economic_bounds_never_allow_mismatched_year_or_noncertified_result():
    base={"source_year":2022,"solver_optimal":False,"solver_status":1,
          "mip_relative_gap":None}
    with pytest.raises(SourceLockedDispatchError,match="certified integer"):
        certify_cost_case(base,np.ones(3),"E",2022)
    with pytest.raises(SourceLockedDispatchError,match="wrong source calendar"):
        certify_cost_case(base,np.ones(3),"E",2024)
