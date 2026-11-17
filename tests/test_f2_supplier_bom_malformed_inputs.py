"""Negative tests: untrusted supplier-BOM input must fail closed without exceptions."""
import unittest
from ptxflex.f2_supplier_bom_evidence import audit_supplier_bom


class MalformedSupplierBOMTests(unittest.TestCase):
    def test_non_mapping_bom_rejected(self):
        for value in (None, [], "not a BOM", 4):
            with self.subTest(value=value):
                result = audit_supplier_bom(value, site_id="site", design_basis_id="basis")
                self.assertFalse(result["passed"])
                self.assertIn("mapping", result["findings"][0])

    def test_invalid_site_and_design_basis_rejected(self):
        for site, basis in ((None, "basis"), ("site", None), (4, "basis"), ("site", []), (" ", "basis")):
            with self.subTest(site=site, basis=basis):
                result = audit_supplier_bom({}, site_id=site, design_basis_id=basis)
                self.assertFalse(result["passed"])
                self.assertIn("missing named site or design basis", result["findings"])

    def test_non_string_extra_category_does_not_crash(self):
        result = audit_supplier_bom({2: {}, "unexpected": {}}, site_id="site", design_basis_id="basis")
        self.assertFalse(result["passed"])
        self.assertTrue(any("unrecognized categories" in x for x in result["findings"]))


if __name__ == "__main__":
    unittest.main()
