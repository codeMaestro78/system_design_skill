# Cloud, containers, and platform architecture

## Placement and responsibility

Select on-premises, public cloud, hybrid, edge, or managed/serverless placement from latency, data residency, connectivity, security control, skills, procurement, cost, and recovery requirements. For each managed product, identify provider responsibility, customer configuration responsibility, service limits, quotas, failure modes, data location, support model, and exit/migration path. Provider architecture frameworks are useful, but their service recommendations are not technology-neutral facts.

Compare regions/zones, VPC/network boundaries, DNS, ingress/egress, private connectivity, service identity, secrets, and control-plane dependencies. Multi-cloud is justified by concrete portability, policy, or resilience needs; it also multiplies identity, networking, telemetry, deployment, and skills.

## Containers and orchestration

Containers package processes and dependencies; they do not inherently provide resilience, orchestration, durable data, secure secrets, or observability. Design image provenance, minimal build context, `.dockerignore`, non-root runtime, resource limits, health behavior, signal handling, graceful shutdown, immutable tags/digests where appropriate, vulnerability updates, and reproducible builds. Separate build-time secrets from runtime configuration. Validate current Docker build checks and chosen runtime guidance.

Use an orchestrator when scheduling, service discovery, rollouts, autoscaling, isolation, or workload density justify its operational cost. Account for cluster/control-plane upgrades, network policy, persistent storage, observability, resource requests/limits, disruption budgets, and team on-call capability. Compose can help define local/test multi-container environments; it is not by itself a production availability architecture.

## Platform and delivery

Define infrastructure ownership, environment boundaries, identity and policy, configuration, CI/CD, artifact promotion, deployment, rollback, and disaster recovery. Keep control-plane failures from unnecessarily stopping critical serving paths where the availability target justifies it. Prefer paved roads and platform capabilities that reduce repeated toil; avoid creating a platform team/product without consumers and ownership.

Review vendor lock-in as the cost of using higher-level managed capabilities versus portable primitives. Portability is a requirement with cost, not an unconditional virtue. Record the capability that would trigger an exit and a testable recovery path.
