# Cloud, containers, and platform architecture

## Placement and responsibility

Select on-premises, public cloud, hybrid, edge, or managed/serverless placement from latency, data residency, connectivity, security control, skills, procurement, cost, and recovery requirements. For each managed product, identify provider responsibility, customer configuration responsibility, service limits, quotas, failure modes, data location, support model, and exit/migration path. Provider architecture frameworks are useful, but their service recommendations are not technology-neutral facts.

Compare regions/zones, VPC/network boundaries, DNS, ingress/egress, private connectivity, service identity, secrets, and control-plane dependencies. Multi-cloud is justified by concrete portability, policy, or resilience needs; it also multiplies identity, networking, telemetry, deployment, and skills.

## Managed service trade-offs

A managed service trades control for operational burden. The trade is only good if the burden it removes is real for this team, and the lock-in it creates is priced.

| Dimension | What the provider takes over | What remains the customer's problem |
|---|---|---|
| Control | Patching, scaling, failover mechanics, capacity provisioning, some availability | Data model, schema, indexing, query patterns, isolation, retention, encryption key policy, region placement, which features to use |
| Operational burden | Fleet management, failover, patching, some scaling | Configuration drift, quota requests, IAM policy sprawl, network design, observability wiring, incident triage, version pinning, cost control, upgrade testing |
| Lock-in | Nothing | Query language, proprietary extensions, identity federation shape, event semantics, storage formats, deployment and configuration model, custom control-plane behaviour |
| Portability | Nothing | Data export path, schema and semantics translation, behaviour differences that only appear under failure or at scale |

The lock-in question is specific: name the capability that would make the exit expensive, then price the exit. Exit cost is dominated by data movement, semantic differences, and retraining of people, not by the code that calls the API. A service with a standard SQL interface, a documented export path, and no proprietary extensions is portable enough for most teams, and the residual risk is acceptable. A service whose correctness depends on its query planner, its consistency model, or its ordering guarantees is not.

A managed service also changes the failure surface rather than removing it. The provider owns the component's internal behaviour and the customer owns the configuration, the credentials, the network path, the quotas, and the client's view of the region. Most production incidents in managed-service architectures are configuration and quota problems, not provider faults. A design that assumes the provider handles everything is a design with an unowned failure domain.

## Build it yourself or adopt the managed service

Evaluate each candidate capability on the same questions, and write down the answers.

1. **What does the managed service actually remove?** List the specific work: patching, failover, capacity, on-call. If the team cannot name at least one real removal, the trade is not worth the lock-in.
2. **What does the team have to operate anyway?** Configuration, IAM, networking, quota, observability, incident triage, and version upgrades stay. If the remaining work needs the same expertise as building it, the managed service buys little.
3. **What is the cost shape?** Compare the fixed floor, the variable rate, and the cost of the expertise retained. Managed services usually win on the fixed floor and on time-to-first-value, and lose on unit cost at high, steady, predictable load, and on the cost of a capability the provider limits.
4. **What are the provider's limits and quotas, and do they bind before the design's limits?** A design that exceeds a quota is not a design. See the quota section below.
5. **What happens at the failure the provider does not cover?** Region loss, a control-plane outage, a quota exhaustion, a deprecation of a feature the design depends on, a price change, a support escalation that goes unanswered.
6. **What is the exit path and how long does it take?** Data export, re-platforming, and re-validation, with an estimate. An exit path that has never been exercised is a hope.
7. **Does the managed capability change the design's semantics?** A strongly consistent managed store lets the design drop a whole class of reconciliation. A read-optimized store forces compensation. Some choices are good for the product and bad for the architecture; the second kind has to be deliberate.
8. **Does the team want to be in this business?** Owning a database, a broker, or an auth server is a permanent speciality. The honest answer is often "not as a primary concern", and that argues for the managed service even at a higher unit cost.

## Quotas are the real scaling limit

The number that bounds a system is rarely the CPU of one node. It is the least of: physical capacity, the provider's per-account and per-service quotas, the provider's control-plane rate limits, the number of connections a dependency allows, the throughput of a single logical partition, and the rate at which quotas can be raised.

