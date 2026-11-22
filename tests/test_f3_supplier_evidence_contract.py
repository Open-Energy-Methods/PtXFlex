"""Synthetic metadata fixtures only: no real supplier or measurements."""
import pytest
from ptxflex.f3_supplier_evidence_contract import (
    check_documentary_bundle, EvidenceContractError
)


def fixture():
    return dict(
        supplier_legal_name="SYNTHETIC TEST ONLY",
        facility_or_delivery_node="synthetic node",
        document_title="Synthetic unit-test document",
        issuer="synthetic issuer",
        publication_date="2023-01-01",
        source_url="https://example.org/synthetic-test-only",
        source_sha256="a" * 64,
        page_or_table_locator="synthetic table 1",
        pressure_basis="absolute_bar",
        pressure_bar_absolute=30.0,
        hydrogen_purity_mole_fraction=0.999,
        capacity_kg_per_hour=100.0,
        ramp_kg_per_hour_per_hour=10.0,
        valid_from="2023-01-01",
        valid_until="2023-12-31",
        geographic_scope="synthetic",
        delivery_mode="synthetic",
        license_or_access_basis="synthetic test fixture",
    )


def test_complete_metadata_does_not_verify_any_supplier():
    r = check_documentary_bundle(fixture())
    assert r["documentary_fields_complete"]
    assert not r["source_bytes_independently_authenticated"]
    assert not r["hourly_2023_availability_verified"]
    assert not r["qualified_for_lca_tea_or_matched_service"]


@pytest.mark.parametrize("key,value", [
    ("source_sha256", "a" * 63),
    ("source_url", "http://example.org/test"),
    ("pressure_basis", "gauge_bar"),
    ("pressure_bar_absolute", 0),
    ("pressure_bar_absolute", True),
    ("pressure_bar_absolute", float("nan")),
    ("hydrogen_purity_mole_fraction", 1.01),
    ("capacity_kg_per_hour", -1),
    ("ramp_kg_per_hour_per_hour", -1),
    ("valid_until", "2022-12-31"),
    ("publication_date", "2024-01-01"),
    ("publication_date", "2023-02-30"),
    ("issuer", ""),
])
def test_invalid_evidence_rejected(key, value):
    f = fixture()
    f[key] = value
    with pytest.raises(EvidenceContractError):
        check_documentary_bundle(f)


def test_unknown_fields_and_missing_fields_rejected():
    f = fixture()
    f["asserted_independently_verified"] = True
    with pytest.raises(EvidenceContractError):
        check_documentary_bundle(f)
    del f["asserted_independently_verified"]
    del f["page_or_table_locator"]
    with pytest.raises(EvidenceContractError):
        check_documentary_bundle(f)
