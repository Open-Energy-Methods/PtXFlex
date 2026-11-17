"""Hermetic controlled source-year counterfactual matrix design regression.

Only synthetic source vectors; no hosted secrets, originals, annual MILPs.
Real 2022/2024 full-year case results are NOT implied by these tests.
"""
import numpy as np
import pytest

from ptxflex import f3d_external_year_controlled_counterfactual as m
from ptxflex.f3_matched_ideal_benchmark import SourceLockedDispatchError


def toy():
    p=np.asarray([(-50.+i) for i in range(200)],dtype=float)
    w=np.asarray([float(i%100) for i in range(200)],dtype=float)
    return p,w


def test_original_source_shape_and_pre_registered_variants():
    assert set(m.VARIANTS)=={
        "price_roll_168h","price_spread_150pct",
        "wind_power_090","wind_power_110_capped"}
    assert m.MODES==("max_inventory","usable_service")
    assert m.PRIVATE_SCHEMA.endswith("exact_dispatch.v1")


def test_price_roll_preserves_multiset_changes_chronology_not_wind():
    p,w=toy()
    q,z=m.transform_inputs(p,w,"price_roll_168h")
    assert np.array_equal(q,np.roll(p,168))
    assert np.array_equal(z,w)
    assert np.array_equal(np.sort(q),np.sort(p))
    assert not np.array_equal(q,p)


def test_centered_price_spread_preserves_median_not_actual_prices():
    p,w=toy()
    q,z=m.transform_inputs(p,w,"price_spread_150pct")
    assert np.array_equal(z,w)
    assert np.median(q)==pytest.approx(np.median(p))
    assert np.ptp(q)==pytest.approx(1.5*np.ptp(p))
    assert not np.array_equal(q,p)


def test_wind_reduction_does_not_scale_wind_speed_or_source_price():
    p,w=toy()
    q,z=m.transform_inputs(p,w,"wind_power_090")
    assert np.array_equal(q,p)
    assert np.allclose(z,w*.9)
    assert np.min(z)>=0


def test_wind_power_cap_does_not_exceed_registered_PyNEXUS_limit():
    p,w=toy()
    w[-2:]=[120.,125.685]
    q,z=m.transform_inputs(p,w,"wind_power_110_capped")
    assert np.array_equal(q,p)
    assert np.max(z)<=125.685
    assert z[-1]==pytest.approx(125.685)
    assert z[-2]==pytest.approx(125.685)
    assert z[0]==0.


def test_unregistered_case_and_bad_observed_vectors_fail_closed():
    p,w=toy()
    with pytest.raises(SourceLockedDispatchError):
        m.transform_inputs(p,w,"wind_speed_110")
    with pytest.raises(SourceLockedDispatchError):
        m.transform_inputs(p,np.array([0.,1.]),"price_roll_168h")
    w[1]=-1
    with pytest.raises(SourceLockedDispatchError):
        m.transform_inputs(p,w,"wind_power_090")


def test_source_original_public_Git_blob_pin_changes_with_one_byte():
    raw=b"source version 1\n"
    assert m.original_blob_sha(raw)==m.original_blob_sha(raw.replace(b"\n",b"\r\n"))
    assert m.original_blob_sha(raw)!=m.original_blob_sha(b"source version 2\n")


def test_counterfactual_paths_preserve_storage_interpretation_and_Year(tmp_path):
    a=m.result_path(tmp_path,2024,"usable_service","price_roll_168h","E")
    b=m.result_path(tmp_path,2024,"usable_service","price_roll_168h","E_plus_S")
    assert a!=b
    assert "2024" in a.name
    assert a.parent==tmp_path
    assert "PRIVATE" in a.name
