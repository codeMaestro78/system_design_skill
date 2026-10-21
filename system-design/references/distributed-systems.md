# Distributed systems and messaging

## Assume partial failure

Remote calls can be delayed, lost, duplicated, reordered, or complete while the caller times out. Clocks drift, DNS/configuration change, certificates expire, and dependencies become overloaded. Specify connection/request deadlines, cancellation propagation, bounded in-flight work, connection pooling, failure detection, and what the user sees. A timeout bounds waiting; it does not cancel a remote side effect unless cancellation is explicitly supported.

## Retry and overload policy

Retry only transient failures and operations with safe replay semantics. Bound attempts and total elapsed time; use exponential backoff with jitter where appropriate; respect server hints. Assign one layer ownership of retries or coordinate budgets to avoid multiplicative retry storms. Use circuit breakers or bulkheads only for a demonstrated isolation need and define fallback semantics. Apply admission control, rate limits, load shedding, priority, and queue bounds to protect healthy work.

## Messaging and event flow

Choose queue, log/stream, pub/sub, or direct call based on ordering, replay, retention, fan-out, throughput, latency, and consumer independence. Define:

- producer ownership and event meaning; command vs fact; event time vs processing time
- schema evolution, compatibility, versioning, and unknown-field handling
- delivery model and duplicate handling; partition/ordering key and ordering scope
- consumer idempotency, checkpoint/ack timing, poison-message policy, retry schedule, DLQ, replay, and operator actions
- queue bounds, age/lag objectives, capacity, drain rate, backpressure, priority, expiry, and cancellation
- privacy, authorization, encryption, and retention for payloads and metadata

“Exactly once” is scoped to a specific broker/transaction boundary. Explain side effects outside it and how duplicates are made harmless. Use an outbox when database state and publication must not drift; design relay idempotency and cleanup. Use inbox/deduplication where the consumer must suppress duplicate effects. A saga coordinates multi-step business work with explicit compensation and terminal failure handling; compensation is not always a literal undo.

## Exactly-once is a scoped claim

State the scope before claiming delivery semantics. The most common architecture failure in this area is not a wrong algorithm, it is a guarantee stated one level wider than the system provides.

A broker's delivery guarantee holds **within the broker boundary**: the producer's write to the log, the log itself, and the consumer's read and acknowledgement of the log. Inside that boundary a broker can offer at-most-once, at-least-once, or exactly-once processing for a producer/consumer pair, and the pair can be made to act as one transactional unit.

End-to-end exactly-once across a database, a queue, and an external provider is **not** a property you can claim, for three independent reasons:

1. **Two systems, no shared transaction.** The write to the database and the publication to the queue are separate systems. Without a distributed transaction, which introduces its own availability and operational costs, there is a window in which one commits and the other does not. An outbox pattern moves the window to the relay, and the relay is another retryable, at-least-once component.
2. **The external effect is outside any transaction.** A payment, a shipped parcel, or an email sent through a third-party API happens in a system you do not control. A network failure between "provider accepted" and "you received the response" leaves the outcome unknown, and the retry is a possible duplicate charge or a duplicate shipment.
3. **The consumer crash window.** A consumer that applies a side effect and then crashes before committing its offset will re-read the message and apply the side effect again. The offset commit and the side effect are two different operations and are not atomic unless a specific mechanism makes them so.

What an honest design has instead:

| Claim | Requires | Cost |
|---|---|---|
| At-most-once | Acknowledge before processing, or drop on failure | Lost work; needs a separate repair path |
| At-least-once | Acknowledge only after the effect is durable | Duplicate effects unless the effect is idempotent |
| Effectively-once (the practical target) | A stable business key carried end to end, local deduplication at each effect site, and reconciliation against the source of truth | Storage for the deduplication records, a reconciliation job, and a stated lag before drift is repaired |
| Exactly-once (end to end) | A single transaction spanning every participant, including the external provider | Not available for external providers; a distributed transaction otherwise, with its own latency and failure behaviour |

The three mechanisms that make "effectively once" true are all required; two out of three is a duplicate waiting to happen:

- **Stable business key.** The key identifies the logical operation, not the message, and it is generated by whoever owns the business decision, not by the transport. It must survive retries, replays, re-queues, and a consumer redeploy.
- **Local deduplication.** The effect site records the key in the same transaction as the effect, or uses an equivalent atomic check such as an insert-if-absent constraint. A read-then-write check is not atomic, so two concurrent deliveries both pass it.
- **Reconciliation.** A job compares the source of truth with the effect sites and repairs drift, on a stated schedule, with a stated repair latency.

