# Capacity and scale

Use when sizing or bottleneck decisions matter. Sources: [Google SRE](sources.md#sre-reliability-operations), [AWS Well-Architected](sources.md#skills-format-and-architecture-foundations), [Little's Law](sources.md#distributed-systems-and-messaging).

## Small auditable estimate

Write each assumption with units and a range where useful. Example formulas, with **illustrative inputs only**:

- Average requests/s = requests/day ÷ 86,400. Peak requests/s = average × observed or assumed peak factor.
- Concurrent in-flight requests ≈ arrival rate (requests/s) × average time in system (s), when the system is stable. Queue growth = arrival rate − completion rate when positive.
- Storage/year ≈ records/day × bytes/record × 365, then add indexes, replicas, backups, retention and growth. Network bytes/s ≈ requests/s × payload bytes, accounting for fan-out.
- Cost drivers include compute duration, provisioned capacity, storage/replicas, requests, transfer, observability, and team operations. Verify current provider prices before giving a quote.

Show average and peak, read/write mix, payload distribution, concurrency, data retention, and headroom only if they affect a choice. A queue does not fix insufficient service capacity; it moves pressure into backlog and latency. If estimates are uncertain, show the break point at which a different design becomes justified.

## Locate bottlenecks

Trace the critical path and assign a latency budget. Measure p95/p99 as well as median, including downstream fan-out; tail latency can dominate composed requests. Check connection pools, locks, indexes, N+1 queries, hot keys, partitions, write amplification, rate limits, and third-party calls before adding replicas. Horizontal scaling works only when state, coordination and dependencies permit it; vertical scaling has finite headroom. CDN/edge caching helps suitable read paths but introduces invalidation, privacy and geographic consistency questions.

Test with representative traffic, data size, skew, bursts, and failure conditions. Define pass criteria from the requirements, monitor saturation, and verify autoscaling plus warm-up behavior. Avoid extrapolating a single benchmark to production without accounting for workload differences.
