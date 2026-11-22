"""Hermetic source-equivalence tests for the OFFICIAL ARCO fast-point pilot.

All vectors fabricated, no actual ERA5 downloaded or re-labelled as original.
The authentic October 2026 PyNEXUS NetCDF hash/UTC evidence is required by
run_pilot(); this suite tests only the comparison semantics.
"""
import numpy as np
import pytest
from ptxflex.f3d_era5_arco_pilot import (
    ALIASES,SCHEMA,compare_original_and_arco,select_variable_name,
    interpret_arco_point,
)


def _fake_vectors(speed=7.0):
    return {
        "u10":np.full(744,5.,dtype="float32"),
        "v10":np.full(744,1.,dtype="float32"),
        "u100":np.full(744,speed,dtype="float32"),
        "v100":np.full(744,1.,dtype="float32"),
    }


def test_identical_744hour_ARCO_2023_january_matches_to_one_watt_and_all_components():
    original=_fake_vectors()
    arco={k:v.copy() for k,v in original.items()}
    r=compare_original_and_arco(original,arco)
    assert r["utc_hour_count"]==744
    assert r["ARCO_Jan2023_wind_1W_quantized_matches_original_CDS_for_every_hour"] is True
    assert r["Jan2023_original_model_wind_1W_SHA256"]==r["Jan2023_ARCO_model_wind_1W_SHA256"]
    assert max(r["all_four_ARCO_native_wind_vector_max_abs_diff_ms"].values())==0
    assert r["ARCO_2022_2024_years_independently_admitted"] is False
    assert r["original_2023_full_annual_source_replaced"] is False


def test_distinct_2023_ARCO_model_wind_is_rejected_not_artificially_source_matched():
    original=_fake_vectors()
    arco={k:v.copy() for k,v in original.items()}
    arco["u100"][10]+=np.float32(.125)
    r=compare_original_and_arco(original,arco)
    assert r["max_abs_modelled_wind_farm_difference_MW"]>1e-6
    assert r["ARCO_Jan2023_wind_1W_quantized_matches_original_CDS_for_every_hour"] is False
    assert r["Jan2023_original_model_wind_1W_SHA256"]!=r["Jan2023_ARCO_model_wind_1W_SHA256"]


def test_missing_OR_duplicate_variable_names_rejected():
    class Fake:
        data_vars={"u10":None,"10m_u_component_of_wind":None}
    with pytest.raises(ValueError,match="exactly one recognized"):
        select_variable_name(Fake(),"u10")
    class Missing:
        data_vars={"unknown":None}
    with pytest.raises(ValueError,match="exactly one recognized"):
        select_variable_name(Missing(),"u100")


def test_wrong_source_hour_count_cannot_be_admitted():
    original=_fake_vectors()
    bad=_fake_vectors()
    bad["v100"]=bad["v100"][:-1]
    with pytest.raises(ValueError,match="vector original UTC sample count changed"):
        compare_original_and_arco(original,bad)
