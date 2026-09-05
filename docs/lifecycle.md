# Lifecycle Contract

Lifecycle answers: **where is this knowledge item in review/currentness over time?**

Allowed states in v0.1:

```text
CANDIDATE -> REVIEWED -> VERIFIED -> CURRENT
                                  -> STALE
                                  -> INVALIDATED
                                  -> HISTORICAL
```

This axis is separate from epistemic status.

Examples:

- `FACT + HISTORICAL` — a verified past event.
- `HYPOTHESIS + CANDIDATE` — an unreviewed proposed explanation.
- `FACT + INVALIDATED` — the statement may accurately describe an earlier observed state while no longer being valid as current operational guidance.

History should normally be superseded or invalidated, not silently rewritten away.
