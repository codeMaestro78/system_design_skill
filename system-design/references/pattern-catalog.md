# Pattern catalog: fit, costs, and misuse

Use this as a search map, not a checklist. For every candidate pattern answer: What requirement or failure does it address? What is the simplest alternative? What new state/failure/operations does it introduce? How will fit be measured? Patterns compose but also compound operational burden.

| Pattern | Fits when | Costs, risks, and checks |
|---|---|---|
| Modular monolith | Shared transactions/team and one deployment are efficient | Enforce module boundaries; avoid shared mutable internals |
| API gateway / BFF | Central routing/policy or client-specific aggregation is needed | Extra hop, bottleneck, policy duplication; keep domain auth in owning service |
| Cache-aside | Measured repeated reads make source cost/latency too high | Staleness, invalidation, stampede, tenant leakage, memory cost; specify source of truth and rebuild |
| Queue-based load leveling | Producers burst and async completion is acceptable | Bounded queue, age/drain SLO, ordering, idempotency, poison/DLQ, expiry; backlog can prolong outages |
| Competing consumers | Parallel workers can process independent messages | Ordering changes, duplicate handling, downstream capacity and fairness |
| Pub/sub | Independent consumers need fan-out | Delivery and schema evolution per consumer; replay/privacy/retention costs |
| Outbox / inbox | Commit state and publish or deduplicate effect across boundaries | Relay lag, cleanup, ordering, dedupe retention and replay behavior |
| Saga | Business process crosses independent transaction owners | Compensation can fail or be impossible; durable state, timeout, reconciliation, operator repair |
| CQRS | Read and write models have materially different requirements | Projection lag, duplicated logic/state, rebuild and consistency behavior |
| Event sourcing | Audit/history and replay are core requirements | Schema evolution, snapshots, event privacy/deletion, query projections, operational learning curve |
| Circuit breaker | Failing dependency calls waste capacity or worsen recovery | Threshold/half-open tuning; not a substitute for timeouts, load shedding, or fallback design |
| Bulkhead | One dependency/tenant/priority must not consume all shared capacity | Pool fragmentation, rejections, sizing; monitor saturation and starvation |
| Rate limit / throttling | Protect shared capacity, fairness, abuse, or provider quota | Key scope, burst semantics, distributed state, customer messaging; not always a hard cost cap |
| Retry with backoff/jitter | Transient errors and replay-safe semantics | Can amplify overload and latency; set total deadline/budget and permanent-error classification |
| Strangler migration | Legacy behavior must be replaced incrementally | Routing/data ownership/coexistence/rollback complexity; define retirement signal |
| Cell-based isolation | Very large scale/blast-radius goals justify independent slices | Placement/routing, skew, cell evacuation, cross-cell features and operations; often excessive for small systems |
| Sharding | A measured single-store limit requires distribution | Key design, hot shards, transactions, rebalancing, migrations and operations |
| Multi-region active-active | Regional writes/availability targets require concurrent operation | Conflict resolution, global identity, data sovereignty, split-brain and testing complexity |
| CQRS/event streams | Independent read models/fan-out/replay are valuable | Event contracts, lag, replay, storage, operations; not a default replacement for direct DB transactions |

Misuse checks: Do not adopt Kafka because “scale”; a managed queue or DB outbox may suffice. Do not cache before measuring. Do not shard before a demonstrated capacity need. Do not add microservices to make code modular. Do not use event sourcing merely to keep audit history. Do not call a service mesh a resilience strategy without understanding retries, timeouts, policy, and ownership. See Microsoft cloud pattern catalog, AWS Builders' Library, and source list for detailed context and provider caveats.
