# Reliability and operations

Use for production readiness, incident/scaling review, and recovery design. Sources: [Google SRE](sources.md#sre-reliability-operations), [AWS Reliability Pillar](sources.md#sre-reliability-operations), [OpenTelemetry](sources.md#sre-reliability-operations), [NIST incident response](sources.md#sre-reliability-operations).

## Define service promises

Identify critical user journeys and measure their success, latency, correctness and freshness with service level indicators (SLIs). Set service level objectives (SLOs) with a window, percentile/denominator, and owner; an error budget is the tolerated gap from the objective. A service level agreement (SLA) is a contractual commitment and need not equal the internal SLO. Do not substitute “high availability” for a target. Alert on meaningful user impact and budget burn, then use resource metrics for diagnosis.

## Design failure and recovery

For each dependency, list failure mode, affected users, detection, isolation/degradation, failover, and recovery. Include overload, regional failure, data corruption, expired credentials, bad deploy, and human error where relevant. Define recovery time objective (RTO) and recovery point objective (RPO) from business impact. Match backups, replication and disaster recovery strategy to those targets; test a restore and record elapsed time and data loss. Faster recovery often costs more and adds complexity.

## Operate the system

- Capacity: forecast peaks and growth; watch saturation, queue age, hot partitions and headroom. Load test representative data and failure modes.
- Telemetry: correlate metrics, logs and traces through request/job IDs; instrument critical paths, errors, retries, dependency latency, and cost. Bound cardinality and remove secrets and personal data.
- Release: choose rolling, blue-green, canary, or feature flags according to rollback speed and migration risk. Evaluate canary against representative control traffic; plan reversible schema/data changes.
- Incidents: assign alert owner, escalation, runbook, communications, and post-incident review. Exercise failover and disaster recovery; use chaos experiments only with clear hypotheses and safety limits.

**Review test:** Can an operator detect the failure, tell which users are affected, stop further damage, and restore the service within its stated targets? If not, the design is incomplete.
