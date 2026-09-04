#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]

def load_registry(schema_dir: Path) -> Registry:
    resources = []
    for path in sorted(schema_dir.glob('*.json')):
        contents = json.loads(path.read_text(encoding='utf-8'))
        uri = contents.get('$id')
        if not uri:
            raise ValueError(f'schema missing $id: {path}')
        resources.append((uri, Resource.from_contents(contents)))
    return Registry().with_resources(resources)

def schema_for_example(example_path: Path, schema_dir: Path) -> Path:
    suffix = '.example.json'
    if not example_path.name.endswith(suffix):
        raise ValueError(f'not an example filename: {example_path.name}')
    entity = example_path.name[:-len(suffix)]
    schema_path = schema_dir / f'{entity}.schema.json'
    if not schema_path.exists():
        raise FileNotFoundError(f'schema not found for {example_path.name}: {schema_path}')
    return schema_path

def validate_document(document: dict, schema_path: Path, registry: Registry) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    cls = validator_for(schema)
    cls.check_schema(schema)
    validator = cls(schema, registry=registry, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda e: (list(e.absolute_path), e.message))
    result = []
    for error in errors:
        path = '$'
        for part in error.absolute_path:
            path += f'[{part}]' if isinstance(part, int) else f'.{part}'
        result.append(f'{path}: {error.message}')
    return result

def validate_repository(root: Path = ROOT) -> list[str]:
    schema_dir = root / 'schemas'
    registry = load_registry(schema_dir)
    failures = []
    for path in sorted(schema_dir.glob('*.json')):
        schema = json.loads(path.read_text(encoding='utf-8'))
        try:
            validator_for(schema).check_schema(schema)
        except Exception as exc:
            failures.append(f'schema {path.name}: {exc}')
    for path in sorted((root / 'examples').glob('*.example.json')):
        document = json.loads(path.read_text(encoding='utf-8'))
        schema_path = schema_for_example(path, schema_dir)
        for error in validate_document(document, schema_path, registry):
            failures.append(f'example {path.name}: {error}')
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
            print(f'FAIL: {failure}')
        return 1
    print('VERIFIED: schemas, synthetic examples, and documentation contracts')
    return 0

if __name__ == '__main__':
    sys.exit(main())
