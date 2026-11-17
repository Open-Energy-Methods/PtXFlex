import unittest
from ptxflex.f2_supplier_provenance import check_supplier_provenance, audit_provenance_for_all

class SupplierProvenanceTests(unittest.TestCase):
    def test_missing_record(self):
        self.assertTrue(check_supplier_provenance(None))
    def test_placeholder_and_boolean_review_rejected(self):
        row = dict(supplier_source_url="https://example.org/fake",
                   independent_review=True)
        issues = check_supplier_provenance(row)
        self.assertTrue(any("placeholder" in x for x in issues))
        self.assertTrue(any("SHA-256" in x for x in issues))
        self.assertTrue(any("reviewer" in x for x in issues))
    def test_valid_structure_is_not_certification(self):
        row = dict(supplier_source_url="https://supplier.example/spec",
                   supplier_document_sha256="a"*64,
                   supplier_document_receipt_id="SYNTHETIC",
                   independent_reviewer_id="SYNTHETIC",
                   source_date="2026-11-16",
                   independent_review_date="2026-11-16",
                   independent_review=True)
        self.assertEqual(check_supplier_provenance(row), [])
        self.assertEqual(audit_provenance_for_all({"vessel":row}, {"vessel"}), {})
    def test_future_date_and_invalid_hash(self):
        row = dict(supplier_source_url="https://supplier.example/spec",
                   supplier_document_sha256="0"*63,
                   supplier_document_receipt_id="synthetic",
                   independent_reviewer_id="synthetic",
                   source_date="2099-01-01",
                   independent_review_date="2099-01-01",
                   independent_review=True)
        issues = check_supplier_provenance(row)
        self.assertTrue(any("SHA-256" in x for x in issues))
        self.assertTrue(any("future" in x for x in issues))
    def test_all_categories_fail_closed(self):
        issues = audit_provenance_for_all({}, {"vessel", "compressor"})
        self.assertEqual(set(issues), {"vessel", "compressor"})

if __name__ == "__main__":
    unittest.main()
