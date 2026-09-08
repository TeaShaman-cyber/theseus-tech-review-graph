# Knowledge Orchestration Plane

This document is an **experimental architecture contract** for research issue
[#5](https://github.com/TeaShaman-cyber/theseus-tech-review-graph/issues/5).
It does not promote the orchestration plane into the accepted v0.1 entity
schemas or make any current provider mandatory.

## Purpose

The existing KnowledgeOps lifecycle explains how evidence becomes maintained
knowledge. The orchestration plane addresses a narrower operational question:
how should candidate knowledge be coordinated across specialized tools before
an authorized durable mutation is accepted?

```text
candidate knowledge
  -> explicit orchestration
  -> relation mapping
  -> reconcile minimal mutation
  -> governed write
  -> independent postcondition verification
  -> accepted durable state
```

The core invariant is:

> writer self-report does not prove persistence.

A mutation is complete only when the required observable postcondition has been
verified through a valid read route appropriate to the authority domain.

## Roles

### Orchestrator

Builds the smallest execution graph needed for the task. It keeps dependencies,
read/write access classes, evidence gates, and repair bounds explicit.

### Relation mapper

Compares candidate knowledge with existing state and proposes semantic
relationships. The relation mapper is advisory, not authority. A graph or model
output may support a reconciliation decision but cannot grant write permission
or promote a claim.

### Reconciler

Chooses the smallest supported state transition:

```text
UPDATE_EXISTING
LINK_EXISTING
CREATE_NEW
REJECT_OR_DEFER
```

This is semantic deduplication before persistence: a new signal should not
automatically become a new durable node.

### Governed writer

Performs only the authorized mutation in the authoritative persistence domain.
Capability and transport access do not imply permission.

### Independent verifier

Reads the resulting state independently when practical and compares it with the
declared postcondition. A verifier may be a deterministic repository read,
remote API read-back, or a specialized formal verifier such as the research
line in issue #2.

### Bounded repair

A concrete failed verification gate may authorize one targeted repair attempt
inside the already-authorized scope. There is no open-ended mutation loop.
After the repair, the postcondition is verified again.

## Provider-neutral operational example

The 2026-09-08 Needle enrichment run used current providers in these roles:

| Role | Operational provider |
|---|---|
| Orchestrator | Graph Mode |
| Relation mapper | Ace Knowledge Graph |
| Durable coordination state | GitHub Issues |
| Writer | governed MarcoPolo route, then an authorized native GitHub fallback after transport corruption |
| Independent verifier | MarcoPolo GitHub read-back |

These are provenance facts, not permanent dependencies.

The run provided one useful failure canary: the first write created the intended
issue but corrupted part of its body. Independent read-back detected the failed
postcondition, one bounded repair corrected it, and a second read-back verified
the remote state.

## Experimental mutation receipt

The repository therefore carries an experimental, non-core receipt pair:

- `experimental/knowledge-mutation-receipt.schema.json`
- `experimental/knowledge-mutation-receipt.example.json`

The receipt records the reconciliation decision, target, write route/status,
verification route/status, and bounded repair count. A relation-map digest is
recorded only when canonical bytes are actually available. The reference
receipt deliberately records that digest as `UNKNOWN` rather than reconstructing
evidence after the fact.

The experimental schema is intentionally outside `schemas/` and `examples/`.
It is not part of the accepted v0.1 KnowledgeOps entity model.

## Root Theseus relationship

Program-level navigation is tracked in
[`theseus-research#28`](https://github.com/TeaShaman-cyber/theseus-research/issues/28).
The root registry already declares `theseus-tech-review-graph` as a Theseus
research line. Cross-repository issue relationships remain coordination edges,
not proof edges:

```text
registry membership
        !=
cross-repository coordination edge
        !=
scientific proof / acceptance
```

No orchestration component gains authority over another Theseus laboratory
merely because it can map or verify a relationship.

## Simple-path rule

The orchestration plane is not mandatory ceremony. A trivial one-step edit with
a direct authoritative write and deterministic read-back should remain simple.
Use orchestration only when dependencies, relation reconciliation, multiple
tools, authority boundaries, or repair/verification value justify it.
