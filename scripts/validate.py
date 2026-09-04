#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENTITIES = {
    "actor": "Actor",
    "analysis": "Analysis",
    "brief": "Brief",
    "signal": "Signal",
    "source": "Source",
    "theme": "Theme",
}
REFERENCE_FIELDS = {
    "Analysis": {
        "evidence_signal_ids": "Signal",
        "theme_ids": "Theme",
    },
    "Brief": {
        "signal_ids": "Signal",
        "theme_ids": "Theme",
    },
    "Signal": {
        "source_ids": "Source",
        "actor_ids": "Actor",
        "theme_ids": "Theme",
    },
}


def load_registry(schema_dir: Path) -> Registry:
    resources = []
    seen_uris = {}
    for path in sorted(schema_dir.glob("*.json")):
        try:
            contents = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(contents, dict):
                raise ValueError("top-level schema must be an object")
            uri = contents.get("$id")
            if not uri:
                raise ValueError("missing $id")
            if uri in seen_uris:
                raise ValueError(f"duplicate schema $id {uri!r}; already defined by {seen_uris[uri]}")
            seen_uris[uri] = path.name
            resources.append((uri, Resource.from_contents(contents)))
        except Exception as exc:
            raise ValueError(f"invalid schema {path.name}: {exc}") from exc
    return Registry().with_resources(resources)


def schema_for_example(example_path: Path, schema_dir: Path) -> Path:
    suffix = ".example.json"
    if not example_path.name.endswith(suffix):
        raise ValueError(f"not an example filename: {example_path.name}")
    entity = example_path.name[: -len(suffix)]
    schema_path = schema_dir / f"{entity}.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"schema not found for {example_path.name}: {schema_path}")
    return schema_path


def validate_document(document: dict, schema_path: Path, registry: Registry) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    cls = validator_for(schema)
    cls.check_schema(schema)
    validator = cls(schema, registry=registry, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda e: (list(e.absolute_path), e.message))
    result = []
    for error in errors:
        path = "$"
        for part in error.absolute_path:
            path += f"[{part}]" if isinstance(part, int) else f".{part}"
        result.append(f"{path}: {error.message}")
    return result


def validate_cross_field_invariants(path: Path, document: dict) -> list[str]:
    failures = []
    if document.get("type") == "Brief":
        period_start = document.get("period_start")
        period_end = document.get("period_end")
        if isinstance(period_start, str) and isinstance(period_end, str) and period_start > period_end:
            failures.append(
                f"example {path.name}: $.period_start must be <= $.period_end "
                f"({period_start!r} > {period_end!r})"
            )
    return failures


def validate_cross_references(documents: list[tuple[Path, dict]]) -> list[str]:
    failures = []
    index = {}
    for path, document in documents:
        document_id = document.get("id")
        document_type = document.get("type")
        if not isinstance(document_id, str) or not isinstance(document_type, str):
            continue
        if document_id in index:
            other_path, _ = index[document_id]
            failures.append(
                f"example {path.name}: duplicate id {document_id!r}; already defined by {other_path.name}"
            )
        else:
            index[document_id] = (path, document_type)

    for path, document in documents:
        document_type = document.get("type")
        for field, expected_type in REFERENCE_FIELDS.get(document_type, {}).items():
            references = document.get(field, [])
            if not isinstance(references, list):
                continue
            for reference_id in references:
                if not isinstance(reference_id, str):
                    continue
                target = index.get(reference_id)
                if target is None:
                    failures.append(
                        f"example {path.name}: $.{field}: dangling reference {reference_id!r}; expected {expected_type}"
                    )
                    continue
                target_path, actual_type = target
                if actual_type != expected_type:
                    failures.append(
                        f"example {path.name}: $.{field}: reference {reference_id!r} resolves to {actual_type} "
                        f"in {target_path.name}; expected {expected_type}"
                    )
    return failures


def validate_repository(root: Path = ROOT) -> list[str]:
    schema_dir = root / "schemas"
    examples_dir = root / "examples"
    failures = []
    invalid_schema_names = set()
    required_schema_names = {"common.schema.json"} | {f"{entity}.schema.json" for entity in REQUIRED_ENTITIES}
    present_schema_names = {path.name for path in schema_dir.glob("*.json")}
    for required_name in sorted(required_schema_names - present_schema_names):
        failures.append(f"missing required schema: {required_name}")
    if failures:
        return failures

    try:
        registry = load_registry(schema_dir)
    except Exception as exc:
        failures.append(str(exc))
        return failures
    for path in sorted(schema_dir.glob("*.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        try:
            validator_for(schema).check_schema(schema)
        except Exception as exc:
            failures.append(f"schema {path.name}: {exc}")
            invalid_schema_names.add(path.name)
    if failures:
        return failures

    for path in sorted(schema_dir.glob("*.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resolver = registry.resolver(schema.get("$id", ""))
        stack = [("$", schema)]
        while stack:
            location, node = stack.pop()
            if isinstance(node, dict):
                ref = node.get("$ref")
                if isinstance(ref, str):
                    try:
                        resolver.lookup(ref)
                    except Unresolvable as exc:
                        failures.append(
                            f"schema {path.name}: unresolved schema reference at {location}: {ref}: {exc}"
                        )
                for key, value in node.items():
                    stack.append((f"{location}.{key}", value))
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    stack.append((f"{location}[{index}]", value))
    if failures:
        return failures

    json_paths = sorted(examples_dir.rglob("*.json"))
    example_paths = []
    for path in json_paths:
        relative = path.relative_to(examples_dir)
        if path.parent != examples_dir or not path.name.endswith(".example.json"):
            failures.append(f"unexpected example filename: {relative.as_posix()}")
            continue
        entity = path.name[: -len(".example.json")]
        if entity not in REQUIRED_ENTITIES:
            failures.append(f"unsupported example entity: {path.name}")
            continue
        example_paths.append(path)
    present_names = {path.name for path in example_paths}
    for entity in REQUIRED_ENTITIES:
        required_name = f"{entity}.example.json"
        if required_name not in present_names:
            failures.append(f"missing required example: {required_name}")

    documents = []
    for path in example_paths:
        try:
            raw = path.read_text(encoding="utf-8")
            document = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            failures.append(f"example {path.name}: invalid JSON: {exc}")
            continue
        schema_path = schema_for_example(path, schema_dir)
        if schema_path.name in invalid_schema_names:
            failures.append(f"example {path.name}: skipped validation because schema {schema_path.name} is invalid")
            continue
        try:
            validation_errors = validate_document(document, schema_path, registry)
        except Exception as exc:
            if not isinstance(exc.__cause__, Unresolvable):
                raise
            failures.append(f"example {path.name}: unresolved schema reference: {exc}")
            continue
        for error in validation_errors:
            failures.append(f"example {path.name}: {error}")
        if not isinstance(document, dict):
            continue
        documents.append((path, document))
        failures.extend(validate_cross_field_invariants(path, document))

    failures.extend(validate_cross_references(documents))
    return failures


def main() -> int:
    try:
        from scripts.check_docs import check_docs
    except ModuleNotFoundError:
        from check_docs import check_docs
    failures = validate_repository(ROOT)
    failures.extend(check_docs(ROOT))
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("VERIFIED: schemas, synthetic examples, cross-entity references, and documentation contracts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
