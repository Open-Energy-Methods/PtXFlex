"""Negative controls for F2/L1 evidence gate; all inputs synthetic."""
import copy
import hashlib
import pytest
from ptxflex.f2_l1_handoff import COMPONENTS, HandoffError, screen_f2_l1_handoff


def source():
    return {"locator": "synthetic-fixture", "sha256": hashlib.sha256(b"synthetic").hexdigest(),
            "bytes_authenticated": True, "review_state": "independently_accepted"}


def fixture():
    return {"capacity_semantics": "max_inventory", "pressure_basis": "absolute",
            "minimum_delivery_bar_absolute": 20., "maximum_storage_bar_absolute": 200.,
            "gas_temperature_min_k": 280., "gas_temperature_max_k": 320.,
            "withdrawable_h2_kg": 100.,
            "components": {k: {"quantity": 1, "unit_empty_mass_kg": 2.,
                "rated_pressure_bar_absolute": 200., "manufacturer_part": "SYNTHETIC",
                "source": source()} for k in COMPONENTS},
            "site_pressure_and_delivery_source": source(), "cooling_duty_kwh_per_kg": 0.0,
            "fatigue_and_embrittlement_review": True, "relief_and_hazard_review": True,
            "site_layout_review": True, "vendor_compressor_map_review": True}


def test_complete_synthetic_fixture_is_only_review_ready():
    result = screen_f2_l1_handoff(fixture())
    assert result["review_ready"] and result["equipment_mass_kg_from_explicit_items"] == 20
    assert not result["design_certified"] and not result["native_bafu_lcia_complete"]
    assert not result["industrial_validation"] and not result["v1_release_approved"]


@pytest.mark.parametrize("component", COMPONENTS)
def test_missing_any_component_rejected(component):
    x = fixture()
    del x["components"][component]
    with pytest.raises(HandoffError):
        screen_f2_l1_handoff(x)


@pytest.mark.parametrize("bad", [None, -1, float("nan"), float("inf"), True, 0])
def test_invalid_mass_rejected(bad):
    x = fixture()
    x["components"]["compressor"]["unit_empty_mass_kg"] = bad
    with pytest.raises(HandoffError):
        screen_f2_l1_handoff(x)


def test_unverified_source_fails_closed():
    x = fixture()
    x["components"]["pressure_vessels"]["source"]["bytes_authenticated"] = False
    with pytest.raises(HandoffError):
        screen_f2_l1_handoff(x)


def test_missing_manufacturer_is_open_not_approved():
    x = fixture()
    x["components"]["compressor"]["manufacturer_part"] = ""
    result = screen_f2_l1_handoff(x)
    assert not result["review_ready"] and result["outstanding"]


def test_missing_cooling_and_review_are_open():
    x = fixture()
    x["cooling_duty_kwh_per_kg"] = None
    x["vendor_compressor_map_review"] = False
    result = screen_f2_l1_handoff(x)
    assert not result["review_ready"] and len(result["outstanding"]) == 2


def test_inverted_pressure_and_temperature_rejected():
    x = fixture()
    x["maximum_storage_bar_absolute"] = 10
    with pytest.raises(HandoffError):
        screen_f2_l1_handoff(x)
    x = fixture()
    x["gas_temperature_min_k"] = 400
    with pytest.raises(HandoffError):
        screen_f2_l1_handoff(x)


@pytest.mark.parametrize("rated", [19.0, 199.999, 0, -1, float("nan"), float("inf"), True])
def test_vessel_rating_cannot_undershoot_maximum_storage_pressure(rated):
    x = fixture()
    x["components"]["pressure_vessels"]["rated_pressure_bar_absolute"] = rated
    with pytest.raises(HandoffError):
        screen_f2_l1_handoff(x)


def test_equal_vessel_rating_is_mathematical_screen_only():
    x = fixture()
    x["components"]["pressure_vessels"]["rated_pressure_bar_absolute"] = 200.0
    result = screen_f2_l1_handoff(x)
    assert result["review_ready"]
    assert not result["design_certified"]


def test_downstream_low_pressure_rating_needs_separate_segment_review():
    x = fixture()
    x["components"]["instrumentation"]["rated_pressure_bar_absolute"] = 30.0
    result = screen_f2_l1_handoff(x)
    assert result["review_ready"] and not result["design_certified"]
