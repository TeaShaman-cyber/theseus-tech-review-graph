# Tech Review Knowledge Adapter

The **Tech Review Knowledge Adapter** is the vendor-neutral role that converts research corpus material into normalized knowledge-state objects.

Current implementation: `memory-tech-brief`, derived from and adapted using Basic Memory's documented skills/workflows.

Its responsibility is not merely summarization:

```text
research corpus
  -> classify evidence
  -> extract bounded signals
  -> bind sources
  -> link actors/themes
  -> update temporal state
  -> derive Brief / Analysis projections
```

A `Brief` is a projection over the graph, not the graph authority itself.

The implementation may later move to another memory backend, a JSON state store, a relational model, or another agent framework without changing this role contract.

## Concrete bridge: Needle Watch receipt v0.2

The first real adapter slice is `scripts/adapt_needle_receipt.py`.

```text
Needle Watch receipt + candidate_id
  -> Source
  -> Signal
  -> Analysis
```

The adapter deliberately reuses existing v0.1 objects instead of introducing an `ExperimentCandidate` schema.

Epistemic rules for this bridge:

- `Source` preserves repository identity, upstream revision/fingerprint, discovery route, run identity, and source-health status from the receipt.
- `Signal` states only that Needle Watch observed the candidate and matched configured watch lines. With healthy source collection it remains `UNVERIFIED / CANDIDATE`; degraded source health maps to `DEGRADED / CANDIDATE`.
- `Analysis` is the experiment-follow-up projection and remains `HYPOTHESIS / CANDIDATE`.
- Receipt metadata alone never establishes repository behavior, efficacy, or experiment suitability.

The acceptance fixture is an immutable copy of Needle Watch run `33902305526-attempt-1`, sourced from `TeaShaman-cyber/theseus-needle-lab` commit `d492250763c4edfb123dc3e0e1b7ebd8abe9d4d5`, receipt blob `d90bb24b8bb2a6d7371206104456b6544c5da92d`. The selected first candidate is `yairpatch/flyweight@main`, matched on `parameter-storage` and `sparse-execution`.
