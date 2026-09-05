#!/usr/bin/env python3
from pathlib import Path
import sys

REQUIRED = {
    'README.md': [
        'roles and contracts',
        'None is architecturally mandatory',
        'If every current product were replaced tomorrow',
    ],
    'docs/architecture.md': [
        'Every box is replaceable',
        'provenance facts, not permanent dependencies',
    ],
    'docs/knowledgeops.md': [
        'maintained state',
        'Schema validity proves shape, not truth',
    ],
    'docs/epistemic-contract.md': [],
    'docs/intake-contract.md': [],
    'docs/lifecycle.md': [],
    'docs/tech-review-knowledge-adapter.md': [],
}

FORBIDDEN_PLACEHOLDERS = ('TODO', 'TBD')

def check_docs(root: Path) -> list[str]:
    failures = []
    docs = [root / 'README.md'] + sorted((root / 'docs').rglob('*.md'))
    for path in docs:
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8')
        for marker in FORBIDDEN_PLACEHOLDERS:
            if marker in text:
                failures.append(f'{path.relative_to(root)} contains forbidden placeholder {marker}')
    for rel, phrases in REQUIRED.items():
        path = root / rel
        if not path.exists():
            failures.append(f'required documentation missing: {rel}')
            continue
        text = path.read_text(encoding='utf-8')
        for phrase in phrases:
            if phrase not in text:
                failures.append(f'{rel} missing invariant phrase: {phrase}')
    return failures


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    failures = check_docs(root)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("VERIFIED: documentation contracts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
