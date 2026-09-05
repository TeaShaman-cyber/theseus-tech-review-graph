# Epistemic Contract

Epistemic status answers: **what kind of claim is this and how strong is its evidence?**

Allowed states in v0.1:

- `FACT` — supported by evidence appropriate for the claim.
- `INFERENCE` — derived from facts but not directly stated by the evidence.
- `HYPOTHESIS` — testable proposed explanation or predicted relation.
- `UNVERIFIED` — useful candidate information not yet through the required verification boundary.
- `DEGRADED` — obtained through a weaker-than-preferred route or with a known verification limitation.

A pipeline must never silently promote `UNVERIFIED` to `FACT` because wording appears plausible.

Epistemic status is independent of currentness. For example, an old release date can remain a `FACT` while the corresponding product state is `HISTORICAL`.
