# Architecture testing, migration, and evolution

## Verification portfolio

Tie tests to requirements, risks, and failure modes. Use the lowest-cost test that gives credible evidence, but do not substitute unit tests for cross-boundary behavior.

- Unit/domain tests: invariants, authorization rules, state transitions.
- Contract/schema tests: provider-consumer compatibility, event evolution, generated API docs.
- Integration tests: actual database, queue, identity, and external adapters.
- End-to-end journey tests: critical user outcomes and degraded behavior.
- Property/model-based tests: stateful protocols, idempotency, concurrency, invariants.
- Performance/load/soak tests: latency percentiles, throughput, queue drain, resource saturation, realistic data.
- Resilience tests: timeout, failover, dependency outage, overload, zone loss, restore, network fault, recovery.
- Security/privacy tests: negative authorization, tenant isolation, abuse/limits, secrets, data deletion, audit.
- Operational exercises: deploy/rollback, backup restore, incident drills, failover and runbooks.

Specify test environment, data safety, success criteria, abort conditions, and production blast radius. Tests should prove properties meaningful to the user, not just mirror code structure.

## Schema evolution compatibility

Schema compatibility is a property of the pair (old schema, new schema) in a direction, and a change that is compatible in one direction is not automatically compatible in the other.

- **Backward compatible**: a consumer running the new schema can read data written with the old schema. This is the property that lets a producer be upgraded before the consumers, and it is the usual default.
- **Forward compatible**: a consumer running the old schema can read data written with the new schema. This is what lets a consumer be upgraded first, and it is what makes a rolling deploy of consumers safe.
- **Full**: both directions. Required only when old and new versions of the same producer and consumer coexist and each may write.

What each forbids:

| Change | Backward | Forward | Notes |
|---|---|---|---|
| Add a field with a default | Yes | Yes | The default covers readers that have not seen the field |
| Add a field without a default | No | Yes | A reader whose schema lacks the field cannot resolve the data unless the reader's schema supplies a default |
| Delete a field | Yes, if the new schema supplies a default | No | The removed field is not written again; old readers then miss it and need their own default |
| Rename a field | No | No | Needs an alias or a reader-side mapping; otherwise it is a delete plus an add |
| Change a field's type | No | No | Wire format and semantics both change; treat as a new field |
| Widen a numeric type | Yes | Yes | Widen only, never narrow; narrowing is not compatible in either direction |
| Add an enum symbol | Yes | No | A strict reader that rejects unknown symbols fails on the new value |
| Remove an enum symbol | No | No | Both directions break; treat the enum as append-only or add a "deprecated" state |
| Make an optional field required | No | No | Breaks readers of old data and writers of new data |
| Add a required field | No | No | Same, and it is the single most common source of a broken deploy |

Protobuf specifics: fields are matched by tag number, not by name. A tag number is never reused, and a removed field has its number and name reserved so it cannot be reallocated later. Renaming a field is wire-compatible and source-incompatible, which is a compile-time break and a runtime no-op. Changing `int32` to `int64`, or `int32` to `uint32`, is wire-compatible but not source-compatible. A required field in the proto2 style cannot be added in a compatible change; proto3 has no required fields, which is one reason proto3 is the safer default. A Protobuf service method cannot change its signature without breaking the generated stub.

Avro specifics: resolution is by writer schema and reader schema, and the writer's schema travels with the data, so a reader resolves what it can. A new field must have a default for an older reader to resolve it. Enum symbols are matched by name, and a reader that does not know a symbol cannot resolve the value unless the schema carries a fallback. Avro's field resolution rules make name changes and deletions resolvable with an alias or a default, but the compatibility tooling still has to be told to use them.

**The default when the mode is unknown is backward compatibility**, checked in CI against the registered schema, and the answer is stated in the contract rather than left to a reviewer. If there is no schema registry, then the compatibility rule is a written team convention plus a CI check that diffs the schema against the previous released version, and the convention is enforced by that check rather than by memory. A schema that is only compatible by luck is not compatible.

A schema change is not finished when the schema compiles. The compatibility check runs against the *previous released* schema, the readers that are deployed are enumerated, and a reader that cannot be upgraded in the same deploy is handled explicitly with a tolerant-reader change or a versioned topic.

