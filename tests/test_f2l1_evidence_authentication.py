"""Synthetic-only regression tests: integrity is never OEM or LCA validation."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from ptxflex.f2l1_evidence_authentication import audit_evidence_manifest

class EvidenceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "synthetic.txt").write_bytes(b"SYNTHETIC TEST ONLY")
        self.record = {
            "id": "synthetic", "role": "manufacturer_document",
            "relative_path": "synthetic.txt",
            "sha256": hashlib.sha256(b"SYNTHETIC TEST ONLY").hexdigest(),
        }

    def audit(self):
        return audit_evidence_manifest({"records": [self.record]}, self.root)

    def test_matching_hash_is_not_authentication(self):
        result = self.audit()
        self.assertTrue(result["all_files_hash_verified"])
        self.assertFalse(result["f2_gate_passed"])
        self.assertFalse(result["l1_gate_passed"])
        self.assertFalse(result["complete_industrial_lca_admitted"])
        self.assertFalse(result["records"][0]["manufacturer_authenticity_verified"])

    def test_modified_bytes_fail(self):
        (self.root / "synthetic.txt").write_bytes(b"ALTERED")
        self.assertFalse(self.audit()["all_files_hash_verified"])

    def test_missing_file_is_unknown(self):
        (self.root / "synthetic.txt").unlink()
        result = self.audit()
        self.assertFalse(result["all_files_hash_verified"])
        self.assertIsNone(result["records"][0]["sha256_observed"])

    def test_path_traversal_rejected(self):
        self.record["relative_path"] = "../outside"
        with self.assertRaises(ValueError):
            self.audit()

    def test_absolute_path_rejected(self):
        self.record["relative_path"] = "/etc/passwd"
        with self.assertRaises(ValueError):
            self.audit()

    def test_invalid_digest_rejected(self):
        self.record["sha256"] = "0" * 63
        with self.assertRaises(ValueError):
            self.audit()

    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):
            audit_evidence_manifest({"records": [self.record, self.record]}, self.root)

    def test_unknown_role_rejected(self):
        self.record["role"] = "complete_certified_lca"
        with self.assertRaises(ValueError):
            self.audit()

    def test_symlink_rejected(self):
        (self.root / "link").symlink_to(self.root / "synthetic.txt")
        self.record["relative_path"] = "link"
        with self.assertRaises(ValueError):
            self.audit()

    def test_empty_manifest_rejected(self):
        with self.assertRaises(ValueError):
            audit_evidence_manifest({"records": []}, self.root)

if __name__ == "__main__":
    unittest.main()
