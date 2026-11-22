import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from ptxflex.f2_supplier_receipt_bytes import verify_local_supplier_receipts


class LocalSupplierReceiptTests(unittest.TestCase):
    def test_valid_private_bytes_identity_is_not_certification(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.pdf"
            path.write_bytes(b"synthetic documentary fixture only")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            records = {"pressure_vessels": {"supplier_document_receipt_id": "R1", "supplier_document_sha256": digest}}
            result = verify_local_supplier_receipts(records, {"R1": path})
            self.assertTrue(result["passed"])
            self.assertIn("not certification", result["claim_scope"])

    def test_modified_bytes_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source"
            path.write_bytes(b"modified")
            records = {"compressor": {"supplier_document_receipt_id": "R1", "supplier_document_sha256": hashlib.sha256(b"original").hexdigest()}}
            self.assertFalse(verify_local_supplier_receipts(records, {"R1": path})["passed"])

    def test_conflicting_receipt_and_missing_file_fail(self):
        records = {"a": {"supplier_document_receipt_id": "R1", "supplier_document_sha256": "a"*64},
                   "b": {"supplier_document_receipt_id": "R1", "supplier_document_sha256": "b"*64}}
        result = verify_local_supplier_receipts(records, {})
        self.assertFalse(result["passed"])
        self.assertTrue(any("conflicting" in x for x in result["findings"]))

    def test_empty_and_undeclared_fail(self):
        self.assertFalse(verify_local_supplier_receipts({}, {})["passed"])
        self.assertFalse(verify_local_supplier_receipts({}, {"extra": "/not/there"})["passed"])

    def test_directory_is_not_original(self):
        with tempfile.TemporaryDirectory() as folder:
            records = {"a": {"supplier_document_receipt_id": "R", "supplier_document_sha256": "0"*64}}
            self.assertFalse(verify_local_supplier_receipts(records, {"R": folder})["passed"])

    def test_symlink_original_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            original = Path(folder) / "original"
            alias = Path(folder) / "alias"
            original.write_bytes(b"synthetic")
            try:
                alias.symlink_to(original)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            records = {"a": {"supplier_document_receipt_id": "R",
                             "supplier_document_sha256": hashlib.sha256(b"synthetic").hexdigest()}}
            self.assertFalse(verify_local_supplier_receipts(records, {"R": alias})["passed"])

    def test_fifo_original_is_rejected_without_blocking(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO unsupported")
        with tempfile.TemporaryDirectory() as folder:
            fifo = Path(folder) / "not_a_document"
            os.mkfifo(fifo)
            records = {"a": {"supplier_document_receipt_id": "R",
                             "supplier_document_sha256": "0" * 64}}
            self.assertFalse(verify_local_supplier_receipts(records, {"R": fifo})["passed"])


if __name__ == "__main__":
    unittest.main()