Even with all three, the claim to make is "effectively once, for effect E, with a deduplication window of W, and reconciliation repairing drift within T". The honest statement is a scope, never the bare words "exactly once".

Claims to refuse when they appear in a review: "the database and the queue are consistent", "the transaction rolls back the side effect", "the offset commit is atomic with the update", "the provider guarantees idempotency so we are safe". Each is false unless a named mechanism provides it, and each belongs in the risk register otherwise. See [API and contract design](api-design.md) for the idempotency-key mechanics and [reliability and operations](reliability-operations.md) for reconciliation and repair practice.

## Consistency and coordination

Explain which reads may be stale and for how long, how writes are ordered, and what happens during partition/failover. CAP describes trade-offs during a network partition for replicated data; it does not classify all systems as globally choosing only consistency or availability. Distinguish consensus, quorum, replication, and transaction guarantees. Do not introduce distributed locks or leader election without fencing, lease expiry, clock/partition analysis, and recovery semantics.

## Quorum arithmetic

Replication parameters are numbers, and the numbers decide whether a read can miss a committed write. State them explicitly rather than saying "quorum-based".

Let N be the number of replicas, W the number of replicas a write must acknowledge, and R the number of replicas a read must consult.

- **Write majority.** Two concurrent write quorums must overlap, otherwise both writes commit to disjoint replica sets and the replicas diverge permanently. That requires `2W > N`, that is `W >= floor(N/2) + 1`. For N=3, W=2. For N=5, W=3. A write that requires a majority cannot commit in a partition where the majority side is unavailable, which is the availability cost of the guarantee.
- **Read/write intersection.** A read that consults R replicas is guaranteed to see a committed write only if its read set overlaps the write's commit set. The overlap is at least `R + W - N`, so the guarantee requires `R + W > N`.
- **Failure tolerance.** Tolerated replica failures for writes is `N - W`, and for reads is `N - R`. These are the numbers that should appear in the availability requirement.

Worked example, N=3, W=2, R=2:

- `2W = 4 > 3`, so write quorums overlap. Two concurrent writes cannot both commit to disjoint sets; one is ordered after the other or one fails.
- `R + W = 4 > 3`, so the read set and the write set overlap in at least `2 + 2 - 3 = 1` replica. A read that consults two of three replicas must touch at least one replica that acknowledged the write, so it observes the committed value.
- A write acknowledges when the second of three replicas responds, so write latency is the second-fastest replica, and one replica may be down. A read has the same shape.
- With N=3, W=1, R=1: `R + W = 2 < 3`. A write commits on one replica and a read may hit either of the other two and return a stale value. The system is available and cheap, and the staleness window is bounded only by replication lag, which is a property of the network and not a guarantee.
- With N=3, W=2, R=1: `R + W = 3`, which is not `> 3`. The read set may miss the write set entirely, so a read served by the one lagging replica returns stale data even though writes are strictly ordered. Fast reads and strong writes are not simultaneously available; this is the classic trade, and it is a trade, not a free win.
- With N=5, W=3, R=3: `R + W = 6 > 5` and `2W = 6 > 5`. Tolerates two replica failures on both paths, at the cost of a third of the replicas acknowledging each operation.

**Read repair** closes the gap that failures open. A replica that was partitioned, or that missed a write for any other reason, holds a value that no longer matches the committed one. Read repair compares the values a read observed and writes the winner back to the stale replicas, so the divergence is repaired on the read path rather than waiting for a client to notice it. It needs:

- A version assigned at commit time, monotonically increasing per logical object, so "newest" is decidable. A wall-clock timestamp is not sufficient, because clocks drift and two writes can share a timestamp.
- A documented conflict rule: highest committed version wins, with a stated tiebreak for equal versions.
- A decision about uncommitted writes. A replica that rejoins holding a write that never reached W has a value that was never committed, and read repair overwrites it with the committed value. That is correct, and it is a behaviour the design states rather than an accident.
- A limit on what read repair may resurrect. If the committed value is a deletion, a stale replica must not be repaired back into existence.

Read repair only touches the replicas a read consulted. Divergence in replicas no read touches is repaired by **anti-entropy**, a background comparison and synchronization process. A design that has only one of the two has a repair gap; name which one exists.

The quorum parameters are also a latency and cost decision. Raising R improves read freshness and raises read latency and read cost. Raising W improves durability and raises write latency and write cost, and reduces the number of failures tolerated. Stating the numbers and their consequences is the deliverable; the name "quorum" is not.