- Quotas are per account, per region, per service, and sometimes per resource type. A quota of N applies to the sum across a fleet, not per instance, and the fleet is what a team scales first.
- Quotas are raised by a support or API request and are not instantaneous. The design horizon must assume the quota you can have next month, not the quota you want.
- Some quotas are hard errors returned on the call. Others are silent degradations: a request is accepted and throttled internally, a replica is not scheduled, a backup is skipped, a log delivery is dropped.
- API request rates, connection counts, storage capacity, IOPS, throughput, and per-second invocation counts are all quotaable. A design that adds a service per request multiplies the quota consumption per user-visible action.
- Model the quota explicitly: maximum sustainable request rate per account, maximum instances, maximum storage, maximum partitions, maximum connections, maximum outbound bandwidth, maximum concurrent executions, and the raise procedure with its lead time.
- A quota increase is a dependency with a lead time, so it belongs in the capacity plan and in the risk register, with a mitigation: sharding the account, spreading across regions, batching, or degrading.
- Client-side and provider-side throttling interact. A provider throttle that arrives as a `429` is a signal the client must honour; a provider throttle that arrives as a `503` or a slow response is an ambiguous failure that will be retried, and the retry load will meet the quota again.

## Serverless economics

Function-as-a-service and similar scale-to-zero or per-invocation models have a cost shape that rewards a specific workload shape and punishes another.

- **Invocation cost** dominates for small, frequent, short work. The bill is dominated by the number of calls, so the design levers are fewer calls, batching, and caching.
- **Duration cost** dominates for long-running work, and duration billing is usually rounded up to a minimum granularity, so a fast function and a slow one can cost the same.
- **Memory cost** is billed as provisioned memory times duration, not actual usage, so over-provisioning to avoid a slow cold path can cost more than the compute it saves. Model the memory setting as a cost decision, not just a performance one.
- **Cold starts** come from provisioning, code load, runtime init, and dependency init. Mitigations are a provisioned or reserved concurrency pool, a smaller package, a slimmer dependency tree, and a keep-warm ping. Every mitigation has a cost: reserved concurrency is paid for whether used or not, and a keep-warm ping converts idle cost into billed invocations. The trade only pays off for a latency-sensitive path whose volume is low or spiky; for a steady high-volume path, a warm container is cheaper.
- **Duration limits** cap a single invocation. A limit means long work must be split, checkpointed, or moved elsewhere, which changes the failure model: a partial run is normal, and resumption must be idempotent.
- **Concurrency limits** cap simultaneous executions per account, per function, and per tenant. The account-level cap is the real one: it interacts with every other function in the account, so one runaway workload can starve unrelated ones. Concurrency is the correct unit to protect a downstream dependency, and it maps to a per-tenant fairness limit.
- **State and long-lived connections** are awkward. A function is short-lived and may be replaced between invocations, so a warm instance is a cache, not a guarantee. Anything that must survive belongs outside the function, which moves cost and latency elsewhere.
- **Local development and test** do not match production: the local emulation is a different runtime, and behaviour under concurrent cold starts is not reproduced locally. Test the deployed behaviour.
- The decision is about the workload shape: bursty, event-driven, infrequent, or per-request-compute work fits; steady, high-utilisation, long-lived, or stateful work usually does not. A hybrid where the request path is a function and the heavy work is a container is common, and it means two runtime models to operate.

## Containers and orchestration

Containers package processes and dependencies; they do not inherently provide resilience, orchestration, durable data, secure secrets, or observability. Design image provenance, minimal build context, `.dockerignore`, non-root runtime, resource limits, health behavior, signal handling, graceful shutdown, immutable tags/digests where appropriate, vulnerability updates, and reproducible builds. Separate build-time secrets from runtime configuration. Validate current Docker build checks and chosen runtime guidance.

Use an orchestrator when scheduling, service discovery, rollouts, autoscaling, isolation, or workload density justify its operational cost. Account for cluster/control-plane upgrades, network policy, persistent storage, observability, resource requests/limits, disruption budgets, and team on-call capability. Compose can help define local/test multi-container environments; it is not by itself a production availability architecture.

