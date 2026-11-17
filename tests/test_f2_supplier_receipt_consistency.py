"""Cross-category supplier document receipt consistency; synthetic evidence only."""
import unittest
from ptxflex.f2_supplier_bom_evidence import audit_supplier_bom, REQUIRED_CATEGORIES

class ReceiptConsistencyTests(unittest.TestCase):
    def fixture(self):
        row = {
            "site_id": "synthetic-site", "design_basis_id": "synthetic-basis",
            "supplier_source_url": "https://supplier.example.invalid/doc",
            "source_date": "2026-01-01",
            "supplier_document_receipt_id": "synthetic-receipt",
            "supplier_document_sha256": "a" * 64,
            "independent_reviewer_id": "synthetic-reviewer",
            "independent_review_date": "2026-01-02",
            "independent_review": True, "quantity": 1, "quantity_unit": "item",
            "installed_cost": 1, "cost_currency_year": "EUR_2026",
            "pressure_qualified": True, "manufacturing_inventory_verified": True,
        }
        return {name: dict(row) for name in REQUIRED_CATEGORIES}

    def audit(self, records):
        return audit_supplier_bom(records, site_id="synthetic-site", design_basis_id="synthetic-basis")

    def test_one_receipt_two_hashes_rejected(self):
        records = self.fixture()
        records["pressure_vessels"]["supplier_document_sha256"] = "b" * 64
        result = self.audit(records)
        self.assertFalse(result["passed"])
        self.assertTrue(any("document receipt conflicts" in x for x in result["findings"]))

    def test_same_receipt_same_hash_not_cross_category_conflict(self):
        result = self.audit(self.fixture())
        self.assertFalse(result["passed"])  # Reserved URL must remain inadmissible.
        self.assertFalse(any("document receipt conflicts" in x for x in result["findings"]))

    def test_missing_receipt_remains_blocked(self):
        records = self.fixture()
        del records["pressure_vessels"]["supplier_document_receipt_id"]
        result = self.audit(records)
        self.assertFalse(result["passed"])
        self.assertTrue(any("missing supplier_document_receipt_id" in x for x in result["findings"]))

if __name__ == "__main__":
    unittest.main()
