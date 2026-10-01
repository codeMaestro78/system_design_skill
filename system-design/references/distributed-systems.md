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

## Consistency and coordination

Explain which reads may be stale and for how long, how writes are ordered, and what happens during partition/failover. CAP describes trade-offs during a network partition for replicated data; it does not classify all systems as globally choosing only consistency or availability. Distinguish consensus, quorum, replication, and transaction guarantees. Do not introduce distributed locks or leader election without fencing, lease expiry, clock/partition analysis, and recovery semantics.

## Common distributed mechanisms

- **Circuit breaker:** stop calls to a failing dependency to limit wasted capacity; define open/half-open/closed thresholds and visible degraded behavior.
- **Bulkhead:** isolate thread/connection/worker capacity by dependency or priority; size pools and expose rejection/saturation metrics.
- **Rate limit/throttle:** protect fairness and capacity; define key, burst, window, response, and trusted enforcement boundary.
- **Saga:** coordinate local transactions across owners; define durable state, idempotent steps, compensation, timeout, manual repair, and reconciliation.
- **Leader election/lease:** coordinate one active actor; use fencing tokens to prevent stale leaders from writing after a pause.
- **Change-data capture:** publish committed database changes; manage schema, ordering, retention, snapshots, duplicates, and lag.

## Failure exercises

For each important dependency, inspect slow response, refusal, partial response, stale data, partition, quota exhaustion, credential expiry, DNS/certificate error, and recovery. Test one failure at a time in a controlled environment, measure user impact, cap blast radius, and define abort. Chaos experiments complement deterministic tests, load tests, and restore drills; they do not replace them.
