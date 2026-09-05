import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.validate import load_registry, validate_cross_references, validate_document

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/needle-watch-33902305526-attempt-1.json"
CANDIDATE_ID = "33e0eef0389227c99cd910a1335ec33aadc68d7dc737989a8d9816326578ad6e"


def run_adapter():
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/adapt_needle_receipt.py"),
            str(FIXTURE),
            "--candidate-id",
            CANDIDATE_ID,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


class NeedleAdapterTests(unittest.TestCase):
    def test_real_needle_receipt_projects_deterministically_into_existing_contracts(self):
        first = run_adapter()
        self.assertEqual(0, first.returncode, first.stdout + first.stderr)
        second = run_adapter()
        self.assertEqual(0, second.returncode, second.stdout + second.stderr)
        self.assertEqual(first.stdout, second.stdout)

        bundle = json.loads(first.stdout)
        source = bundle["source"]
        signal = bundle["signal"]
        analysis = bundle["analysis"]

        suffix = CANDIDATE_ID
        self.assertEqual(f"source.needle.{suffix}", source["id"])
        self.assertEqual(f"signal.needle.{suffix}", signal["id"])
        self.assertEqual(f"analysis.needle.{suffix}", analysis["id"])

        self.assertEqual("yairpatch/flyweight", source["title"])
        self.assertEqual("https://github.com/yairpatch/flyweight", source["url"])
        self.assertEqual([source["id"]], signal["source_ids"])
        self.assertEqual([signal["id"]], analysis["evidence_signal_ids"])

        self.assertEqual("UNVERIFIED", signal["epistemic_state"])
        self.assertEqual("CANDIDATE", signal["currentness_state"])
        self.assertEqual("HYPOTHESIS", analysis["epistemic_state"])
        self.assertEqual("CANDIDATE", analysis["currentness_state"])
        self.assertIn("33902305526-attempt-1", signal["provenance"]["origin_label"])
        self.assertIn("status=ok", signal["provenance"]["origin_label"])
        self.assertIn("receipt metadata", analysis["thesis"])

        registry = load_registry(ROOT / "schemas")
        for entity, document in (("source", source), ("signal", signal), ("analysis", analysis)):
            errors = validate_document(document, ROOT / f"schemas/{entity}.schema.json", registry)
            self.assertEqual([], errors)

        self.assertEqual(
            [],
            validate_cross_references(
                [
                    (Path("source.json"), source),
                    (Path("signal.json"), signal),
                    (Path("analysis.json"), analysis),
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
