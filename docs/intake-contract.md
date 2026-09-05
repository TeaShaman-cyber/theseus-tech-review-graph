# Intake / Corpus Contract

The intake layer accepts research output from replaceable producers and preserves enough context for later normalization.

Current implementation: Notion. This is not mandatory.

A conforming intake record should make available, when known:

- producer or origin;
- source URL or stable source identity;
- publication/retrieval time;
- collected text or bounded summary;
- originating review/task;
- collection provenance.

The intake layer is **not** the final knowledge authority. A claim copied into an intake page remains unverified until the KnowledgeOps pipeline explicitly classifies and reviews it.

Alternative implementations may include a database, filesystem corpus, message queue, object store, API, or future connector surface.
