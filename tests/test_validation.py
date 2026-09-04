import json
import unittest
from pathlib import Path

from scripts.validate import load_registry, schema_for_example, validate_document
from scripts.check_docs import check_docs

ROOT = Path(__file__).resolve().parents[1]


class KnowledgeOpsValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry(ROOT / "schemas")

    def test_all_valid_examples_pass(self):
        for path in sorted((ROOT / "examples").glob("*.json")):
            with self.subTest(example=path.name):
                document = json.loads(path.read_text(encoding="utf-8"))
                schema_path = schema_for_example(path, ROOT / "schemas")
                errors = validate_document(document, schema_path, self.registry)
                self.assertEqual([], errors)

    def test_signal_missing_source_fails(self):
        path = ROOT / "tests/fixtures/invalid/signal-missing-source.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_document(document, ROOT / "schemas/signal.schema.json", self.registry)
        self.assertTrue(any("source_ids" in error for error in errors), errors)

    def test_signal_bad_epistemic_state_fails(self):
        path = ROOT / "tests/fixtures/invalid/signal-bad-state.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_document(document, ROOT / "schemas/signal.schema.json", self.registry)
        self.assertTrue(any("TRUE-ish" in error for error in errors), errors)

    def test_docs_preserve_replaceable_module_invariant(self):
        errors = check_docs(ROOT)
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
