#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

try:
    from scripts.validate import load_registry, validate_cross_references, validate_document
except ModuleNotFoundError:
    from validate import load_registry, validate_cross_references, validate_document

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RECEIPT_SCHEMA = "needle-watch-receipt-v0.2"


def iso_date(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) < 10:
        raise ValueError(f"missing or invalid {field}")
    return value[:10]


def select_candidate(receipt: dict, candidate_id: str) -> tuple[dict, dict]:
    if receipt.get("schema_version") != EXPECTED_RECEIPT_SCHEMA:
        raise ValueError(
            f"unsupported Needle receipt schema {receipt.get('schema_version')!r}; "
            f"expected {EXPECTED_RECEIPT_SCHEMA!r}"
        )

    matches = [candidate for candidate in receipt.get("candidates", []) if candidate.get("candidate_id") == candidate_id]
    if len(matches) != 1:
        raise ValueError(f"candidate_id {candidate_id!r} matched {len(matches)} candidates")
    candidate = matches[0]

    source_id = candidate.get("source_id")
    health_matches = [item for item in receipt.get("source_health", []) if item.get("source_id") == source_id]
    if len(health_matches) != 1:
        raise ValueError(f"source health for {source_id!r} matched {len(health_matches)} records")
    return candidate, health_matches[0]


def project_candidate(receipt: dict, candidate_id: str) -> dict:
    candidate, health = select_candidate(receipt, candidate_id)
    suffix = candidate_id
    source_object_id = f"source.needle.{suffix}"
    signal_object_id = f"signal.needle.{suffix}"
    analysis_object_id = f"analysis.needle.{suffix}"

    source = {
        "id": source_object_id,
        "type": "Source",
        "title": candidate["title"],
        "source_class": "REPOSITORY" if candidate.get("source_class") == "github_repo" else "OTHER",
        "url": candidate["canonical_url"],
        "retrieved_at": iso_date(receipt["generated_at"], "generated_at"),
        "notes": (
            f"Needle Watch candidate_id={candidate_id}; run_id={receipt['run_id']}; "
            f"source_identity={candidate.get('source_identity')}; "
            f"upstream_revision={candidate.get('upstream_revision')}; "
            f"content_fingerprint={candidate.get('content_fingerprint')}; "
            f"discovery_route={candidate.get('discovery_route')}; "
            f"source_health.status={health.get('status')}"
        ),
    }
    published = candidate.get("published_or_pushed_at")
    if published:
        source["published_at"] = iso_date(published, "published_or_pushed_at")

    matched_lines = candidate.get("matched_watch_lines") or []
    matched_text = ", ".join(matched_lines) if matched_lines else "none"
    health_status = health.get("status")
    signal = {
        "id": signal_object_id,
        "type": "Signal",
        "observed_on": iso_date(candidate["observed_at"], "observed_at"),
        "claim": f"Needle Watch observed {candidate['title']} and matched watch lines: {matched_text}.",
        "why_it_matters": (
            "This discovery metadata identifies a candidate for primary-source review; "
            "it does not establish technical behavior or experimental value."
        ),
        "source_ids": [source_object_id],
        "epistemic_state": "UNVERIFIED" if health_status == "ok" else "DEGRADED",
        "currentness_state": "CANDIDATE",
        "provenance": {
            "producer_class": "SCHEDULED_AGENT",
            "intake_class": "FILESYSTEM",
            "origin_label": (
                f"needle-watch:{receipt['schema_version']}:run={receipt['run_id']}:"
                f"source={candidate.get('source_id')}:status={health_status}:candidate={candidate_id}"
            ),
        },
    }

    analysis = {
        "id": analysis_object_id,
        "type": "Analysis",
        "title": f"Experiment follow-up candidate: {candidate['title']}",
        "thesis": (
            f"Investigate {candidate['title']} for possible relevance to {matched_text}; "
            "receipt metadata alone does not establish technical behavior, efficacy, or experiment suitability."
        ),
        "evidence_signal_ids": [signal_object_id],
        "epistemic_state": "HYPOTHESIS",
        "currentness_state": "CANDIDATE",
    }

    return {"source": source, "signal": signal, "analysis": analysis}


def validate_bundle(bundle: dict) -> list[str]:
    registry = load_registry(ROOT / "schemas")
    failures = []
    documents = []
    for entity in ("source", "signal", "analysis"):
        document = bundle[entity]
        schema_path = ROOT / f"schemas/{entity}.schema.json"
        failures.extend(
            f"{entity}: {error}" for error in validate_document(document, schema_path, registry)
        )
        documents.append((Path(f"{entity}.json"), document))
    failures.extend(validate_cross_references(documents))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Project one Needle Watch candidate into existing KnowledgeOps objects.")
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--candidate-id", required=True)
    args = parser.parse_args()

    try:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
        bundle = project_candidate(receipt, args.candidate_id)
        failures = validate_bundle(bundle)
        if failures:
            for failure in failures:
                print(f"FAIL: {failure}", file=sys.stderr)
            return 1
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    json.dump(bundle, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
