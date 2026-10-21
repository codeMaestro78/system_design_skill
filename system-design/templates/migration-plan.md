<!-- Use when a schema, contract, ownership, or storage change must land on a live system where old and new code coexist. -->

# Migration plan: <from> to <to>

Date: YYYY-MM-DD
Author: <role or name>
Owner: <role accountable for the migration>
Status: Draft | Approved | In progress | Complete
Window: <scheduled date and time, and the decision deadline>
Reversibility: <rollback possible until <event>, after which forward repair is the only path>

## 1. What is changing

| Item | From | To | Why | Reversible after cutover? |
|---|---|---|---|---|
| <schema, contract, service boundary, storage> | | | | |

## 2. Phases

| Phase | Name | Changes | Mixed-version support | Exit criteria | Owner | Window |
|---|---|---|---|---|---|---|
| 0 | Expand | <additive changes only, no behaviour change> | | | | |
| 1 | Migrate / backfill | | | | | |
| 2 | Switch reads | | | | | |
| 3 | Switch writes | | | | | |
| 4 | Contract | <remove old paths once evidence supports it> | | | | |

Expand/contract: additive changes land first and are safe with both old and new code running. Destructive changes land only after the old path is unused, measured, and retired.

## 3. Mixed-version deployment

| Aspect | Rule |
|---|---|
| Code versions in production | <which versions coexist, and for how long> |
| Schema compatibility | <what old code may assume, and what new code may assume> |
| Forward and backward compatibility | <can new code read old data, can old code read new data, and for how long> |
| Serialization format | <how a record is read by both versions, and the field naming or default rules> |
| Deployment order | <which component deploys first and why> |
| Version skew detection | <the metric or log that reveals skew, and where it is watched> |
| Exit | <the condition that lets the old version be removed> |

Old code must never read a value it cannot parse. New code must tolerate the oldest supported record.

## 4. Source of truth during migration

| Data set | Source of truth before | Source of truth during | Source of truth after |
|---|---|---|---|
| | | | |

Write authority during the window: <single writer per fact, or dual write with a stated reconciliation rule>
Reads during the window: <which path is authoritative for each read, and what happens if they disagree>

Dual write is two writes that can diverge. If both paths are written, state how divergence is detected and repaired.

## 5. Backfill

| Property | Rule |
|---|---|
| Scope | <which records, and the selection predicate> |
| Batch size | <rows per batch> |
| Idempotency | <re-running the backfill does not corrupt or duplicate; name the mechanism, for example "upsert by primary key" or "write only rows where the target column is null"> |
| Checkpointing | <where progress is stored, and the resume point> |
| Ordering | <primary key order for locality, or an order that avoids contention> |
| Rate limit | <rows/s, or batch interval, and the limit that protects production> |
| Throttle and backoff | <behaviour on contention, lock wait, or replica lag> |
| Load impact | <write amplification, index maintenance, log volume, replica lag> |
| Lock impact | <which locks the backfill takes, their duration, and the worst-case wait> |
| Interruption behaviour | <what happens if the job is killed mid-batch, and how partial batches are detected> |
| Concurrent writes | <how a row changed during the backfill is detected, for example a version column or updated_at comparison> |
| Verification | <row counts, checksums, sampled comparisons, and the reconciliation report> |

Backfills run against production volume, not a copy. Rehearse on production-like volume before the real run.

## 6. Validation and reconciliation

| Check | Scope | Method | Threshold | Frequency | Owner |
|---|---|---|---|---|---|
| Count | | <count comparison> | | | |
| Checksum | | <hash or aggregate comparison> | | | |
| Field-level sample | | <random and targeted sample> | | | |
| Referential integrity | | <orphan and dangling reference scan> | | | |
| Business invariant | | <for example, no overlapping intervals> | | | |
| Freshness | | <age of the new path relative to the old> | | | |

Reconciliation runs continuously during the dual window, not only at the end. A reconciliation report that shows differences but no owner is not a check.

## 7. Dual read/write window

| Path | Start | End | Condition to end it | Owner |
|---|---|---|---|---|
| Dual write | | | <no divergence beyond threshold for N days> | |
| Dual read, compare, prefer new | | | | |
| Read from old only | | | | |

## 8. Cutover

Cutover signal: <the measured condition that permits the switch, for example "dual write divergence below 0.01% for 7 consecutive days, backfill complete, and p99 latency of the new path within 10% of the old">

| Item | Value |
|---|---|
| Decision maker | <role> |
| Decision deadline | <date and time> |
| Preconditions checked | <list> |
| Expected duration | |
| Blast radius if wrong | <users, tenants, or records affected> |
| Communication plan | <who is told, when> |

## 9. Rollback versus forward repair

| Situation | Rollback or forward repair | Mechanism | Data implications | Time to safe state |
|---|---|---|---|---|
| Failure before any new writes | Rollback | <revert code and feature flag> | None | |
| Failure after new writes started | | | | |
| Failure after old path is removed | Forward repair only | | | |

State the point of no return explicitly: <the event after which rollback is no longer safe, for example "the first write to the new column that the old code cannot read">.

Never assume rollback is safe after irreversible writes. A dual-write schema is not a rollback plan if the old code cannot read the new data.

## 10. Cleanup and retirement

| Item | Action | Condition | Owner | Due |
|---|---|---|---|---|
| Old column or table | Drop | <no reads and no writes for N days, and the backfill is verified> | | |
| Old code path | Delete | <traffic at zero for N days, measured> | | |
| Compatibility shim | Remove | <all clients migrated> | | |
| Feature flag | Remove | <flag at 100% for N days> | | |
| Dual write | Remove | <cutover complete and stable> | | |
| Old credentials, topics, buckets | Revoke or delete | | | |

Permanent dual systems and compatibility paths without retirement criteria are the failure mode this section prevents. Every row needs a condition and a due date.

## 11. Load, lock, and cost impact

| Resource | During backfill | During dual write | After cutover | Headroom |
|---|---|---|---|---|
| Primary write IOPS | | | | |
| Index maintenance | | | | |
| Replica lag | | | | |
| Storage growth (temporary) | | | | |
| Log and telemetry volume | | | | |
| Lock wait time | | | | |
| Cost delta | | | | |

Abort conditions: <the metrics and thresholds that stop the backfill or the cutover, and who can pull that trigger>

## 12. Rollout stages

| Stage | Traffic or scope | Duration | Health criteria | Stop condition | Rollback action |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |

## Before you deliver

- Every phase has an exit criterion, an owner, and a window.
- No invented numbers. Every rate, volume, size, duration, and threshold carries units and a source, or is labelled a proposed value with an owner.
- The backfill is idempotent, checkpointed, rate limited, and safe to interrupt and resume.
- The point of no return is named, and forward repair is planned for the states where rollback is unsafe.
- Every cleanup item has a condition, an owner, and a due date. No permanent dual path.
- The load and lock impact of the migration is estimated against production, not a copy, and abort conditions are defined.
- Every component touched by the migration maps to a requirement, a constraint, or a named risk reduction.
- Restore and rollback are drills with an owner and a date, not intentions.
