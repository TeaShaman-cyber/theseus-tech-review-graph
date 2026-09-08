# KnowledgeOps

KnowledgeOps treats changing knowledge as maintained state rather than a pile of documents.

```mermaid
flowchart TD
    E[External evidence] --> I[Ingest]
    I --> P[Provenance + normalization]
    P --> S[Schema / contract checks]
    S --> R[Review / contradiction handling]
    R --> L[Lifecycle transition]
    L --> K[Durable knowledge state]
    K --> D[Drift / invalidation / reflection]
    D --> K
```

Historical stage names used in the current Basic Memory adaptation are:

```text
memory-ingest -> memory-schema -> memory-tasks -> memory-lifecycle -> memory-reflect
```

The names preserve origin; the stage contracts are vendor-neutral.

## Informational CI/CD analogy

| Software CI/CD | KnowledgeOps |
|---|---|
| source commit | new evidence |
| git history | provenance |
| parser/build | ingest |
| schema/type tests | structural knowledge checks |
| integration tests | relation/evidence checks |
| review | epistemic review |
| release candidate | reviewed knowledge |
| deployment | current knowledge |
| monitoring | drift detection |
| rollback | invalidation/supersession |
| release notes | brief/reflection |

Schema validity proves shape, not truth. A validator may prove that a `Signal` has a source and legal states; it cannot prove the underlying claim is factually correct.

## Verified knowledge mutation

For non-trivial multi-tool changes, KnowledgeOps may insert an experimental
orchestration step before durable state is accepted:

```text
candidate
  -> relation map
  -> minimal reconcile decision
  -> authorized write
  -> independent read-back
  -> accepted mutation
```

This makes relation/evidence checks operational rather than merely descriptive.
A semantic mapper can recommend whether to update, link, create, or defer, while
the persistence and verification layers remain independently accountable.

A write transport reporting success is not sufficient evidence that the intended
knowledge state exists remotely. See
[Knowledge Orchestration Plane](knowledge-orchestration-plane.md) for the
experimental receipt and bounded-repair contract.
