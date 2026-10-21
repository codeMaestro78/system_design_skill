# Architecture patterns

Use this for: matching a named failure or change pressure to a pattern before adopting it.

Sources: [Azure patterns](sources.md#patterns), [AWS saga and fault isolation](sources.md#patterns).

**Canonical guide:** [Pattern catalog](pattern-catalog.md). That file is the source of truth for pattern fit, cost, and misuse; this page is only a first pass.

## Decision rules

- Adopt a pattern only for a stated pressure, and state the simpler alternative you rejected. Every pattern adds state, failure modes, and operational work.
- For every chosen pattern, state its trigger, ownership, steady-state path, failure path, metric, and removal or migration condition.
- Traffic and fan-out: API gateway or BFF for shared entry policy; competing consumers for independent parallel work; pub/sub for independent fan-out.
- Load bursts: queue-based load leveling and dead-letter handling for async work; rate limiting and bulkheads to protect shared capacity. Queueing increases tolerance to bursts only while queue size, queue age, and processing recovery stay bounded.
- Read cost: cache-aside only after measurement, with an explicit source of truth and invalidation path. A cache does not fix a slow write path, and cache entries can leak across tenants.
- Write and read shape divergence: CQRS with a materialized view. CQRS does not require event sourcing; event sourcing is for history and replay as first-class requirements.
- Cross-owner workflows: transactional outbox for publish-after-commit, saga with compensation for multi-owner business processes. Compensation is not rollback.
- Migration and scale: strangler migration for legacy replacement, sharding only on a measured limit, cell-based isolation only for a real blast-radius need, multi-region active-active only when regional write or availability targets demand it.
- Combining patterns multiplies risk: retry plus circuit breaker can form two feedback loops, and outbox publication still needs consumer idempotency.

## Where to go next

- Full table with fit, cost, and misuse checks: [pattern catalog](pattern-catalog.md).
- Pattern choices recorded as decisions: [architecture method](architecture-method.md).
- Source of truth and consistency behind these patterns: [data architecture](data-architecture.md).
