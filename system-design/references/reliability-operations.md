# Reliability, performance, and production operations

Use this for: defining service objectives, designing failure behavior, and running the system in production. This file is the canonical guide for SLO, RTO, and RPO guidance in the reference set.

Sources: [Google SRE](sources.md#sre-reliability-operations), [AWS Reliability Pillar](sources.md#sre-reliability-operations), [OpenTelemetry](sources.md#sre-reliability-operations), [NIST incident response](sources.md#sre-reliability-operations).

## Reliability goals

Define service level indicators from user journeys (successful/valid requests, latency, freshness, correctness, completion). Define SLOs as target over a window and distinguish contractual SLAs. Error budgets connect reliability investment and release risk; do not pick targets from current uptime alone. Set separate objectives for critical paths, asynchronous completion, and data freshness when needed.

For recovery, define RTO (time to restore) and RPO (acceptable data loss) from business impact. Assign them to services/data classes and validate dependencies; avoid "zero downtime" or "zero data loss" unless the design and tests support the literal promise.

## Availability and resilience

Map failure domains: process, host, rack/zone, region, control plane, identity, network, storage, DNS, deployment, human error, vendor, and correlated dependencies. Identify single points of failure and blast radius. Include redundancy, health checks, failover, graceful degradation, static/last-known-good behavior, and recovery. Redundancy can add coordination, split-brain, and cost; explain its assumptions. [Netflix fault tolerance](sources.md#first-party-engineering-case-studies) is an optional read on isolation, fallbacks, and circuit breakers in a high-volume system.

Test degraded capacity after failures and during rollout. Autoscaling can lag and cannot create capacity beyond quotas/dependency limits. A queue can buffer a burst but can create an unbounded backlog. Monitor age/lag and estimate drain time, not just depth. Workload shape and the capacity numbers behind these claims come from [requirements and capacity](requirements-and-capacity.md).

## Performance

Set end-to-end latency percentiles, throughput, concurrency, freshness, and resource budgets from user needs. Profile and load-test representative data/workflows. Examine tail latency, fan-out, N+1 queries, lock contention, serialization, allocation/GC, network hops, cold starts, hot keys, cache behavior, and external calls. Separate throughput from latency and CPU utilization from saturation. Tune the measured bottleneck before scaling other tiers.

## Observability and incident practice

Start from questions operators need to answer: Is a user journey failing? Which dependency or release changed? Is the system saturated? Are queues/replicas falling behind? Can it recover? Instrument metrics, structured logs, traces, and domain events with correlation/trace context. Use bounded-cardinality labels; avoid secrets and unnecessary personal data. OpenTelemetry is a vendor-neutral instrumentation/telemetry framework, not a monitoring backend.

Define dashboards, symptom-based alerts, ownership, escalation, runbooks, and actionable thresholds. Practice incident command, communication, containment, mitigation, and recovery. Postmortems should identify contributing system conditions and track corrective work without blame. The security incident path is described in [security and privacy](security-privacy.md).

## Change and launch readiness

Use staged rollout, canary or blue/green where risk justifies, feature flags with ownership/expiry, health criteria, and tested rollback. Monitor version skew and database compatibility. Launch readiness should include security review, capacity, dependency failure, load/failover, backup restore, observability, on-call ownership, runbooks, cost, and rollback. Test under realistic failure and configuration changes. A rollback that depends on a schema change is not a rollback unless the change is backward compatible or the forward-repair path is rehearsed; the migration rules are in [data architecture](data-architecture.md).

[Netflix chaos engineering](sources.md#first-party-engineering-case-studies) is an optional read on running controlled failure experiments with hypotheses and safety limits.

## Capacity and cost operations

Track saturation and demand against capacity, including peak/failover headroom, dependency quotas, storage growth, and backlog age. Define scaling thresholds and operator actions. Cost review should include idle and peak resources, egress, replication, backup/retention, telemetry volume, managed-service charges, and engineer time. Set budget signals and anomaly response. Sustainability/resource efficiency can be a quality attribute where relevant.

## Operations review test

Can an operator detect the failure, tell which users are affected, stop further damage, and restore the service within its stated targets? If not, the design is incomplete. Record the resulting decisions in [architecture method](architecture-method.md).
