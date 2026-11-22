"""Synthetic admission tests only; no actual manufacturer qualification implied."""
import unittest
from ptxflex.f2l1_supplier_admission import REQUIRED, audit_supplier_record

class SupplierAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.record = {k: "synthetic" for k in REQUIRED}
        self.record.update(document_url="https://example.org/synthetic",
            pressure_basis="absolute", rated_pressure_bar=200.0, quantity=1.0,
            equipment_scope="stationary_typeI_steel_vessel",
            provider_database="BAFU:2026", provider_version="v1.1",
            provider_reference_unit="kg_equipment", provider_process="steel forming")

    def test_review_ready_does_not_certify(self):
        r = audit_supplier_record(self.record)
        self.assertTrue(r["review_ready"])
        self.assertFalse(r["certified_design"])
        self.assertFalse(r["native_lca_accepted"])
        self.assertFalse(r["complete_station_bom"])

    def test_each_missing_field_fails_closed(self):
        for field in REQUIRED:
            with self.subTest(field=field):
                d = self.record.copy()
                del d[field]
                self.assertFalse(audit_supplier_record(d)["review_ready"])

    def test_capacity_unit_rejected(self):
        d = self.record.copy()
        d["provider_reference_unit"] = "kg_H2_capacity"
        self.assertFalse(audit_supplier_record(d)["review_ready"])

    def test_composite_provider_rejected(self):
        d = self.record.copy()
        d["provider_process"] = "automotive composite tank"
        self.assertFalse(audit_supplier_record(d)["review_ready"])

    def test_ambiguous_pressure_rejected(self):
        d = self.record.copy()
        d["pressure_basis"] = "200 bar"
        self.assertFalse(audit_supplier_record(d)["review_ready"])

    def test_bafu_version_mismatch_rejected(self):
        d = self.record.copy()
        d["provider_version"] = "v1"
        self.assertFalse(audit_supplier_record(d)["review_ready"])

    def test_invalid_quantities_rejected(self):
        for v in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(value=v):
                d = self.record.copy()
                d["quantity"] = v
                self.assertFalse(audit_supplier_record(d)["review_ready"])

    def test_invalid_pressures_rejected(self):
        for v in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(value=v):
                d = self.record.copy()
                d["rated_pressure_bar"] = v
                self.assertFalse(audit_supplier_record(d)["review_ready"])

    def test_insecure_source_rejected(self):
        d = self.record.copy()
        d["document_url"] = "http://example.org"
        self.assertFalse(audit_supplier_record(d)["review_ready"])

    def test_non_mapping_rejected(self):
        with self.assertRaises(TypeError):
            audit_supplier_record([])
