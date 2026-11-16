import unittest
from ptxflex.f2_supplier_bom_evidence import REQUIRED_CATEGORIES, audit_supplier_bom

class SupplierEvidenceGateTests(unittest.TestCase):
    def test_empty_is_blocked(self):
        r = audit_supplier_bom({}, site_id="site", design_basis_id="basis")
        self.assertFalse(r["passed"])
        self.assertEqual(len(r["findings"]), len(REQUIRED_CATEGORIES))

    def test_literature_empty_mass_cannot_pass(self):
        r = audit_supplier_bom({"pressure_vessels": {
            "quantity": 802, "quantity_unit": "vessels",
            "supplier_source_url": "https://example.org/paper",
            "source_date": "2026-01-01",
            "site_id": "site", "design_basis_id": "basis",
        }}, site_id="site", design_basis_id="basis")
        self.assertFalse(r["passed"])
        self.assertTrue(any("manufacturing inventory" in f for f in r["findings"]))

    def test_complete_synthetic_fixture_is_documentary_only(self):
        row = dict(site_id="site", design_basis_id="basis",
                   supplier_source_url="https://example.org/synthetic",
                   source_date="2026-11-16", quantity=1, quantity_unit="item",
                   installed_cost=1, cost_currency_year="EUR_2026",
                   pressure_qualified=True, manufacturing_inventory_verified=True,
                   independent_review=True)
        r = audit_supplier_bom({k: dict(row) for k in REQUIRED_CATEGORIES},
                               site_id="site", design_basis_id="basis")
        self.assertTrue(r["passed"])
        self.assertIn("documentary", r["claim_scope"])

    def test_nan_and_zero_and_boolean_rejected(self):
        row = dict(site_id="site", design_basis_id="basis",
                   supplier_source_url="https://example.org/synthetic",
                   source_date="2026-11-16", quantity=float("nan"),
                   quantity_unit="item", installed_cost=True,
                   cost_currency_year="EUR_2026", pressure_qualified=True,
                   manufacturing_inventory_verified=True, independent_review=True)
        r = audit_supplier_bom({k: dict(row) for k in REQUIRED_CATEGORIES},
                               site_id="site", design_basis_id="basis")
        self.assertFalse(r["passed"])
        self.assertTrue(any("nonpositive quantity" in f for f in r["findings"]))
        self.assertTrue(any("nonpositive installed_cost" in f for f in r["findings"]))

if __name__ == "__main__":
    unittest.main()
