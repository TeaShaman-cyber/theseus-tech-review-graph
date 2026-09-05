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


    def test_repository_stops_before_examples_when_schema_metaschema_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            bad_path = root / "schemas/signal.schema.json"
            schema = json.loads(bad_path.read_text(encoding="utf-8"))
            schema["type"] = 7
            bad_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(any("signal.schema.json" in error for error in errors), errors)


    def test_repository_stops_when_shared_schema_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            bad_path = root / "schemas/common.schema.json"
            schema = json.loads(bad_path.read_text(encoding="utf-8"))
            schema["$defs"]["id"]["type"] = 7
            bad_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(any("common.schema.json" in error for error in errors), errors)

    def test_repository_reports_missing_required_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            missing = root / "schemas/signal.schema.json"
            missing.rename(root / "schemas/signal.schema.json.missing")

            errors = validate_repository(root)

            self.assertTrue(any("missing required schema: signal.schema.json" in error for error in errors), errors)


    def test_repository_rejects_unsupported_entity_example_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            (root / "examples/foo.example.json").write_text("{}\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(
                any("foo.example.json" in error and "unsupported example entity" in error for error in errors),
                errors,
            )

    def test_repository_reports_unresolved_schema_reference_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            common_path = root / "schemas/common.schema.json"
            common = json.loads(common_path.read_text(encoding="utf-8"))
            common["$id"] = "https://example.invalid/common-renamed.schema.json"
            common_path.write_text(json.dumps(common, indent=2) + "\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(
                any("unresolved schema reference" in error for error in errors),
                errors,
            )


    def test_repository_reports_unresolved_optional_schema_reference_without_example_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            actor_path = root / "schemas/actor.schema.json"
            actor = json.loads(actor_path.read_text(encoding="utf-8"))
            actor["properties"]["optional_broken_ref"] = {
                "$ref": "https://example.invalid/missing.schema.json#/$defs/value"
            }
            actor_path.write_text(json.dumps(actor, indent=2) + "\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(
                any("actor.schema.json" in error and "unresolved schema reference" in error for error in errors),
                errors,
            )

    def test_repository_rejects_duplicate_schema_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            actor_path = root / "schemas/actor.schema.json"
            source_path = root / "schemas/source.schema.json"
            actor = json.loads(actor_path.read_text(encoding="utf-8"))
            source = json.loads(source_path.read_text(encoding="utf-8"))
            source["$id"] = actor["$id"]
            source_path.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(any("duplicate schema $id" in error for error in errors), errors)

    def test_repository_resolves_refs_against_nested_id_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            actor_path = root / "schemas/actor.schema.json"
            actor = json.loads(actor_path.read_text(encoding="utf-8"))
            actor["properties"]["optional_nested_scope"] = {
                "$id": "nested/",
                "$ref": "common.schema.json#/$defs/id",
            }
            actor_path.write_text(json.dumps(actor, indent=2) + "\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(
                any("actor.schema.json" in error and "unresolved schema reference" in error for error in errors),
                errors,
            )

    def test_repository_validates_dynamic_refs_without_example_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            actor_path = root / "schemas/actor.schema.json"
            actor = json.loads(actor_path.read_text(encoding="utf-8"))
            actor["properties"]["optional_broken_dynamic_ref"] = {
                "$dynamicRef": "https://example.invalid/missing.schema.json#node"
            }
            actor_path.write_text(json.dumps(actor, indent=2) + "\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(
                any("actor.schema.json" in error and "unresolved schema reference" in error for error in errors),
                errors,
            )

    def test_repository_ignores_ref_shaped_instance_data_in_const(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            actor_path = root / "schemas/actor.schema.json"
            actor = json.loads(actor_path.read_text(encoding="utf-8"))
            actor["properties"]["literal_ref_object"] = {
                "const": {"$ref": "literal-not-a-schema-reference"}
            }
            actor_path.write_text(json.dumps(actor, indent=2) + "\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertEqual([], errors)

    def test_repository_rejects_duplicate_embedded_schema_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            duplicate_id = "https://example.invalid/embedded-resource"
            actor_path = root / "schemas/actor.schema.json"
            source_path = root / "schemas/source.schema.json"
            actor = json.loads(actor_path.read_text(encoding="utf-8"))
            source = json.loads(source_path.read_text(encoding="utf-8"))
            actor["properties"]["embedded_a"] = {"$id": duplicate_id, "type": "string"}
            source["properties"]["embedded_b"] = {"$id": duplicate_id, "type": "string"}
            actor_path.write_text(json.dumps(actor, indent=2) + "\n", encoding="utf-8")
            source_path.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(any("duplicate schema $id" in error and duplicate_id in error for error in errors), errors)


    def test_repository_accepts_percent_escaped_property_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            actor_path = root / "schemas/actor.schema.json"
            actor = json.loads(actor_path.read_text(encoding="utf-8"))
            actor["properties"]["optional%2Ffield"] = {
                "$ref": "https://teashaman-cyber.github.io/theseus-tech-review-graph/schemas/common.schema.json#/$defs/id"
            }
            actor_path.write_text(json.dumps(actor, indent=2) + "\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertEqual([], errors)

    def test_repository_rejects_duplicate_anchors_within_resource(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(ROOT / "examples", root / "examples")
            actor_path = root / "schemas/actor.schema.json"
            actor = json.loads(actor_path.read_text(encoding="utf-8"))
            actor.setdefault("$defs", {})["anchored_a"] = {"$anchor": "dup", "type": "string"}
            actor["$defs"]["anchored_b"] = {"$dynamicAnchor": "dup", "type": "string"}
            actor_path.write_text(json.dumps(actor, indent=2) + "\n", encoding="utf-8")

            errors = validate_repository(root)

            self.assertTrue(any("duplicate schema anchor" in error and "dup" in error for error in errors), errors)

    def test_check_docs_cli_fails_when_contract_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "docs", root / "docs")
            shutil.copy2(ROOT / "README.md", root / "README.md")
            (root / "docs/architecture.md").write_text("TODO\n", encoding="utf-8")
            result = __import__("subprocess").run(
                [__import__("sys").executable, str(ROOT / "scripts/check_docs.py"), str(root)],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("forbidden placeholder TODO", result.stdout + result.stderr)

    def test_docs_require_all_top_level_contract_documents(self):
        required = [
            "docs/epistemic-contract.md",
            "docs/intake-contract.md",
            "docs/lifecycle.md",
            "docs/tech-review-knowledge-adapter.md",
        ]
        for rel in required:
            with self.subTest(document=rel), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                shutil.copytree(ROOT / "docs", root / "docs")
                shutil.copy2(ROOT / "README.md", root / "README.md")
                (root / rel).unlink()
                errors = check_docs(root)
                self.assertTrue(any(f"required documentation missing: {rel}" in e for e in errors), errors)

    def test_docs_scan_nested_markdown_for_placeholders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "docs", root / "docs")
            shutil.copy2(ROOT / "README.md", root / "README.md")
            nested = root / "docs/superpowers/specs/nested.md"
            nested.parent.mkdir(parents=True, exist_ok=True)
            nested.write_text("TBD\n", encoding="utf-8")

            errors = check_docs(root)

            self.assertTrue(any("docs/superpowers/specs/nested.md" in e and "TBD" in e for e in errors), errors)

    def test_docs_report_missing_readme_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "docs", root / "docs")

            errors = check_docs(root)

            self.assertTrue(
                any("required documentation missing: README.md" in error for error in errors),
                errors,
            )

    def test_docs_preserve_replaceable_module_invariant(self):
        errors = check_docs(ROOT)
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