**The dual-write hazard.** Writing the old and the new form at the same time creates a window in which the two disagree, and the window is not closed by a retry. The failure modes are: one write succeeds and the other fails, so the stores diverge; the two writes are ordered differently than expected, so a reader between them sees the older value; a retry after a partial failure writes the pair twice; a crash between the writes leaves a half-applied state with no record that it was half-applied. A dual write without a comparison and a repair process is not a migration, it is a second source of truth that disagrees quietly. Prefer, in order: a single atomic write (one table, one column, one row), an outbox with a relay and a comparison, or two stores with a reconciler that names the authoritative side. The dual-write window needs a stated maximum duration, a comparison metric, and an owner for the repair.

See [distributed systems](distributed-systems.md) for the messaging side of the same problem and [data architecture](data-architecture.md) for storage-level evolution.

## Observability mechanics

**Metric types.** A counter is monotonically increasing and resets on restart; the useful value is its rate, `rate(counter[window])`, which is also what a restart-safe alert should use. Counters suit requests, errors, bytes, and retries. A gauge is an instantaneous value that goes up and down, and it suits queue depth, active connections, in-flight requests, pool saturation, and cache size. A gauge is not for quantities that only accumulate, because a counter that is accidentally implemented as a gauge is a rate that reads as zero after a restart. A histogram buckets observations of a value, usually latency, and its bucket boundaries are the design decision: they should sit on the SLO thresholds so the dashboard can answer "how much traffic exceeded the objective" without arithmetic. A summary reports quantiles directly and is not aggregatable across instances in most backends, so a quantile computed from a summary is a quantile of one instance. Client-side histograms aggregate before they leave the process and give a more accurate distribution at a higher memory cost; server-side histograms are cheaper and approximate. A distribution is the general form. Pick one type per question and label the metric so the type is visible in the tool, because a counter read as a gauge produces a silent false reading.

**RED and USE.** RED is for request-serving services: Rate (traffic arriving), Errors (failures), Duration (latency). Three panels, per service, answer "is the user path healthy". USE is for resources: Utilization (time busy divided by time available), Saturation (work waiting because capacity is exhausted), Errors (failures of the resource itself). Use it on CPUs, memory, disk and IOPS, network, thread pools, connection pools, and queue depth. Saturation is the leading indicator and the one that pages. A CPU at a high utilization figure can be healthy if the work is short and the queue is empty; a connection pool with one free slot is saturated and will start rejecting work even though utilization reads low. Capacity work is driven by the saturation metric, not the utilization metric.

**Sampling.** Head-based sampling decides at the source, so the decision is consistent for the whole trace and the trace remains coherent, and the trade is that the sampling decision is made before the interesting part of the request is known. Tail-based sampling decides after collection, so errors and slow traces can be kept at a much higher rate than average traffic, at the cost of buffering at the collector. Rules: never sample away errors, never sample away the slow tail, keep the low-rate aggregate metric at full rate so the SLI is computed from all traffic rather than from a sample, and record the sampling rate on the metric so the number can be corrected. A latency percentile computed from a sampled trace is a percentile of the sampled subset; if the sampling is head-based and uniform, that is acceptable for the body of the distribution, and it is wrong for the tail that matters most. SLO error rates are computed from counters, which are never sampled.

**Cardinality budget.** A metric with labels has one time series per distinct combination of label values. For a metric with labels A, B, and C, the series count is the product of the distinct value counts, not the sum. Illustrative arithmetic: route (200) x method (4) x status (5) x tenant (500) = 2,000,000 series for one metric. The total series count of an instrumented service is the sum over metrics. The budget is derived, not habitual: take the backend's documented limits on series per metric, per tenant, and per account, take the documented per-series storage and cost, and set a maximum series count per metric and a total for the service that fits inside both. Then hold the label set to a fixed set of dimensions with bounded values, and enforce the budget with a check in CI or a lint on the instrumentation.

The labels that break a budget are the unbounded ones: user id, request id, session id, full URL path including an id, raw error message, exception class, email address, timestamp, build id, and anything taken from a client-supplied string. The fix is usually not to drop the information but to move it: exemplars attach a trace id to a series, traces hold the per-request detail, and a small allowlist of known status or error codes replaces the raw message. Label cardinality is a design decision with a cost, and the cost lands on the backend that the team does not own.

