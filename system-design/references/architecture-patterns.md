# Architecture patterns

Choose patterns by the failure or change pressure they solve. Each adds state, operations or semantics. Sources: [Azure patterns](sources.md#patterns), [AWS saga and fault isolation](sources.md#patterns). Guidance below is a recommendation unless a cited source explicitly defines a pattern.

| Pattern | Fit | Cost and common misuse |
| --- | --- | --- |
| API gateway / backend for frontend | Shared entry controls; client-specific composition | Gateway becomes bottleneck or business monolith; avoid needless layers. |
| Service discovery | Dynamic independently deployed instances | Registry/control-plane failure; static endpoints suffice for small deployments. |
| Strangler migration | Replace a legacy system by slices | Dual routing and data ownership may persist; plan cutover/rollback. |
| Cache-aside / read-through | Hot reads with acceptable staleness | Miss storms, invalidation, origin overload; cache does not fix a slow write path. |
| Write-through / write-behind | Synchronized reads / buffered writes | Write-through adds latency; write-behind risks delayed loss and ordering. |
| Queue load leveling / competing consumers | Bursty async work within downstream capacity | Backlog, poison jobs, lost ordering; a queue does not add throughput. |
| Dead-letter queue | Isolate work that exceeded a defined retry policy | Silent graveyard unless monitored, triaged and replayed safely. |
| CQRS / materialized view | Read and write shapes differ materially | Projection lag and duplicate models; unnecessary for basic CRUD. CQRS does not require event sourcing. |
| Event sourcing | Domain history and reconstruction are first-class needs | Replay, event evolution, privacy deletion, projection complexity; do not adopt for incidental audit logs. |
| Change-data capture | Publish committed DB changes or migrate data | Connector lag, schema drift, replay/ordering; business intent may be missing from raw row changes. |
| Transactional outbox / idempotent inbox | DB and broker cannot share one commit | Relay lag, duplicate delivery, ordering and deduplication state. |
| Saga / compensation | Cross-owner business workflow with partial progress | Compensation may fail and is not rollback; weak isolation and complex reconciliation. |
| Circuit breaker / bulkhead | Remote failure or shared resource saturation | False opens, capacity fragmentation; shared downstream state can defeat isolation. |
| Retry / throttle / rate limit | Transient errors / overload or abuse | Retry storms and unfairness; require budgets, idempotency, and feedback. |
| Cell-based architecture | Strong blast-radius limits at very large scale | Routing, duplicated capacity, cross-cell operations; avoid when a simpler partition suffices. |

For every chosen pattern, state its trigger, ownership, steady-state path, failure path, metric, and removal or migration condition. Combine patterns carefully: retry plus circuit breaker can create two feedback loops; queue plus workers still depends on downstream capacity; outbox publication still needs consumer idempotency. Verify product-specific guarantees in current documentation before relying on them.
