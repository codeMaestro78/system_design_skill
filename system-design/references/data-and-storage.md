# Data and storage

Use for persistence, data ownership, consistency, and lifecycle decisions. Sources: [PostgreSQL transactions and indexes](sources.md#data-cloud-container-and-operations-sources), [Amazon DynamoDB read consistency](sources.md#data-cloud-container-and-operations-sources), [Azure data patterns](sources.md#patterns), [NIST media sanitization](sources.md#security-and-privacy).

## Choose from access paths and invariants

List entities, owners, required queries, write rates, transaction boundaries, consistency needs, retention and deletion. A relational store suits relationships, constraints and multi-row transactions; a key/document store can suit access patterns and independent item operations. Neither category implies a universal scale or consistency level. Prototype critical queries and inspect indexes and query plans. An index speeds matching reads at storage and write cost. Search indexes, analytical stores, object stores and data lakes serve different query and lifecycle needs; treat them as derived or primary stores explicitly.

For booking, inventory, or another no-conflict invariant, a read-then-insert inside a transaction may still race. Use an appropriate database constraint, or serialize writes through a resource row/lock that every writer uses. Explain why that lock target exists before the check, or how its creation is made race-safe. A query that locks only matching appointments locks nothing for an empty interval. State the isolation and retry behavior; test simultaneous writes against the actual database.

## Distribution changes semantics

Replication improves read locality or availability but adds lag and failover behavior. Partitioning/sharding spreads load but complicates joins, unique constraints, hot keys, rebalancing and cross-partition transactions. Specify a partition key from observed access patterns and skew; design migration when it must change. State the actual consistency guarantee for each flow (for example, read after own write) and how the UI handles lag.

For multi-system writes, define the source of truth, commit boundary, duplicate/replay behavior and reconciliation path. Avoid assuming a transaction spans a database, queue and external API. See [distributed systems](distributed-systems.md) and [patterns](architecture-patterns.md) for outbox and saga choices.

## Lifecycle is part of design

Specify schema evolution, backward compatible rollout, backfill, retention, deletion propagation, backup frequency, restore objectives and restore tests. Encryption is useful but does not by itself establish deletion. Test recovery against the required data and time targets; a backup without a successful restore is unverified. For regulated data, verify current jurisdictional requirements before specifying a policy.