**Multi-window burn-rate alerting.** Burn rate is the ratio of the observed error rate to the allowed error rate, that is `burn_rate = observed_error_rate / (1 - SLO)`. A burn rate of 1 consumes the error budget exactly as fast as the window length, so a burn rate of 14.4 for an hour consumes 14.4 hours of budget. The general relation: the fraction of the budget consumed by a sustained burn is `burn_rate x window / budget_window`, so the burn rate needed to consume a fraction f of the budget within a window T is `B = f x budget_window / T`.

With a 30-day budget window, the standard alert tiers are:

| Budget consumed | Burn rate | Long window | Short window | Response |
|---|---|---|---|---|
| 2% | 14.4 | 1 hour | 5 minutes | Page |
| 5% | 6 | 6 hours | 30 minutes | Page |
| 10% | 3 | 1 day | 2 hours | Ticket |
| 10% | 1 | 3 days | 6 hours | Ticket |

The long window sets the budget consequence: `0.02 x 720h / 1h = 14.4`, `0.05 x 720h / 6h = 6`, `0.10 x 30d / 1d = 3`, `0.10 x 30d / 3d = 1`. The short window gives fast detection. The alert fires only when both conditions hold, so a brief spike that would have consumed a negligible share of the budget does not page, while a sustained burn pages within minutes rather than after the whole window. A single-window alert on a fast burn rate pages on every brief spike; a single-window alert on a slow burn rate detects a real outage too late. The tiers are computed from the SLO and the budget window, not chosen as round numbers, and they are recomputed when the SLO changes.

## Rate limiting as a test surface

Rate limiting is where an untested concurrency bug becomes a production incident, and the tests are specific.

- **Over-limit behaviour**: with a limit of N per window, requests 1 to N succeed and request N+1 is rejected with the documented status and error code. The rejection is a `429` with a `Retry-After` header and a stable machine-readable code, not a generic `500` and not a silently queued request.
- **Retry-After correctness**: the value equals the time until the next request would be admitted, within a stated tolerance. A client that waits exactly the stated interval is admitted on its first attempt afterwards, and that is asserted, not assumed. A missing or wrong header in the rejection path is a defect, because the client cannot pace itself without it.
- **Admission at the boundary**: a burst of concurrent requests that straddles the limit admits exactly the limit and rejects the rest. This catches a check-then-act limiter that reads the counter and then increments it non-atomically.
- **Shared-state correctness**: the limit is global, not per instance. The test runs against several instances and asserts the fleet admits no more than the global limit. A limiter that keeps local state fails here, and this is the single most valuable rate-limit test, because the bug is invisible in a single-instance test and in development.
- **Per-tenant fairness**: tenant A exhausting its budget does not cause tenant B to be throttled, and A's abusive traffic does not consume the shared global budget that B depends on. A's quota recovers after the stated window. A fleet where one tenant's traffic can exhaust a shared pool fails this test.
- **Burst allowance**: the configured burst is admitted, and the sustained rate after the burst is enforced.
- **Window boundary**: a fixed window and a sliding window behave differently at the boundary, and the test asserts the behaviour that the contract states.
- **Dependency failure**: when the shared counter store is unreachable, the documented fail-open or fail-closed behaviour is what happens. Fail open is a denial-of-service exposure and fail closed is an availability exposure, and the test asserts the chosen one rather than leaving it to implementation.
- Test at three levels: the algorithm against a fake clock, the service in one process, and the fleet across instances. See [API and contract design](api-design.md) for the limiter algorithms and the shared-state trade-off.

## Cache as a test surface

A cache changes behaviour, so the tests must assert behaviour rather than assume it.

- **Cold start**: the first request after a deploy, a flush, or an eviction serves a correct response within the stated cold-start budget, and does not error. Under a cold cache with high request rate, assert the origin request count, not only correctness.
- **Stampede**: many concurrent requests for one hot key when the cache is empty must not all miss through to the origin. The origin load must be bounded by the designed mechanism (single-flight, a lock, stale-while-revalidate) and the test asserts the bound. A cache that returns correct answers while melting the origin has still failed, and this is the classic cache incident.
- **Invalidation correctness**: after a write, a subsequent read reflects the write within the stated propagation delay, for each write strategy used (write-through, write-behind, invalidate-on-write, read-through). The test asserts the bound, not instantaneous visibility.
- **Stale reads**: within the TTL, a read may return a value older than the latest write. The test asserts that the staleness is within the stated bound, so a real regression is caught without forcing the removal of a legitimate optimization. A test that asserts zero staleness will pass only for an uncached design, and writing it against a cached design means either the assertion is wrong or the cache is unnecessary.
- **Cache down**: with the cache unreachable, the documented fallback is what happens: fail open to the origin, or fail closed, or serve a stale value. The origin's behaviour under a total cache outage is measured, because a fallback that doubles origin traffic can cause the outage it was meant to survive.
- **Eviction and negative caching**: an evicted key is recomputed correctly, and a negative cache entry does not shadow an entity that was created after the negative entry was stored.
- **Poisoned cache**: an entry containing wrong data, from an upstream bug or a bad deployment, is not re-served forever. The invalidation and versioning path that removes it is named and tested.
- **Tenant isolation**: a cached key from one tenant is never served to another, which is the same tenant-binding rule that idempotency keys follow.

