#!/usr/bin/env python3
from pathlib import Path

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
}

FORBIDDEN_PLACEHOLDERS = ('TODO', 'TBD')

def check_docs(root: Path) -> list[str]:
    failures = []
    docs = [root / 'README.md'] + sorted((root / 'docs').glob('*.md'))
    for path in docs:
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
