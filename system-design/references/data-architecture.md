# Data architecture

Use this for: choosing stores, enforcing invariants, and owning the data lifecycle across a system. This file is the canonical guide for persistence, consistency, and data lifecycle decisions.

Sources: [PostgreSQL transaction isolation](sources.md#data-cloud-container-and-operations-sources), [PostgreSQL range constraints](sources.md#data-cloud-container-and-operations-sources), [PostgreSQL btree_gist](sources.md#data-cloud-container-and-operations-sources), [MySQL affected-rows semantics](sources.md#data-cloud-container-and-operations-sources), [Amazon DynamoDB read consistency](sources.md#data-cloud-container-and-operations-sources).

## Model access, ownership, and invariants first

List entities/events, identifiers, ownership, write paths, read/query patterns, relationships, cardinality, hot keys, data classification, retention, locality, and correctness invariants. Identify the authoritative source for each fact and who may mutate it. A database is a design choice, not the domain model.

Select relational, key/value, document, wide-column, graph, time-series, search, object, or analytical storage from workload, consistency, query, transaction, and operational needs. Polyglot persistence adds backup, access-control, schema, observability, and on-call burden. Use one datastore where it meets needs; add specialized stores only for a measured or clear workload requirement.

Classification drives encryption, retention, and access design, so fix the data classes before choosing stores; see [security and privacy](security-privacy.md) for the classification and tenancy rules that apply to those stores.

## Transactions and consistency

Specify invariants and the scope that must commit atomically. Select isolation/consistency based on anomalies the business can tolerate, not merely database feature names. Consider lost updates, write skew, stale reads, duplicate actions, read-your-writes, monotonic reads, and serializability. Define conflict detection and retry behavior. Some serialization/deadlock failures require rerunning the entire transaction and decision logic.

For a no-overlap booking or inventory limit, do not rely on a plain read-then-insert transaction. Name the enforcement mechanism: a database uniqueness/exclusion constraint where the data model supports it, serializable execution with whole-transaction retry, or locking a resource row that every writer follows. Explain why the lock row exists before checking, or how concurrent creation is safe. For example, a clinician row may already exist; a clinician/day row must be created uniquely before it can serve as a lock target. Locking only currently matching appointments cannot protect an empty interval. Verify concurrent requests against the chosen database and isolation level.

Enforcement details are engine-specific and must be checked against the target database. In PostgreSQL, an exclusion constraint that mixes an equality column with a range column needs the `btree_gist` extension for the equality column, so confirm the extension is installed (`CREATE EXTENSION btree_gist`) before depending on the constraint. On engines without exclusion constraints, enforce the invariant with a unique slot key plus a conditional write, and confirm that engine's affected-rows semantics: the returned count distinguishes an insert from an update, and the no-op case, before treating it as proof that the invariant held.

Across independent services, do not imply a distributed ACID transaction unless the actual platform and failure model provide one. Consider outbox/inbox, saga with compensations, reconciliation, or a single transactional boundary. State eventual-consistency delay, intermediate states, and user-visible behavior. Pattern-level choices are in the [pattern catalog](pattern-catalog.md); delivery semantics and failure behavior are in [distributed systems](distributed-systems.md).

## Replication, partitioning, and distribution

- Replication improves read capacity or some availability objectives; specify sync/async mode, lag, stale-read behavior, failover, split-brain protection, and possible acknowledged-data loss.
- Replicas are not backups. Plan separately for corruption, accidental deletion, ransomware, and operator error.
- Partitioning divides data by key/range/time within a storage system; sharding distributes ownership across partitions/nodes. Define key cardinality, query routing, hot partitions, rebalancing, cross-partition transactions, and migration.
- Multi-region design must define write ownership, conflict resolution, consistency, residency, routing, failover, recovery, and testing. Active-active is not a free reliability upgrade.

## Indexes, cache, and derived data

Design indexes from query plans and write costs; include selectivity, size, update frequency, and consistency. Caches and materialized views need source of truth, freshness SLA, invalidation/update method, stampede protection, negative caching policy, stale/missing fallback, rebuild/reconciliation, and tenant isolation. Measure locality and miss cost before adding a cache.

## Lifecycle, migrations, and recovery

Document schema evolution, backward/forward compatibility, data backfills, dual-read/write windows, validation, lock impact, rollback versus forward repair, and old/new application coexistence. Plan retention, legal hold where applicable, deletion across replicas, indexes, caches, analytics, exports, and backups (including expiry limits). Minimize copies and restrict access.

Define RPO/RTO and backup scope; encrypt and access-control backups; test point-in-time restore into an isolated environment; verify application-level consistency and restore the service, not just files. Record owner and drill interval. A green backup job is not proof of recoverability. Restore drills and disaster recovery are covered in [reliability, performance, and production operations](reliability-operations.md).

## Data governance and quality

Include lineage, provenance, freshness, schema, nullability, deduplication, quality checks, ownership, and remediation for data pipelines. Distinguish transactional/operational stores from analytical stores and define freshness/consistency contracts for derived feeds. Protect logs, telemetry, prompts, embeddings, and exports under the same classification rules as source records.