An orchestrator gives you placement, scheduling, service discovery, declarative configuration, rollout, and autoscaling. It does not give you durable state, transactional coordination between services, correct retry semantics, data replication, backup and restore, schema migration, or a human being awake at 3am. Those remain yours, and on a managed orchestrator they are still yours, expressed as manifests, policies, and runbooks.

The distinction that decides the question: a managed orchestrator removes the cluster and control plane and keeps the workload model; a managed container service removes the cluster, the control plane, and usually the node. The latter is closer to a PaaS and is the right answer for most teams that do not need node-level control. Take the node when a workload needs a specific kernel feature, a specialized accelerator, a network or storage driver, a consistent machine image, or a hard isolation requirement the service does not provide. Do not take the node because the team is curious about orchestration.

## Deployment model comparison

| Model | Control | Operational burden | Cost shape | Dominant failure modes |
|---|---|---|---|---|
| Virtual machines | Highest: OS, kernel, network, storage, runtime | Highest: image, patch, fleet, failover, on-call | Fixed per instance plus storage and egress; pays for idle capacity | Image drift, unpatched fleet, config divergence, noisy neighbours, capacity not matching load |
| Containers on self-managed nodes | High: full node and runtime control | High: cluster, control plane, upgrades, storage, networking | Fixed cluster floor plus nodes plus operator time | Control-plane outage, cluster upgrade breakage, storage and network plugin failure, no one watching the cluster |
| Managed orchestrator | Medium-high: workloads, policies, manifests; not nodes | Medium: manifests, policies, quotas, upgrades, workload debugging | Cluster or node floor plus workload usage; managed control plane | Version skew between add-ons and platform, quota exhaustion, shared control plane coupling, node pool exhaustion |
| Managed container service | Medium: image, config, scaling, network rules | Low-medium: manifests, environment config, permissions | Per workload running plus scaling events and egress | Configuration errors dominate; ambient failures come from the managed control plane and from quota and network limits |
| Serverless functions | Low: code, memory, timeout, concurrency | Low: code, permissions, configuration, cold-start tuning | Per invocation and per GB-second, plus concurrency and egress; idle is near zero | Cold start latency, timeout truncation, concurrency starvation, downstream throttling amplification, state loss between invocations |
| Platform as a service | Low-medium: application, config, scaling | Low: deploy, config, add-ons | Per application instance or dyno plus database and egress | Platform-imposed runtime limits, vendor-specific service limits, less diagnosability, migration effort at exit |
| Managed database | Low: schema, queries, indexes, policies | Low-medium: schema, sizing, backups, failover parameters, credentials | Provisioned capacity or consumed IOPS plus storage and backups | Configuration-induced failure, failover and reconnect storms, plan limits, maintenance-window surprise |
| Third-party SaaS or API | None over the provider's interface | Low in ops, high in dependency risk | Per seat, per call, or per record; price and rate limits set externally | Provider outage and degradation, API change and deprecation, rate limits, data export constraints, price change |

Read the table down the operational burden column before reading the cost column. The lowest-burden option that meets the isolation, compliance, and portability requirements wins; a cheaper model the team cannot operate is more expensive, because the failure arrives at 3am with no runbook.

## Multi-region placement

