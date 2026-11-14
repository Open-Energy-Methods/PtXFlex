"""Synthetic-only negative controls for supplier release admissibility."""
import pytest

from ptxflex.f3_supplier_release_gate import (
    REQUIRED_EXTERNAL_REVIEWS, SupplierReleaseError, assess_supplier_release,
)


def review(**changes):
    data = dict.fromkeys(REQUIRED_EXTERNAL_REVIEWS, False)
    data.update(changes)
    return data


def offer(passed=True):
    return {"fixed_trace_supplier_offer_screen_pass": passed,
            "full_plant_science_gate_passed": False}


def document(complete=True):
    return {"documentary_fields_complete": complete,
            "qualified_for_lca_tea_or_matched_service": False}


def test_math_and_metadata_never_qualify_without_external_reviews():
    result = assess_supplier_release(offer(), document(), review())
    assert result["mathematical_offer_screen_passed"]
    assert result["documentary_metadata_complete"]
    assert not result["supplier_release_admissible"]
    assert not result["full_programme_v1_gate_passed"]


@pytest.mark.parametrize("missing", REQUIRED_EXTERNAL_REVIEWS)
def test_each_independent_review_is_necessary(missing):
    checks = dict.fromkeys(REQUIRED_EXTERNAL_REVIEWS, True)
    checks[missing] = False
    assert not assess_supplier_release(offer(), document(), checks)["supplier_release_admissible"]


def test_even_all_review_flags_do_not_pass_full_programme():
    checks = dict.fromkeys(REQUIRED_EXTERNAL_REVIEWS, True)
    result = assess_supplier_release(offer(), document(), checks)
    assert result["supplier_release_admissible"]
    assert not result["full_programme_v1_gate_passed"]
    assert result["review_flags_are_not_source_authentication"]


@pytest.mark.parametrize("math,metadata", [(False, True), (True, False), (False, False)])
def test_missing_upstream_screen_fails(math, metadata):
    checks = dict.fromkeys(REQUIRED_EXTERNAL_REVIEWS, True)
    assert not assess_supplier_release(offer(math), document(metadata), checks)["supplier_release_admissible"]


def test_missing_or_truthy_review_flags_rejected():
    with pytest.raises(SupplierReleaseError):
        assess_supplier_release(offer(), document(), {})
    checks = review()
    checks["source_bytes_authenticated"] = "yes"
    with pytest.raises(SupplierReleaseError):
        assess_supplier_release(offer(), document(), checks)


def test_upstream_self_certification_rejected():
    a = offer()
    a["full_plant_science_gate_passed"] = True
    with pytest.raises(SupplierReleaseError):
        assess_supplier_release(a, document(), review())
    d = document()
    d["qualified_for_lca_tea_or_matched_service"] = True
    with pytest.raises(SupplierReleaseError):
        assess_supplier_release(offer(), d, review())
