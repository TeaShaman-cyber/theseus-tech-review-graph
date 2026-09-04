# KnowledgeOps v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first public, self-validating reference implementation of Theseus KnowledgeOps using the tech-review graph as the initial vertical.

**Architecture:** Keep current producers, intake stores, and memory backends replaceable. GitHub contains only vendor-neutral contracts, schemas, synthetic examples, a deterministic validator, and CI; no private Basic Memory export or live Notion synchronization is part of v0.1.

**Tech Stack:** Markdown, Mermaid, JSON Schema Draft 2020-12, Python 3.11, `jsonschema`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-04-theseus-tech-review-graph-design.md`

## Global Constraints

- Current products are replaceable modules, never architectural invariants.
- Keep epistemic status separate from temporal/currentness lifecycle.
- Repository examples must be synthetic and contain no private Basic Memory or Notion content.
- v0.1 has no automatic synchronization, crawler, vector store, LLM judge, or autonomous publication path.
- The same deterministic validator must run locally and in GitHub Actions.
- `memory-tech-brief` is documented as an implementation of the vendor-neutral Tech Review Knowledge Adapter role.

---

### Task 1: Public architecture and contracts

**Files:**
- Modify: `README.md`
- Create: `docs/architecture.md`
- Create: `docs/knowledgeops.md`
- Create: `docs/epistemic-contract.md`
- Create: `docs/lifecycle.md`
- Create: `docs/intake-contract.md`
- Create: `docs/tech-review-knowledge-adapter.md`

**Interfaces:**
- Consumes: approved design spec.
- Produces: human/agent-readable public contract for all later schema and validator tasks.

- [ ] Write README and focused docs using vendor-neutral role names first and current implementations only as historical examples.
- [ ] Add Mermaid diagrams for module replacement, KnowledgeOps flow, and tech-review vertical.
- [ ] Verify no document presents Notion, Basic Memory, ChatGPT, or Grok as mandatory.
- [ ] Run `python3 scripts/check_docs.py` and require a clean documentation-contract result.
- [ ] Commit as `docs: define replaceable KnowledgeOps architecture`.

### Task 2: Core JSON Schemas and synthetic corpus

**Files:**
- Create: `schemas/common.schema.json`
- Create: `schemas/signal.schema.json`
- Create: `schemas/source.schema.json`
- Create: `schemas/actor.schema.json`
- Create: `schemas/theme.schema.json`
- Create: `schemas/brief.schema.json`
- Create: `schemas/analysis.schema.json`
- Create: `examples/source.example.json`
- Create: `examples/actor.example.json`
- Create: `examples/theme.example.json`
- Create: `examples/signal.example.json`
- Create: `examples/brief.example.json`
- Create: `examples/analysis.example.json`
- Create: `tests/fixtures/invalid/signal-missing-source.json`
- Create: `tests/fixtures/invalid/signal-bad-state.json`

**Interfaces:**
- Consumes: entity definitions and epistemic/lifecycle contracts from Task 1.
- Produces: Draft 2020-12 schemas and a synthetic reference corpus.

- [ ] Define shared enums for epistemic states and currentness states.
- [ ] Require stable string IDs, provenance/source links where applicable, and explicit epistemic/currentness fields on state-bearing entities.
- [ ] Keep `FACT/INFERENCE/...` independent from `CANDIDATE/CURRENT/...`.
- [ ] Write one valid synthetic example per entity and two deliberately invalid signal fixtures.
- [ ] Run JSON parsing over every `.json` file and require success.
- [ ] Commit as `feat: add KnowledgeOps schemas and synthetic corpus`.

### Task 3: Deterministic validator with RED→GREEN tests

**Files:**
- Create: `requirements-dev.txt`
- Create: `scripts/validate.py`
- Create: `scripts/check_docs.py`
- Create: `tests/test_validation.py`

**Interfaces:**
- Consumes: `schemas/*.json`, `examples/*.json`, `tests/fixtures/invalid/*.json`.
- Produces: `python scripts/validate.py` exit code contract: `0` only when schemas and examples satisfy all checks.

- [ ] Write tests that load each valid example against its schema and assert success.
- [ ] Write tests asserting `signal-missing-source.json` and `signal-bad-state.json` fail validation.
- [ ] Run tests before validator implementation and observe RED due to missing validator functions.
- [ ] Implement schema loading, `$ref` resolution, example-to-schema mapping, and deterministic error formatting.
- [ ] Implement documentation checks for forbidden placeholders and required invariant phrases.
- [ ] Run `python -m unittest discover -v` and require all tests PASS.
- [ ] Run `python scripts/validate.py` and require a zero exit status.
- [ ] Commit as `test: add deterministic KnowledgeOps validation`.

### Task 4: GitHub informational CI/CD gate

**Files:**
- Create: `.github/workflows/validate.yml`

**Interfaces:**
- Consumes: local validation command from Task 3.
- Produces: GitHub check that runs exactly the same validator on pull requests and pushes to `main`.

- [ ] Configure Python 3.11 and install `requirements-dev.txt`.
- [ ] Run `python -m unittest discover -v`.
- [ ] Run `python scripts/validate.py`.
- [ ] Parse workflow YAML locally and verify commands match local verification.
- [ ] Commit as `ci: validate KnowledgeOps contracts`.

### Task 5: Final repository acceptance and public PR

**Files:**
- Modify only if verification reveals defects.

**Interfaces:**
- Consumes: all prior tasks.
- Produces: public PR with reproducible v0.1 evidence.

- [ ] Run `python -m unittest discover -v`.
- [ ] Run `python scripts/validate.py`.
- [ ] Run Python compile checks for `scripts/` and `tests/`.
- [ ] Run JSON parse check for all schemas/examples/fixtures.
- [ ] Run `git diff --check` and placeholder scan.
- [ ] Push `feat/knowledgeops-v0.1` to the public fork/repository.
- [ ] Open a PR to `main` describing the replaceable-module invariant and local verification receipt.
- [ ] Read back PR head SHA and GitHub Actions result before claiming completion.