- **Single region, multi-zone.** The default. Zones are independent failure domains inside a region with independent power, cooling, and networking, and they are cheap. Cross-zone traffic is a network hop, so it is not free, and a service that fans out across zones on every request pays that hop on every request. This is the right answer until a stated requirement (latency, residency, or a region-level availability target) says otherwise.
- **Read replicas in a second region.** The write path stays in one region; reads are served nearer to the user or from a replica. The cost is replication lag, so the read must tolerate staleness, and the design must name which reads may be stale and by how much. Promotion of a replica is a failover with a promotion procedure, and the write path's cold start after promotion is a real outage contributor.
- **Active-passive.** The standby is scaled down or stopped and promoted on failover. The recovery time is the sum of detection, promotion, and the application's reconnect and warm-up, and the design must state that sum as the RTO rather than assuming instant. Promotion also has split-brain risk when the old primary is partitioned but not dead; fencing or a decision authority is required.
- **Active-active.** Both regions serve traffic. The cost is a consistency model that must survive a partition: either a single writer with a routing decision, or a multi-writer model with conflict resolution that the product has to define. Most products do not want a single-writer model, so a conflict-free replicated data type or a last-writer-wins rule is chosen, and the rule becomes a product behaviour. Active-active is the most expensive option in engineering time, in operational complexity, and in permanent test burden, and it must be paid for by a stated requirement rather than by a preference for elegance.
- **Global traffic management.** DNS-based routing with health checks moves traffic between regions, and its resolution TTL sets a floor on the failover time, which is often larger than the target. Decide failover by data (which write is authoritative) or by traffic (which region serves), and do not conflate them: traffic can be moved in seconds while the data decision takes longer, and moving traffic before the data question is settled produces split-brain.
- The honest cost of multi-region is not the replica, it is the testing: every combination of region, zone, and dependency failure must be rehearsed, because the interesting failures only appear when two things fail at once.

## Egress cost as a design driver

Egress is billed per byte leaving the platform, per region, per service tier, and often differently for internal traffic and the public internet. Because it is a unit price times a volume, it scales with usage exactly as traffic does, and it is invisible until the bill arrives.

- Design drivers: how many bytes cross a boundary, how many times a byte is copied, and how many boundaries it crosses. A response that fans out to three internal services in one region is cheap; the same fan-out across regions is a cost line. A cache in front of a cross-region database turns an egress charge into a local read.
- Chatty internal APIs are a cost multiplier, because each hop is a billable byte in transit plus a serialization cost plus a latency cost. Interface design and cost design are the same exercise.
- Logging and telemetry are egress: shipping logs, metrics, and traces to a region or a vendor is billed, and log volume is driven by traffic and by verbosity, so a debug flag left on in production is a cost incident.
- Backup and replication between regions are egress, and they run continuously.
- The mitigations are structural: keep the compute near the data, cache what is read often, compress payloads, aggregate before crossing a boundary, batch, and prefer push (one outbound stream to many consumers) over pull (many inbound reads of the same object). Push is not always cheaper, and a push to a shared subscription fans out inside the provider for free while a pull from object storage is billed per request.
- Put egress in the capacity model and the cost model with a sensitivity, because a growth plan that assumes a fixed response size is usually wrong. See [design brief](design-brief.md) for the cost model format.

## Platform and delivery

Define infrastructure ownership, environment boundaries, identity and policy, configuration, CI/CD, artifact promotion, deployment, rollback, and disaster recovery. Keep control-plane failures from unnecessarily stopping critical serving paths where the availability target justifies it. Prefer paved roads and platform capabilities that reduce repeated toil; avoid creating a platform team/product without consumers and ownership.

Review vendor lock-in as the cost of using higher-level managed capabilities versus portable primitives. Portability is a requirement with cost, not an unconditional virtue. Record the capability that would trigger an exit and a testable recovery path.

## Vendor-specific notes

The reasoning above is provider-neutral. The following are illustrative examples of how one provider's product line maps onto the models above, and are labelled as such so they are not read as general facts. Verify current limits, prices, and behaviours against the provider's own documentation before relying on any of them.

- *(AWS-oriented example)* A managed container service abstracts nodes and the control plane, while a managed orchestrator retains the node model and adds scheduling, policy, and rollout. Object storage separates request cost, storage, and egress, which makes egress the term that surprises on a chatty design.
- *(GCP-oriented example)* Serverless functions bill per invocation and duration with a memory-provisioning multiplier, and a configurable concurrency cap, which is the account-level limit that starves unrelated functions.
- *(Azure-oriented example)* A platform-as-a-service model binds deployment to a configuration model with platform-imposed runtime limits, and the exit path requires re-expressing configuration in a different model.

Provider feature comparisons age quickly. Re-check current documentation for any specific product, and prefer the [source guide](sources.md) plus first-party documentation over remembered capability lists.
