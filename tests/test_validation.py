import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate import load_registry, schema_for_example, validate_document, validate_repository
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

    def test_repository_rejects_missing_required_entity_example(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            examples_dir = root / "examples"
            examples_dir.mkdir()
            for path in sorted((ROOT / "examples").glob("*.example.json")):
                if path.name != "analysis.example.json":
                    shutil.copy2(path, examples_dir / path.name)

            errors = validate_repository(root)

            self.assertTrue(
                any("missing required example: analysis.example.json" in error for error in errors),
                errors,
            )

    def test_repository_rejects_dangling_cross_entity_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            source_path = root / "examples/source.example.json"
            source = json.loads(source_path.read_text(encoding="utf-8"))
            source["id"] = "source.synthetic.release-renamed"
            source_path.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(
                any(
                    "signal.example.json" in error
                    and "source_ids" in error
                    and "source.synthetic.release-001" in error
                    for error in errors
                ),
                errors,
            )

    def test_repository_rejects_inverted_brief_period(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            brief_path = root / "examples/brief.example.json"
            brief = json.loads(brief_path.read_text(encoding="utf-8"))
            brief["period_start"] = "2026-09-07"
            brief["period_end"] = "2026-09-06"
            brief_path.write_text(json.dumps(brief, indent=2) + "\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(
                any("brief.example.json" in error and "period_start" in error and "period_end" in error for error in errors),
                errors,
            )

    def test_repository_rejects_untracked_json_in_examples(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            (root / "examples/untracked.json").write_text("{not-json}\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(
                any("untracked.json" in error and "unexpected example filename" in error for error in errors),
                errors,
            )

    def test_repository_rejects_nested_untracked_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / 'schemas', root / 'schemas')
            shutil.copytree(ROOT / 'examples', root / 'examples')
            nested = root / 'examples/archive'
            nested.mkdir()
            (nested / 'untracked.json').write_text('{}\n', encoding='utf-8')

            errors = validate_repository(root)

            self.assertTrue(
                any('archive/untracked.json' in error and 'unexpected example filename' in error for error in errors),
                errors,
            )

    def test_repository_reports_malformed_tracked_example_as_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            bad_path = root / "examples/signal.example.json"
            bad_path.write_text("{not-json}\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(
                any(
                    "signal.example.json" in error
                    and "invalid JSON" in error
                    for error in errors
                ),
                errors,
            )

    def test_repository_reports_malformed_schema_as_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            bad_path = root / "schemas/signal.schema.json"
            bad_path.write_text("{not-json}\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(
                any(
                    "signal.schema.json" in error
                    and "invalid schema" in error
                    for error in errors
                ),
                errors,
            )

    def test_repository_reports_non_object_example_as_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            bad_path = root / "examples/signal.example.json"
            bad_path.write_text("null\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(
                any(
                    "signal.example.json" in error
                    and "is not of type 'object'" in error
                    for error in errors
                ),
                errors,
            )

    def test_docs_preserve_replaceable_module_invariant(self):
        errors = check_docs(ROOT)
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
