import copy
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from scripts.check_docs import check_docs

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "experimental/knowledge-mutation-receipt.schema.json"
EXAMPLE = ROOT / "experimental/knowledge-mutation-receipt.example.json"


class KnowledgeOrchestrationTests(unittest.TestCase):
    def test_reference_mutation_receipt_validates(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        document = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual([], list(validator.iter_errors(document)))

    def test_repair_count_is_bounded_to_one(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        document = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        document["repair_count"] = 2
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertTrue(any(error.validator == "maximum" for error in validator.iter_errors(document)))

    def test_reject_or_defer_cannot_claim_a_write(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        document = copy.deepcopy(json.loads(EXAMPLE.read_text(encoding="utf-8")))
        document.update(
            {
                "decision": "REJECT_OR_DEFER",
                "target": None,
                "writer_route": None,
                "write_status": "COMPLETED",
                "verification_route": None,
                "postcondition_status": "NOT_APPLICABLE",
                "repair_count": 0,
            }
        )
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertNotEqual([], list(validator.iter_errors(document)))

    def test_orchestration_contract_doc_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            for rel in (
                "README.md",
                "docs/architecture.md",
                "docs/knowledgeops.md",
                "docs/epistemic-contract.md",
                "docs/intake-contract.md",
                "docs/lifecycle.md",
                "docs/tech-review-knowledge-adapter.md",
            ):
                source = ROOT / rel
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            failures = check_docs(root)
            self.assertTrue(
                any("docs/knowledge-orchestration-plane.md" in failure for failure in failures),
                failures,
            )


if __name__ == "__main__":
    unittest.main()
