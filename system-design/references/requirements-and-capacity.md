# Requirements and workload modeling

Use this for: eliciting testable requirements, sizing a workload, and finding the binding capacity constraint before a design decision is made.

Sources: [Google SRE](sources.md#sre-reliability-operations), [Little's Law](sources.md#distributed-systems-and-messaging), [AWS Well-Architected](sources.md#architecture-foundations).

## Make requirements testable

Record each requirement with its user/business importance, scope, operating condition, metric, target or unresolved status, owner, and verification method. Distinguish a product requirement, internal SLO, contractual SLA, regulatory obligation, and a provisional assumption. Define quality at the critical user journey, not only at an individual component. Turn each quality attribute into a scenario in the format defined in [architecture method](architecture-method.md).

Ask for normal, peak, burst, seasonal, and failure workloads. Include traffic mix, tenant skew, request size, read/write/compute mix, fan-out, background work, data retention, locality, and growth horizon. Never invent load figures. If the user lacks them, create explicit scenarios (low/base/high) and label values illustrative.

## Back-of-the-envelope model

Use rounded estimates with visible assumptions. Keep units consistent and clarify whether decimal or binary storage units matter.

- Average RPS = requests in interval / seconds in interval. Peak RPS = average × stated peak factor, if justified.
- Concurrent work ≈ arrival rate × mean duration (Little's Law); this is an average, not a safe upper bound. Account for tail latency and burstiness.
- Storage = writes/day × average stored bytes × retention days × replica/overhead factor. Separate raw, indexed, log, backup, and derived copies.
- Network throughput = requests/sec × mean payload bytes × fan-out, plus protocol and response overhead.
- Queue backlog grows when arrival rate exceeds service rate. Estimate drain time from backlog / spare processing rate; account for new arrivals and retries.
- Cache working set and hit rate require actual locality and invalidation behavior. Do not infer them from total dataset size alone.
- Cost model includes request/compute, storage, I/O/egress, observability, replication, backups, licenses, support, and on-call engineering effort. Price only current provider facts from current official calculators/docs.

For every estimate, show formula, input source/assumption, range if uncertain, likely bottleneck, and decision sensitivity. Avoid false precision. A spreadsheet or small script can help when many variables interact; keep formulas reviewable.

## Latency and performance budgets

Define user-perceived latency percentiles and scope (client-to-edge, service boundary, or full transaction). Allocate the end-to-end budget across DNS/TLS/network, gateway, services, queues, database/cache, and external providers. Parallel calls use max-of-branches latency; sequential dependencies add. Account for tail behavior and retries. Define deadlines and propagate remaining time; do not let downstream work outlive the request without an explicit asynchronous contract.

## Capacity and bottleneck analysis

Map each critical path to throughput/capacity limits, resource saturation, concurrency limits, quotas, and failure-domain headroom. Examine CPU, memory, disk/IOPS, connections, locks, network, hot keys/partitions, queue age, provider quotas, and human/operator capacity. Model skew and noisy neighbors. Include degraded capacity after losing an instance, zone, region, dependency, or replica.

Use measurement and representative benchmarks before scaling decisions. Load tests need realistic data shape, cache state, concurrency, traffic distribution, dependencies, and success criteria. Test beyond expected peak to discover the knee/overload behavior; define abort conditions and avoid harming shared production systems. Pattern choices that move pressure (queues, caches, bulkheads) are listed in the [pattern catalog](pattern-catalog.md); each one adds failure modes that sizing must account for.

## Decision output

Conclude with current demand, projected range/horizon, binding bottleneck, headroom, scaling mechanism, and the metric that triggers capacity action. Distinguish horizontal/vertical scaling and autoscaling. Autoscaling has reaction delay, warm-up and quota limits; it does not fix serial work or a saturated dependency. Queueing increases tolerance to bursts only while queue size/age and processing recovery are bounded. Operating the resulting capacity (thresholds, on-call actions, cost signals) is covered in [reliability and operations](reliability-operations.md).
