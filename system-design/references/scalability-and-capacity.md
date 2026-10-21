# Capacity and scale

Use this for: a quick sizing or bottleneck decision when the numbers, not the topology, drive the choice.

Sources: [Google SRE](sources.md#sre-reliability-operations), [AWS Well-Architected](sources.md#architecture-foundations), [Little's Law](sources.md#distributed-systems-and-messaging).

**Canonical guide:** [Requirements and workload modeling](requirements-and-capacity.md). That file is the source of truth for estimation method, latency budgets, and capacity analysis; this page is only a first pass.

## Decision rules

- Show every assumption with units and a range. Average requests/s = requests/day ÷ 86,400; peak = average × a stated peak factor. Never invent load figures.
- Concurrent in-flight work ≈ arrival rate × mean time in system (Little's Law). It is an average, not a safe upper bound; add tail latency and burstiness.
- Storage ≈ writes/day × bytes/record × retention, plus indexes, replicas, backups, and derived copies. Network bytes/s ≈ requests/s × payload bytes × fan-out.
- Assign a latency budget to the critical path and measure p95/p99, not the median. Check pools, locks, indexes, N+1 queries, hot keys, and write amplification before adding replicas.
- Horizontal scaling works only when state, coordination, and dependencies permit it. Vertical headroom is finite. Autoscaling has reaction delay, warm-up, and quota limits.
- A queue does not fix insufficient service capacity; it moves pressure into backlog and latency. Watch queue age and estimate drain time, not just depth.
- Estimate cost drivers (compute duration, provisioned capacity, storage, requests, transfer, observability, on-call) and verify current provider prices before quoting.
- If the estimate is uncertain, report the break point at which a different design becomes justified.

## Where to go next

- Full estimation method, latency budgets, and load testing: [requirements and capacity](requirements-and-capacity.md).
- Patterns that shift load (queues, caches, bulkheads): [pattern catalog](pattern-catalog.md).
- Operating capacity and cost in production: [reliability and operations](reliability-operations.md).
