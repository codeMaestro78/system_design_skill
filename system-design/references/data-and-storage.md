# Data and storage

Use this for: a fast pass on persistence, data ownership, consistency, and lifecycle questions.

Sources: [PostgreSQL transactions and indexes](sources.md#data-cloud-container-and-operations-sources), [Amazon DynamoDB read consistency](sources.md#data-cloud-container-and-operations-sources), [Azure data patterns](sources.md#patterns), [NIST media sanitization](sources.md#security-and-privacy).

**Canonical guide:** [Data architecture](data-architecture.md). That file is the source of truth for storage choice, invariants, and lifecycle; this page is only a first pass.

## Decision rules

- Name the authoritative source for every fact and its owner before choosing a store. A cache, replica, search index, or warehouse is derived data until proven otherwise.
- Cache-aside gives stale reads, not strong consistency. It does not fix a slow write path, and cache entries can leak across tenants unless keys are tenant-scoped. Never promote a cache to source of truth without an invariant-preserving design.
- Replicas are not backups. Plan separately for corruption, accidental deletion, ransomware, and operator error, with tested restores.
- A read-then-insert inside a transaction still races for a no-conflict invariant. Use a database constraint, serializable execution with whole-transaction retry, or a resource row that every writer locks. A lock row must exist before it is used, and locking only matching rows protects nothing when the interval is empty.
- State the actual consistency guarantee per flow (for example, read-your-own-write), the lag, and how the UI behaves during it. Replication and partitioning change semantics, not just scale.
- A transaction does not span a database, a queue, and an external API. Define source of truth, commit boundary, duplicate handling, and reconciliation.
- Specify schema evolution, backfill, retention, deletion propagation, backup scope, and restore objectives. A backup that has not been restored is unverified. Encryption does not establish deletion.

## Where to go next

- Storage choice, invariants, indexes, and lifecycle detail: [data architecture](data-architecture.md).
- Outbox, saga, and cache patterns: [pattern catalog](pattern-catalog.md).
- Delivery semantics and failure behavior: [distributed systems](distributed-systems.md).
- Restore drills, RPO/RTO, and incident handling: [reliability and operations](reliability-operations.md).
