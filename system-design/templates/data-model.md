<!-- Use when entities, keys, invariants, ownership, and lifecycle must be fixed before choosing a database or splitting a service. -->

# Data model: <bounded context or store>

Owner: <team or role that owns the data>
Date: YYYY-MM-DD
Status: Draft | Reviewed | Accepted
Scope: <entities covered, and what is explicitly out>

## 1. Entities

One row per entity. The key columns are the contract, not an implementation detail.

| Entity | Purpose | Primary key | Natural/alternate key | Foreign keys | Cardinality | Volume (rows/day) | Size (bytes/row) | Owner |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |
| | | | | | | | | |

Attribute detail for each entity, with types, units, and nullability:

| Entity | Attribute | Type | Null? | Unit/format | Default | Sensitive | Validation rule |
|---|---|---|---|---|---|---|---|
| | | | | | | | | |

State whether identifiers are assigned by the client or the server, and whether they are sortable in creation order. Sequence-based keys leak volume and complicate merges; random keys cost locality. Choose deliberately.

## 2. Constraints and invariants

### 2.1 Business invariants

| Invariant ID | Rule | Scope (one row, one tenant, all rows) | Enforcement mechanism | Where it is checked | Failure behaviour |
|---|---|---|---|---|---|
| INV-1 | | | | | |
| INV-2 | | | | | |

Name the mechanism, not the intent. Viable mechanisms: a unique or exclusion constraint, a foreign key, a check constraint, a serializable transaction with whole-transaction retry, or a row lock that every writer follows.

### 2.2 Concurrency invariant and the empty case

For each invariant that concurrent writers can violate, name the enforcement mechanism and answer the empty case explicitly.

> Enforcement mechanism: <constraint name, index, lock target, or isolation level>
> When the conflicting row does not yet exist: <how the mechanism behaves when there is no row to lock, see, or conflict against>

State why a read-then-write check is not sufficient: two concurrent transactions can both observe a free slot and both insert. If the invariant depends on a row that must exist before the check, state how that row is created uniquely and when it is created. Verify the chosen mechanism against the actual database and isolation level; a mechanism that only works in a different engine is not a design.

| Concurrency invariant | Enforcement mechanism | Empty-case behaviour | Verified by |
|---|---|---|---|
| | | | <concurrency test, and the database and isolation level used> |

## 3. Relationships and ownership

| From entity | To entity | Relationship | Cardinality | Delete behaviour | Owning context |
|---|---|---|---|---|---|
| | | 1:N, N:M, 1:1 | | Cascade/Restrict/Set null/Soft delete | |

Source of truth per fact:

| Fact | Authoritative store | Derived copies | Write authority | Readers that must not write |
|---|---|---|---|---|
| | | <caches, indexes, search, analytics> | | |

Shared-database writes across a service boundary are prohibited unless the reason is written here: <reason and the explicit coordination cost>

## 4. Access patterns

| Access pattern | Query shape | Frequency (reads/s) | Latency requirement | Index or mechanism | Notes |
|---|---|---|---|---|---|
| | | | | | |

State the index and its write cost, not just its existence. Note hot keys, unbounded scans, and paginated queries over non-indexed sorts.

Read paths that need different freshness than the write path: <path, freshness requirement, and how it is met>

## 5. Lifecycle

| Stage | Entry condition | State change | Owner | Reversible? | Retention at this stage |
|---|---|---|---|---|---|
| Created | | | | | |
| Active | | | | | |
| Suspended/pending | | | | | |
| Closed/archived | | | | | |
| Deleted | | | | | |

Soft delete versus hard delete, and which one the system reads from: <policy and where it is enforced>

## 6. Retention, deletion, and legal holds

| Data set | Retention period | Basis for the period | Deletion trigger | Deletion scope (live, replicas, indexes, caches, logs, backups, exports, analytics, embeddings) | Backups expiry limit | Legal hold behaviour | Owner |
|---|---|---|---|---|---|---|---|
| | | <policy, obligation, or user need> | | | | | | |

Deletion must reach every copy. Name the mechanism for each: <for example "tombstone row plus periodic sweep of the analytics bucket" and "backups expire after N days, so erasure completes by then, not before">

## 7. Schema evolution

| Change | Backward compatible? | Forward compatible? | Migration mechanism | Rollback | See |
|---|---|---|---|---|---|
| | | | Expand/contract | | [migration-plan.md](migration-plan.md) |

Rules for this store: <what a deploy may assume about the schema at read time and write time, and how mixed versions are handled>

## 8. Storage choice rationale

| Criterion | Requirement | Chosen store | Why it fits | Cost of the choice | Alternative rejected |
|---|---|---|---|---|---|
| Query and transaction needs | | | | | |
| Consistency needs | | | | | |
| Scale and growth | | | | | |
| Operational burden (backup, ACL, schema, on-call) | | | | | |
| Cost | | | | | |

State the extra burden that a second datastore adds: backups, access control, schema evolution, observability, on-call, and incident response.

## Before you deliver

- Every entity has a key, an owner, and a lifecycle.
- Every concurrency invariant names its enforcement mechanism, and the empty case is answered for each one.
- No invented numbers. Every volume, size, and retention figure carries units and a source, or is labelled Assumed with an owner.
- Every entity and every derived copy maps to a requirement, a constraint, or a named risk reduction, and unused fields are named.
- Deletion covers every copy including backups, and the unavoidable backup expiry limit is stated.
- Restore and rollback are drills with an owner and a date, not intentions.
