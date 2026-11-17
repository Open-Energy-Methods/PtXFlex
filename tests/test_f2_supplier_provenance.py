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
        row = dict(supplier_source_url="https://manufacturer.org/spec",
                   supplier_document_sha256="a"*64,
                   supplier_document_receipt_id="SYNTHETIC",
                   independent_reviewer_id="SYNTHETIC",
                   source_date="2026-11-16",
                   independent_review_date="2026-11-16",
                   independent_review=True)
        self.assertEqual(check_supplier_provenance(row), [])
        self.assertEqual(audit_provenance_for_all({"vessel":row}, {"vessel"}), {})
    def test_future_date_and_invalid_hash(self):
        row = dict(supplier_source_url="https://manufacturer.org/spec",
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


    def test_reserved_and_local_hosts_are_rejected(self):
        base = dict(supplier_document_sha256="a"*64,
                    supplier_document_receipt_id="SYNTHETIC",
                    independent_reviewer_id="SYNTHETIC",
                    source_date="2026-11-16",
                    independent_review_date="2026-11-16",
                    independent_review=True)
        for url in ("https://manufacturer.org/spec", "https://example.org.evil.test/doc",
                    "https://localhost/doc", "https://vendor.local/spec",
                    "https://127.0.0.1/spec", "https://192.168.1.2/doc",
                    "https://supplier.invalid/doc", "https://supplier.test/doc",
                    "https://vendor.example.com/doc", "https://vendor.com/doc#fragment"):
            with self.subTest(url=url):
                self.assertTrue(any("URL" in issue for issue in
                                    check_supplier_provenance(dict(base, supplier_source_url=url))))
        self.assertEqual(check_supplier_provenance(dict(base,
            supplier_source_url="https://manufacturer.org/specification.pdf")), [])

    def test_mapping_subclass_supported(self):
        from types import MappingProxyType
        row = dict(supplier_source_url="https://manufacturer.org/specification.pdf",
                   supplier_document_sha256="a"*64,
                   supplier_document_receipt_id="SYNTHETIC",
                   independent_reviewer_id="SYNTHETIC",
                   source_date="2026-11-16",
                   independent_review_date="2026-11-16",
                   independent_review=True)
        self.assertEqual(check_supplier_provenance(MappingProxyType(row)), [])

if __name__ == "__main__":
    unittest.main()
