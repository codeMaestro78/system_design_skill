# Pattern catalog: fit, costs, and misuse

Use this for: choosing a pattern only when a named failure or change pressure justifies it, and stating what that pattern costs. This file is the canonical pattern list for the reference set.

Sources: [Microsoft cloud design patterns](sources.md#patterns), [Microsoft transactional outbox](sources.md#patterns), [AWS saga pattern](sources.md#patterns), [AWS fault isolation](sources.md#patterns).

## How to use this catalog

Use this as a search map, not a checklist. For every candidate pattern answer: What requirement or failure does it address? What is the simplest alternative? What new state/failure/operations does it introduce? How will fit be measured? Patterns compose but also compound operational burden.

## Pattern table

| Pattern | Fits when | Costs, risks, and checks |
|---|---|---|
| Modular monolith | Shared transactions/team and one deployment are efficient | Enforce module boundaries; avoid shared mutable internals |
| API gateway / BFF | Central routing/policy or client-specific aggregation is needed | Extra hop, bottleneck, policy duplication; keep domain auth in owning service |
| Cache-aside | Measured repeated reads make source cost/latency too high | Staleness, invalidation, stampede, memory cost; a cache does not fix a slow write path and cache entries can leak across tenants; specify source of truth, tenant-scoped keys, and rebuild |
| Queue-based load leveling | Producers burst and async completion is acceptable | Bounded queue, age/drain SLO, ordering, idempotency, poison/DLQ, expiry; backlog can prolong outages |
| Competing consumers | Parallel workers can process independent messages | Ordering changes, duplicate handling, downstream capacity and fairness |
| Pub/sub | Independent consumers need fan-out | Delivery and schema evolution per consumer; replay/privacy/retention costs |
| Outbox / inbox | Commit state and publish or deduplicate effect across boundaries | Relay lag, cleanup, ordering, dedupe retention and replay behavior |
| Saga | Business process crosses independent transaction owners | Compensation can fail or be impossible; durable state, timeout, reconciliation, operator repair |
| CQRS | Read and write models have materially different requirements | Projection lag, duplicated logic/state, rebuild and consistency behavior; CQRS does not require event sourcing |
| Event sourcing | Audit/history and replay are core requirements | Schema evolution, snapshots, event privacy/deletion, query projections, operational learning curve |
| Circuit breaker | Failing dependency calls waste capacity or worsen recovery | Threshold/half-open tuning; not a substitute for timeouts, load shedding, or fallback design |
| Bulkhead | One dependency/tenant/priority must not consume all shared capacity | Pool fragmentation, rejections, sizing; monitor saturation and starvation |
| Rate limit / throttling | Protect shared capacity, fairness, abuse, or provider quota | Key scope, burst semantics, distributed state, customer messaging; not always a hard cost cap |
| Retry with backoff/jitter | Transient errors and replay-safe semantics | Can amplify overload and latency; set total deadline/budget and permanent-error classification |
| Strangler migration | Legacy behavior must be replaced incrementally | Routing/data ownership/coexistence/rollback complexity; define retirement signal |
| Cell-based isolation | Very large scale/blast-radius goals justify independent slices | Placement/routing, skew, cell evacuation, cross-cell features and operations; often excessive for small systems |
| Sharding | A measured single-store limit requires distribution | Key design, hot shards, transactions, rebalancing, migrations and operations |
| Multi-region active-active | Regional writes/availability targets require concurrent operation | Conflict resolution, global identity, data sovereignty, split-brain and testing complexity |

## Composition and removal

For every chosen pattern, state its trigger, ownership, steady-state path, failure path, metric, and removal or migration condition. Combine patterns carefully: retry plus circuit breaker can create two feedback loops; queue plus workers still depends on downstream capacity; outbox publication still needs consumer idempotency. Verify product-specific guarantees in current documentation before relying on them. Record the chosen pattern and its accepted cost as a decision record in [architecture method](architecture-method.md).

Pattern choice must stay consistent with the declared source of truth and consistency level in [data architecture](data-architecture.md), with the delivery guarantees assumed in [distributed systems](distributed-systems.md), and with tenant isolation rules in [security and privacy](security-privacy.md). Cache keys, queue payloads, and search indexes are all isolation boundaries, not just storage.

## Misuse checks

Do not adopt Kafka because "scale"; a managed queue or DB outbox may suffice. Do not cache before measuring. Do not shard before a demonstrated capacity need. Do not add microservices to make code modular. Do not use event sourcing merely to keep audit history. Do not call a service mesh a resilience strategy without understanding retries, timeouts, policy, and ownership. See [Microsoft cloud design patterns](sources.md#patterns), [Amazon Builders' Library](sources.md#sre-reliability-operations), and the [source guide](sources.md) for detailed context and provider caveats. [Meta TAO](sources.md#first-party-engineering-case-studies) is an optional read on why graph read paths are cached rather than queried live.
