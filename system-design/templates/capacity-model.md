<!-- Use when load is unknown, growing, or spiky enough that a sizing argument, a bottleneck, and a scale trigger are needed before committing to a design. -->

# Capacity model: <system or component>

Date: YYYY-MM-DD
Author: <role or name>
Horizon: <date or traffic multiple the model covers>
Scenarios: <low | base | peak | burst, and the reason each exists>
Status: Draft | Reviewed

## 1. Inputs

Every input carries units and a source. Mark each as Observed, Given, Assumed, or Estimated. An Estimated input needs a range.

| Input | Value | Unit | Status | Source or derivation | Range | Owner to validate |
|---|---|---|---|---|---|---|
| Active users | | users | | | | |
| Sessions per user per day | | sessions/user/day | | | | |
| Requests per session | | requests/session | | | | |
| Working hours per day | | hours/day | | | | |
| Request size (mean) | | bytes | | | | |
| Response size (mean) | | bytes | | | | |
| Read/write mix | | % reads | | | | |
| Payload per domain object | | bytes | | | | |
| Objects created per day | | objects/day | | | | |
| Retention period | | days | | | | |
| Third-party quota or limit | | requests/s or calls/day | | | | |

## 2. Request rate

Show the arithmetic. Do not state a rate without the division that produced it.

| Scenario | Computation | Result | Unit |
|---|---|---|---|
| Average | <sessions/user/day> x <requests/session> x <users> / <seconds of active window> | | requests/s |
| Peak | <average> x <peak factor> | | requests/s |
| Burst | <short window spike> | | requests/s |

Peak factor: <value, its source, and what makes the peak occur, for example "morning clinic intake concentrated in 30 minutes">
Read and write rates: <average x read share> requests/s read, <average x write share> requests/s write

## 3. Fan-out

| Operation | Downstream calls per request | Called service | Resulting dependency rate at base | Resulting dependency rate at peak |
|---|---|---|---|---|
| | | | | requests/s |

Total dependency rate: <sum, in requests/s>
Note which calls are sequential (add latency) and which are parallel (take the max). State the fan-out for background and batch work separately, since it does not share the user-facing path.

## 4. Concurrency

Little's Law:

```
concurrency (in flight) = arrival rate (requests/s) x mean time in system (s)
```

| Scenario | Arrival rate (requests/s) | Mean duration (s) | Concurrency (in flight) | Source of the duration | Tail note (p99 duration) |
|---|---|---|---|---|---|
| Base | | | | | |
| Peak | | | | | |

This is an average, not a safe ceiling. Record the p99 duration separately and state the concurrency implied by it: <arrival rate x p99 duration> in flight. If the two differ materially, the service must be sized for the tail, and say so.

Where the queue absorbs the difference: <queue name, and the age rather than the depth as the limit>

## 5. Storage growth

```
stored bytes = objects/day x bytes/object x retention days x (1 + index and replica overhead)
```

| Store | Objects/day | Bytes/object | Retention (days) | Raw size | With overhead | Growth rate | Notes |
|---|---|---|---|---|---|---|---|
| Primary | | | | | | | |
| Index | | | | | | | |
| Replica | | | | | | | |
| Object storage | | | | | | | |
| Logs and telemetry | | | | | | | |
| Backups | | | | | | | | |
| Derived: cache, search, analytics | | | | | | | |

Total growth: <GB per day and GB per month, with decimal or binary units stated>
Peak steady-state size: <size at end of horizon>
Rebuild time: <time to rebuild the largest derived store at the write rate above>
Note the primary/derived divergence: a derived store that grows faster than its source needs a compaction or retention rule.

## 6. Bandwidth

```
throughput (MB/s) = requests/s x payload bytes x fan-out x (1 + protocol overhead)
```

| Flow | Direction | Requests/s | Bytes each | Fan-out | Throughput | Egress or internal |
|---|---|---|---|---|---|---|
| | | | | | | Egress/Internal |
| | | | | | | |

Peak egress: <value and unit>. State the cost driver and whether egress is metered. Account for replication, backup, and log shipping traffic separately.

## 7. Latency budget

| Stage | Budget (ms) | Basis | Notes |
|---|---|---|---|
| DNS and TLS | | | |
| Edge and gateway | | | |
| Application compute | | | |
| Downstream calls | | | |
| Database or cache | | | |
| Queue wait | | | |
| Total | | | |

Parallel branches take the max; sequential dependencies add. State the scope of the measurement: client-to-edge, service boundary, or full transaction.

## 8. Bottleneck and scale trigger

| Resource | Limit at current size | Saturation point (metric and threshold) | Headroom at peak | Scaling mechanism | Scaling trigger |
|---|---|---|---|---|---|
| CPU | | | | | |
| Memory | | | | | |
| Disk IOPS or throughput | | | | | |
| Connections | | | | | |
| Storage capacity | | | | | |
| Network | | | | | |
| Hot key or partition | | | | | |
| Third-party quota | | | | | |
| Queue age | | | | | |
| Connection pool or lock contention | | | | | |

First likely bottleneck: <the resource that saturates first, at what load, and the evidence or reasoning that identifies it>
Scale trigger: <the metric and threshold that starts scaling work, who watches it, and how long the action takes>
What scaling does not fix: <serial work, a saturated dependency, an unshardable hot key, a quota, and human on-call capacity>
Degraded capacity: <what the system can serve after losing an instance, a zone, a replica, or a dependency, in requests/s and percent>

## 9. Cost

| Driver | Unit | Unit cost | Quantity at base | Quantity at peak | Cost at base | Cost at peak | Source |
|---|---|---|---|---|---|---|---|
| Compute | | | | | | | |
| Storage | | | | | | | |
| IO or requests | | | | | | | |
| Egress | | | | | | | |
| Observability | | | | | | | |
| Replication and backups | | | | | | | |
| Managed service and support fees | | | | | | | |
| On-call engineering effort | hours/week | | | | | | |

Pricing source and date: <link or note that prices were checked on YYYY-MM-DD>

## 10. Assumptions and unknowns

| Item | Status | Effect if wrong | Validation action | Owner |
|---|---|---|---|---|
| | | | | |

## Before you deliver

- No invented numbers. Every input carries units and a source, and every result shows the formula that produced it.
- Estimates carry a range, and the range is wide enough to contain the reality.
- Every component in the model maps to a requirement, a constraint, or a named risk reduction, and unmodeled components are named.
- The concurrency figure states that Little's Law gives an average and that the tail is sized separately.
- The first likely bottleneck and the scale trigger are both named, with the metric and threshold.
- Load test evidence is cited where it exists, and the difference between modelled and measured values is stated.
- Restore and rollback are drills with an owner and a date, not intentions.
