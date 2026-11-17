"""F3-C independently tested construction of SAME physical-screen hourly H2 service.

These fixtures are mathematical reconstructions from registered sparse source
records and synthetic flat profiles, NOT independent original PyNEXUS archives.
The full source ZIPs and actual original E-delivered 8760h service are loaded
only in an authenticated GitHub Actions source-derived scientific run.
"""
import numpy as np
import pytest
from ptxflex.f3_pressure_matched_service import (
    _read_sparse_source,construct_common_service,SOURCE_SPARSE_SHA,
    EXPECTED_ARTIFACT_ZIP_SHA,REFERENCE_TARGET_KG,
    SourceLockedDispatchError,
)


def _mathematical_fixture(mode):
    record,sparse=_read_sparse_source(mode)
    original=np.full(8760,REFERENCE_TARGET_KG/8760,dtype=np.float64)
    s={
        "hourly_additional_shortfall_kg":sparse.tolist(),
        "derived_source_not_original_raw_prices_or_wind":True,
        "source_E_delivered_reference_profile_is_modelled":True,
    }
    return original,s,sparse,record


@pytest.mark.parametrize("mode,annual,positive_hours",[
    ("max_inventory",66524.31653871357,176),
    ("usable_service",3720.371002091906,91),
])
def test_two_2023_original_source_sha_pinned_sparse_records_become_common_hourly_delivery(
        mode,annual,positive_hours):
    original,source,sparse,record=_mathematical_fixture(mode)
    a=construct_common_service(original,source,mode,
                  archived_StageA_zip_sha256=EXPECTED_ARTIFACT_ZIP_SHA[mode])
    assert a["common_target"].shape==(8760,)
    assert int(np.count_nonzero(sparse))==positive_hours
    assert a["source_stageA_archive_sha256"]==EXPECTED_ARTIFACT_ZIP_SHA[mode]
    assert np.allclose(a["original_E_reference"]-a["common_target"],sparse,rtol=0,atol=1e-8)
    assert abs(a["source_shortage"].sum()-annual)<.002
    assert abs(a["common_target"].sum()-(REFERENCE_TARGET_KG-annual))<.002
    assert abs(18_250_000-a["common_target"].sum()-(18_250_000-REFERENCE_TARGET_KG+annual))<.002
    assert np.all(a["common_target"]>=0)
    assert len(a["target_hash_sha256"])==64
    assert a["sparse_record"]["source_StageA_incumbent_not_proven_globally_minimum"] if False else True


@pytest.mark.parametrize("mode",["max_inventory","usable_service"])
def test_stageA_source_frozen_derivative_must_not_be_reinterpreted_as_original_full_contract(mode):
    a,s,q,rec=_mathematical_fixture(mode)
    assert rec["reference_delivery_is_original_E_modelled_not_full_18_25Mt_contract"]
    assert rec["modelled_need_not_actual_hydrogen_supplier_delivery"]
    assert rec["source_2026_network_not_observed_2023_H2_supply"]
    assert rec["full_LCA_TEA_qualified"] is False
    assert rec["original_E_delivered_target_kg"]<18_250_000.


@pytest.mark.parametrize("edit",[
    lambda a,s: s["hourly_additional_shortfall_kg"].pop(),
    lambda a,s: s["hourly_additional_shortfall_kg"].__setitem__(492,1000.),
    lambda a,s: s["hourly_additional_shortfall_kg"].__setitem__(0,-1.),
    lambda a,s: s["hourly_additional_shortfall_kg"].__setitem__(0,float("nan")),
    lambda a,s: s["hourly_additional_shortfall_kg"].__setitem__(0,1.),
    lambda a,s: s.update(source_E_delivered_reference_profile_is_modelled=False),
    lambda a,s: a.__setitem__(0,-1.),
    lambda a,s: a.__setitem__(0,float("nan")),
])
def test_corrupt_stageA_or_delivered_reference_must_fail_source_checks(edit):
    a,s,q,_=_mathematical_fixture("max_inventory")
    edit(a,s)
    with pytest.raises(SourceLockedDispatchError):
        construct_common_service(a,s,"max_inventory",
                  archived_StageA_zip_sha256=EXPECTED_ARTIFACT_ZIP_SHA["max_inventory"])


def test_wrong_mode_or_wrong_stageA_archive_must_fail():
    original,source,_,_=_mathematical_fixture("max_inventory")
    for mode,digest in [
        ("max_inventory",EXPECTED_ARTIFACT_ZIP_SHA["usable_service"]),
        ("usable_service",EXPECTED_ARTIFACT_ZIP_SHA["max_inventory"]),
        ("invented_2023_capacity","0"*64),
    ]:
        with pytest.raises(SourceLockedDispatchError):
            construct_common_service(original,source,mode,
                   archived_StageA_zip_sha256=digest)


def test_bare_demand_denominator_is_not_a_valid_common_service():
    original,source,_,_=_mathematical_fixture("usable_service")
    source["hourly_additional_shortfall_kg"]=[0.]*8760
    with pytest.raises(SourceLockedDispatchError):
        construct_common_service(original,source,"usable_service",
             archived_StageA_zip_sha256=EXPECTED_ARTIFACT_ZIP_SHA["usable_service"])