## What consensus buys

Consensus is a specific mechanism with a specific bill, and it is frequently proposed when a simpler arrangement would do.

Consensus (the family of algorithms behind Raft and Paxos) provides a replicated log with a single total order of operations, tolerant of a minority of node failures: with N=3, one node may fail; with N=5, two. Through that log it provides a single writer at a time, an agreed value for every committed entry, and linearizability for the operations that go through it. What it does not provide is application-level semantics, transactionality across services, schema evolution, or a way around a slow or unreachable majority.

The three guarantees a reader must keep apart:

| Guarantee | What it says | What it costs |
|---|---|---|
| Linearizable | The system behaves as if there were a single copy, and every operation appears to take effect at some instant between its invocation and its response | Coordination on every operation; unavailable during a partition of the majority side |
| Sequentially consistent | All operations appear in one total order that respects each process's program order, but that order need not match real time | A read may return a value written before the read was issued, so real-time anomalies are possible |
| Eventually consistent | No ordering guarantee at all; replicas converge if updates stop, and a read may return arbitrarily stale data | Cheapest to run; the application must define staleness bounds and tolerate the difference |

The practical conclusion: **most systems should prefer a single writer plus a database over a distributed lock service.** A transactional database already gives one writer, atomicity, isolation, durability, and recovery for the data it owns. A distributed lock service adds a component, a new failure domain, a new availability dependency (the lock service becomes part of the critical path of every operation it guards), lease and clock and fencing concerns, and a new operational burden, and it does not remove the need for the database transaction underneath. It is paid for to protect mutual exclusion across writers, and a single-writer design removes the need for mutual exclusion instead of paying for it. Prefer a database constraint, an atomic conditional update, or a single-writer partition over a lock service for the same reason.

A lock or consensus service earns its place when the mutual exclusion must span systems that share no database and cannot be made single-writer, when the critical section is short and the coordination must survive failover, and when fencing tokens are available so a paused leader cannot write late. Those are narrow conditions, and a design that proposes a lock service should show why the simpler arrangement was rejected.

For the consistency models, the failure modes under partition, the clock and lease analysis, and the fencing-token mechanics, see [consistency, clocks, and coordination](consistency-and-clocks.md). For storage-engine behaviour and replication layout, see [data architecture](data-architecture.md).

## Object storage consistency

Object stores have their own consistency model, and it is not the database's model.

An S3-style object store offers strong read-after-write: a newly written object is immediately visible on reads, and in the current product behaviour overwrite and overwrite-then-delete pairs are strongly consistent as well, including in listings. That is a specific, product-specific guarantee that was added over time, so it must be cited to the current product documentation rather than assumed for object storage in general. Many other object stores, and many versioned blob stores, remain eventually consistent for overwrite and delete.

Design consequences that survive regardless of the product's current guarantee:

- Strong consistency at the object level is not transactional consistency across objects. A multi-object update, such as writing a manifest and its data files, still needs a coordination step, and the object store does not provide one.
- A database row that points at an object may be committed before the object is written, or the object may be written and the row rolled back. The pair needs an ordering rule and a repair path.
- Listing consistency differs from object consistency in some products and versions, and a design that discovers objects by listing depends on it.
- Versioning, retention, and legal hold on the object store are a separate durability and recovery story from the database's backups.

See [data architecture](data-architecture.md) for where blobs belong relative to the system of record, and for the replication and backup model.

## Common distributed mechanisms

- **Circuit breaker:** stop calls to a failing dependency to limit wasted capacity; define open/half-open/closed thresholds and visible degraded behavior.
- **Bulkhead:** isolate thread/connection/worker capacity by dependency or priority; size pools and expose rejection/saturation metrics.
- **Rate limit/throttle:** protect fairness and capacity; define key, burst, window, response, and trusted enforcement boundary.
- **Saga:** coordinate local transactions across owners; define durable state, idempotent steps, compensation, timeout, manual repair, and reconciliation.
- **Leader election/lease:** coordinate one active actor; use fencing tokens to prevent stale leaders from writing after a pause.
- **Change-data capture:** publish committed database changes; manage schema, ordering, retention, snapshots, duplicates, and lag.

## Failure exercises

For each important dependency, inspect slow response, refusal, partial response, stale data, partition, quota exhaustion, credential expiry, DNS/certificate error, and recovery. Test one failure at a time in a controlled environment, measure user impact, cap blast radius, and define abort. Chaos experiments complement deterministic tests, load tests, and restore drills; they do not replace them.
