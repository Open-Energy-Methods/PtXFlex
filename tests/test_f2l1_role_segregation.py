"""Synthetic adversarial tests: evidence byte reuse must fail closed."""
import hashlib
import unittest

from ptxflex.f2l1_role_segregation import audit_role_segregation

ROLES = ("manufacturer_document", "pressure_conformity", "installed_bom", "native_lci_provider")


def fixture():
    return {"records": [
        {"role": role, "relative_path": role + ".pdf",
         "sha256": hashlib.sha256(role.encode()).hexdigest()}
        for role in ROLES
    ]}


class RoleSegregationTests(unittest.TestCase):
    def test_distinct_synthetic_roles_still_not_certified(self):
        result = audit_role_segregation(fixture())
        self.assertTrue(result["role_segregation_complete"])
        for key in ("manufacturer_authenticated", "physical_design_certified",
                    "native_bafu_lca_accepted", "f2_gate_passed", "l1_gate_passed"):
            self.assertFalse(result[key])

    def test_same_file_reused_for_two_roles(self):
        m = fixture()
        m["records"][1]["relative_path"] = m["records"][0]["relative_path"]
        self.assertIn("reused_evidence_path", audit_role_segregation(m)["rejection_reasons"])

    def test_different_file_names_same_bytes(self):
        m = fixture()
        m["records"][1]["sha256"] = m["records"][0]["sha256"]
        self.assertIn("reused_evidence_bytes_across_roles", audit_role_segregation(m)["rejection_reasons"])

    def test_duplicate_role(self):
        m = fixture()
        m["records"][1]["role"] = m["records"][0]["role"]
        self.assertIn("duplicate_evidence_role", audit_role_segregation(m)["rejection_reasons"])

    def test_missing_role(self):
        m = fixture()
        m["records"].pop()
        self.assertIn("missing_evidence_role", audit_role_segregation(m)["rejection_reasons"])

    def test_invalid_hash(self):
        m = fixture()
        m["records"][0]["sha256"] = "NOT-A-HASH"
        with self.assertRaises(ValueError):
            audit_role_segregation(m)

    def test_unknown_role(self):
        m = fixture()
        m["records"][0]["role"] = "synthetic_certification"
        with self.assertRaises(ValueError):
            audit_role_segregation(m)

    def test_empty_records(self):
        with self.assertRaises(ValueError):
            audit_role_segregation({"records": []})


if __name__ == "__main__":
    unittest.main()
