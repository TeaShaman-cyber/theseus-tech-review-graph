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
