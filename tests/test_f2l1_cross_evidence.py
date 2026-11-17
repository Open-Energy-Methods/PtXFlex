"""Synthetic-only cross-ledger adversarial tests; no supplier claims."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ptxflex.f2l1_cross_evidence import audit_f2l1_cross_evidence
from ptxflex.f2l1_supplier_admission import REQUIRED


class CrossEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.supplier = {key: "SYNTHETIC" for key in REQUIRED}
        self.supplier.update(
            product_model="TEST-ONLY", document_revision="R0",
            pressure_basis="absolute", rated_pressure_bar=200.0,
            quantity=1.0, document_url="https://example.org/synthetic",
            provider_database="BAFU:2026", provider_version="v1.1",
            equipment_scope="stationary_typeI_steel_vessel",
            provider_reference_unit="kg_equipment",
            provider_process="synthetic steel manufacturing",
        )
        self.manifest = {"records": []}
        for role in ("manufacturer_document", "pressure_conformity", "installed_bom", "native_lci_provider"):
            name = role + ".txt"
            data = ("SYNTHETIC " + role).encode()
            (self.root / name).write_bytes(data)
            self.manifest["records"].append(dict(
                id=role, role=role, relative_path=name,
                sha256=hashlib.sha256(data).hexdigest(),
                product_model="TEST-ONLY", document_revision="R0",
            ))

    def run_audit(self):
        return audit_f2l1_cross_evidence(self.supplier, self.manifest, self.root)

    def test_complete_synthetic_still_not_certified(self):
        r = self.run_audit()
        self.assertTrue(r["ready_for_external_authentication_review"])
        for key in ("manufacturer_authenticated", "certified_design", "native_lca_accepted",
                    "complete_station_bom", "f2_gate_passed", "l1_gate_passed"):
            self.assertFalse(r[key])

    def test_missing_role(self):
        self.manifest["records"].pop()
        r = self.run_audit()
        self.assertIn("missing_evidence_roles", r["rejection_reasons"])

    def test_duplicate_role(self):
        r = dict(self.manifest["records"][0], id="second")
        self.manifest["records"].append(r)
        self.assertIn("duplicate_evidence_roles", self.run_audit()["rejection_reasons"])

    def test_mismatched_product(self):
        self.manifest["records"][0]["product_model"] = "OTHER"
        self.assertIn("evidence_supplier_revision_binding_mismatch", self.run_audit()["rejection_reasons"])

    def test_mismatched_revision(self):
        self.manifest["records"][1]["document_revision"] = "R1"
        self.assertIn("evidence_supplier_revision_binding_mismatch", self.run_audit()["rejection_reasons"])

    def test_missing_binding(self):
        del self.manifest["records"][0]["product_model"]
        self.assertFalse(self.run_audit()["ready_for_external_authentication_review"])

    def test_tampered_file(self):
        (self.root / "installed_bom.txt").write_text("ALTERED")
        self.assertIn("evidence_bytes_not_verified", self.run_audit()["rejection_reasons"])

    def test_invalid_supplier(self):
        self.supplier["provider_reference_unit"] = "kg_H2_capacity"
        self.assertIn("supplier_metadata_not_review_ready", self.run_audit()["rejection_reasons"])


if __name__ == "__main__":
    unittest.main()
