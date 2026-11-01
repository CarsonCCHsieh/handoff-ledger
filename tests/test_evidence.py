import copy
import json
from pathlib import Path
import tempfile
import unittest

from handoff_ledger.evidence import EvidenceVault

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sample-project"


class EvidenceIntegrityTests(unittest.TestCase):
    def test_recorded_failure_and_unrun_remain_distinct(self):
        vault = EvidenceVault(FIXTURE)
        self.assertEqual(vault.check_claim("C01")["classification"], "supported")
        self.assertEqual(vault.check_claim("C02")["classification"], "contradicted")
        self.assertEqual(vault.check_claim("C03")["classification"], "unknown")

    def test_forged_or_altered_citation_is_rejected(self):
        vault = EvidenceVault(FIXTURE)
        facts = [vault.check_claim(key) for key in vault.claims]
        report = {
            "claims": [{"id": item["claim_id"], "status": item["classification"], "evidence_refs": [item["reference"]["id"]]} for item in facts],
            "references": [item["reference"] for item in facts],
            "unknowns": ["Review not run"], "risks": ["Migration failed"],
        }
        self.assertEqual(vault.validate_report(report), [])
        forged = copy.deepcopy(report)
        forged["references"][0]["excerpt"] = "All checks passed."
        self.assertTrue(any("altered" in item for item in vault.validate_report(forged)))
        lied = copy.deepcopy(report)
        lied["claims"][1]["status"] = "supported"
        self.assertTrue(any("Classification" in item for item in vault.validate_report(lied)))
        hidden = copy.deepcopy(report)
        hidden["unknowns"] = []
        hidden["risks"] = []
        self.assertEqual(len(vault.validate_report(hidden)), 2)

    def test_fixture_hash_and_path_boundary_are_enforced(self):
        with tempfile.TemporaryDirectory(dir=FIXTURE.parents[1] / ".tmp") as folder:
            root = Path(folder)
            manifest = json.loads((FIXTURE / "manifest.json").read_text("utf-8"))
            manifest["evidence"][0]["source"] = "../outside.txt"
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "escapes"):
                EvidenceVault(root)

    def test_modified_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=FIXTURE.parents[1] / ".tmp") as folder:
            root = Path(folder)
            for path in FIXTURE.iterdir():
                (root / path.name).write_bytes(path.read_bytes())
            (root / "checks.jsonl").write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                EvidenceVault(root)


if __name__ == "__main__":
    unittest.main()
