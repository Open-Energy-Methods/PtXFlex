"""F3-D H30 W090 exogenous original-source integer scenario admission tests.

Synthetic evidence only. The real 2022 annual E/ES MILPs have NOT been run
by these tests. Original source provider arrays/witnesses remain PRIVATE.
"""
import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from ptxflex import f3d_exogenous_h2_integer_dispatch as m
from ptxflex.f3_matched_ideal_benchmark import SourceLockedDispatchError
from ptxflex.f3d_year_matched_service import array_sha


def test_source_locked_fixed_H2_is_not_E_maximal_selector():
    assert m.SERVICE_TPD==30.
    assert m.WIND_POWER_FACTOR==.9
    assert m.CASES==("E","E_plus_S")
    for n in (8760,8784):
        t=m.fixed_target(n)
        assert t.shape==(n,)
        assert float(t[0])==1250.
        assert np.all(t==1250.)
        assert float(np.sum(t))==1250*n
        assert array_sha(t)==array_sha(np.full(n,1250.,dtype="<f8"))
    with pytest.raises(SourceLockedDispatchError):
        m.fixed_target(8760,30.480648653278504)
    with pytest.raises(SourceLockedDispatchError):
        m.fixed_target(8761)


def valid_manifest(year=2022,mode="max_inventory"):
    hours={2022:8760,2024:8784}[year]
    target=m.fixed_target(hours)
    selected=30.480648653278504 if year==2022 else 30.747937895131617
    entries=[]
    for d in (25.,27.5,30.):
        for k in (.9,.95,1.):
            tgt=np.full(hours,d*1000/24.,dtype="<f8")
            entries.append({
                "exogenous_H2_tonnes_per_day":d,
                "source_wind_power_multiplier":k,
                "exogenous_H2_original_same_hourly_SHA256":array_sha(tgt),
                "exogenous_same_product_annual_H2_kg":float(np.sum(tgt)),
                "matched_source_annual_E_minus_EplusS_cost_saving_eur":None,
                "E_and_ES_original_integer_dispatch_both_certified":False,
                "cases":{case:{
                    "HiGHS_LP_status_code":0,
                    "source_E_or_EplusS_original_model_LP_status":
                        "SOURCE_LP_PRIMAL_FEASIBLE_INTEGER_UNDETERMINED",
                    "source_stress_wind_electric_power_multiplier":k,
                    "original_integer_MILP_feasible":None,
                    "source_matched_service_annual_cost_saving_eur":None,
                } for case in ("E","E_plus_S")}
            })
    j={
        "schema_version":m.LP_SCHEMA,
        "source_year":year,"capacity_semantics":mode,
        "source_calendar_UTC_hours":hours,
        "source_original_4_case_public_Git_blob_sha1":m.SOURCE_BLOB_SHA,
        "source_original_price_float64_SHA256":"a"*64,
        "source_original_wind_power_float64_SHA256":"b"*64,
        "source_original_E_max_selected_hourly_H2_float64_SHA256":"c"*64,
        "source_price_year_input_unchanged":True,
        "same_H2_target_hourly_for_E_and_ES_at_every_wind_factor":True,
        "exogenous_delivery_schedules_selected_without_looking_at_stressed_wind_outcomes":True,
        "original_integer_dispatch_or_matched_wholesale_savings_certified":False,
        "real_site_or_manufacturer_or_native_BAFU_or_scientific_v1_0":False,
        "original_selected_E_max_nominal_tonnes_day":selected,
        "prespecified_exogenous_delivery_tonnes_day":[25.,27.5,30.],
        "source_wind_electric_power_multipliers":[.9,.95,1.],
        "nine_service_factor_pairs_two_architectures_LP_cells":entries,
    }
    return j,target,selected


def accept(tmp_path,obj,target,selected):
    path=tmp_path/"synthetic_exogenous_original_lp.json"
    path.write_text(json.dumps(obj),encoding="utf-8")
    out=m.check_lp_manifest(path,obj["source_year"],obj["capacity_semantics"],
                            "a"*64,"b"*64,"c"*64,selected,target,
                            np.full(target.shape,50.,dtype=float))
    return out


def test_full_synthetic_predeclared_LP_matrix_admitted_with_original_H2_SHA(tmp_path):
    j,target,selected=valid_manifest()
    out=accept(tmp_path,j,target,selected)
    assert out["LP_cell_status"]=="BOTH_ORIGINAL_MODEL_LPS_FEASIBLE_INTEGER_UNKNOWN"
    assert out["exogenous_H2_fixed_hourly_SHA256"]==array_sha(target)
    assert len(out["LP_screen_bytes_SHA256"])==64


@pytest.mark.parametrize("mutation",[
    lambda j:j.update(source_original_4_case_public_Git_blob_sha1="altered"),
    lambda j:j.update(real_site_or_manufacturer_or_native_BAFU_or_scientific_v1_0=True),
    lambda j:j.update(original_integer_dispatch_or_matched_wholesale_savings_certified=True),
    lambda j:j["nine_service_factor_pairs_two_architectures_LP_cells"].pop(),
    lambda j:j["nine_service_factor_pairs_two_architectures_LP_cells"][6]["cases"]["E"].update(
        HiGHS_LP_status_code=2),
    lambda j:j["nine_service_factor_pairs_two_architectures_LP_cells"][6]["cases"]["E_plus_S"].update(
        original_integer_MILP_feasible=True),
    lambda j:j["nine_service_factor_pairs_two_architectures_LP_cells"][6].update(
        matched_source_annual_E_minus_EplusS_cost_saving_eur=50000.),
    lambda j:j["nine_service_factor_pairs_two_architectures_LP_cells"][6].update(
        exogenous_H2_original_same_hourly_SHA256="changed"),
])
def test_corrupt_historical_LP_or_false_v1_integer_release_refused(tmp_path,mutation):
    j,target,selected=valid_manifest()
    mutation(j)
    with pytest.raises(SourceLockedDispatchError):
        accept(tmp_path,j,target,selected)


def test_missing_private_source_gate_and_output_case_disambiguation(tmp_path):
    for case in m.CASES:
        path=m.private_result_file(tmp_path,2022,"max_inventory",case)
        assert path.parent.name=="exogenous_service_robustness"
        assert "PRIVATE" in path.name
        assert "H30_W090" in path.name
        assert case in path.name
    assert m.private_result_file(tmp_path,2022,"max_inventory","E")!=\
           m.private_result_file(tmp_path,2022,"max_inventory","E_plus_S")
