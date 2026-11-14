"""Deliberately mathematical 2023-shaped fixtures; no original data copied to test."""
import pytest
from ptxflex.f3_backup_sparse_hourly import (
    extract_verified_sparse_h2_need,InvalidOriginalHourlyShortage,
    E_SHA,ES_SHA,EXPECTED_ARTIFACT_ZIP_SHA,REFERENCE_TARGET_KG,
)


def make_case():
    q=[0.]*8760
    q[3]=50.
    q[4]=80.
    q[800]=20.
    source={"derived_source_not_original_raw_prices_or_wind":True,
            "source_E_delivered_reference_profile_is_modelled":True,
            "hourly_additional_shortfall_kg":q}
    summary={
        "schema_version":"ptxflex.F3_2023_hypothetical_source_hourly_H2_backup_load_envelope.v1",
        "capacity_semantics":"max_inventory","source_E_zip_sha256":E_SHA,
        "source_EplusS_zip_sha256":ES_SHA,
        "matched_service_LCA_TEA_comparison_permitted":False,
        "source_2023_original_E_reference_delivered_kg":REFERENCE_TARGET_KG,
        "single_incumbent_hypothetical_topup_annual_kg":150.,
        "single_incumbent_hypothetical_topup_occupied_hours":3,
        "single_incumbent_contiguous_events_0_indexed_inclusive":[[3,4],[800,800]],
        "single_incumbent_hypothetical_topup_24h_peak_kg":130.,
        "single_incumbent_hypothetical_topup_max_kg_per_hour":80.,
    }
    return source,summary


def test_produces_exact_source_hour_index_without_unlicensed_price_weather():
    s,r=make_case()
    out=extract_verified_sparse_h2_need("max_inventory",s,r,
             artifact_zip_sha256=EXPECTED_ARTIFACT_ZIP_SHA["max_inventory"])
    assert out["source_8760_hourly_count"]==8760
    assert [q["hour_index_0_based"] for q in out["positive_H2_topup_needed_kg_by_0_based_source_hour"]]==[3,4,800]
    assert out["modelled_additional_annual_topup_for_feasible_incumbent_kg"]==150.
    assert out["event_count"]==2
    assert out["zero_kg_h_at_all_hours_not_listed"]
    assert out["actual_supplier_capacity_and_quality_pressure_checked"] is False


@pytest.mark.parametrize("mutation",[
    lambda s,r:s["hourly_additional_shortfall_kg"].pop(),
    lambda s,r:s["hourly_additional_shortfall_kg"].__setitem__(100,float("nan")),
    lambda s,r:s["hourly_additional_shortfall_kg"].__setitem__(100,-1.),
    lambda s,r:r.update(single_incumbent_hypothetical_topup_annual_kg=1500),
    lambda s,r:r.update(single_incumbent_hypothetical_topup_occupied_hours=2),
    lambda s,r:r.update(single_incumbent_hypothetical_topup_24h_peak_kg=150.),
    lambda s,r:r.update(source_E_zip_sha256="0"*64),
    lambda s,r:r.update(matched_service_LCA_TEA_comparison_permitted=True),
])
def test_fails_on_corrupted_historical_modelled_hourly_backup_need(mutation):
    s,r=make_case();mutation(s,r)
    with pytest.raises(InvalidOriginalHourlyShortage):
        extract_verified_sparse_h2_need("max_inventory",s,r,
              artifact_zip_sha256=EXPECTED_ARTIFACT_ZIP_SHA["max_inventory"])


def test_wrong_source_evidence_digest_rejected():
    s,r=make_case()
    with pytest.raises(InvalidOriginalHourlyShortage,match="digest"):
        extract_verified_sparse_h2_need("max_inventory",s,r,artifact_zip_sha256="bad")