## Property-based and model-based testing

Property-based testing generates inputs and sequences and asserts a property that must hold for every generated case, rather than asserting a fixed expected value per case. It finds the boundary cases nobody wrote down, provided the generator reaches them and the property is stated precisely.

**Stateful models for idempotency.** The model is a small in-memory implementation of the intended behaviour, not a copy of the real code. For idempotency, the model is a map from (tenant, key) to the stored response, and the properties are: applying the same (tenant, key, body) twice has the same effect as applying it once; the same key with a different body produces a conflict and no second effect; a key from one tenant never affects another tenant; and the stored response is byte-identical to the original response. The generator produces sequences of requests with repeated keys, repeated bodies, changed bodies, interleaved tenants, and concurrent arrivals. The implementation under test and the model are both fed the same sequence and their states are compared after each step.

**Stateful models for concurrency.** A sequential model cannot express a race, so the harness runs the implementation one operation at a time and explores the interleavings: at each step, either the model or the implementation takes the next action, and the harness enumerates the orders. The properties are the forbidden states, such as two live holders of one exclusive resource, a committed offset that is ahead of the applied effect, a count that exceeds the number of distinct items, or a balance that goes negative. This is how a lease-expiry race or a check-then-act limit is found: the model has one holder, the implementation can produce two, and the interleaving that does it is reported as a reproducible sequence.

**Seeding a model.** Write the model from the specification, not from the implementation, and keep it small enough to read in one sitting; a model that mirrors the implementation cannot find the implementation's bugs. Validate the model against the implementation on deterministic scenarios first, so a failure means one of the two is wrong rather than the model being nonsense. Seed the generator with known-bad sequences: the bug that was fixed, the sequence from the customer's report, and the boundary that broke last time. Keep the seed corpus in the repository, and record the generator version and the seed with every failure, so a failure found in CI reproduces exactly and a failure found in production is a new corpus entry. Use the framework's shrinking to minimise a failing sequence, because a minimal sequence is a diagnosable one. Bound the generator: an unbounded sequence space is a flaky test suite, so bound the operation count, the number of distinct keys, and the number of tenants.

**Properties worth stating for a service boundary**: no operation returns another tenant's data; a rejected operation leaves no partial effect; the response to a repeated idempotent request is identical to the original; the state after any interleaving matches the model; a timeout never leaves the system in a state that the model forbids; and no input, including empty, oversized, duplicated, or non-UTF-8 input, causes an unhandled failure or unbounded memory growth.

## Migrations

Plan expand/contract changes for APIs, database schemas, events, and infrastructure. Support mixed-version deployment where necessary. For data movement, state source of truth, backfill idempotency, checkpoints, rate limits, validation/reconciliation, dual-read/write window, cutover signal, rollback/forward repair, and cleanup. Estimate migration load and lock impact; rehearse on production-like volume. Never assume rollback is safe after irreversible writes.

For service extraction, first establish module ownership/contracts and measure the reason for separation. Move one bounded capability, add telemetry and reconciliation, then remove old paths only after traffic and correctness evidence. Strangler migration should include routing, coexistence, data ownership, rollback, and retirement plan.

## Evolution and fitness functions

Architecture changes as requirements and evidence change. Use lightweight fitness functions (automated checks or operational measures) for key constraints: dependency direction, API compatibility, latency budget, tenant isolation, cost ceiling, or restore objective. Make checks enforceable only where ownership and false-positive handling exist. Keep ADRs, diagrams, contracts, and runbooks current as part of change work.

Use feature flags with owner and expiry. Avoid permanent dual systems and compatibility paths without retirement criteria. Revisit decisions when demand, team ownership, regulations, platform capabilities, cost, or failure evidence crosses a stated trigger.
