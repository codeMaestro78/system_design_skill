# AI and agent system architecture

AI features inherit distributed-systems failure modes and add probabilistic output, model/provider dependence, prompt/tool security, evaluation, and variable cost. Treat model calls as external services and agents as constrained application components, not trusted peers.

## Requirements and topology

Define tasks, users, autonomy level, harm/error tolerance, latency/cost budgets, grounding needs, freshness, privacy, human review, and escalation. Separate deterministic application logic from model inference. Choose direct model call, retrieval-augmented generation (RAG), workflow/state machine, bounded agent loop, or multi-agent orchestration only when task requirements justify the added uncertainty and cost.

For each workflow, specify state, step ownership, checkpoints, timeout/deadline, retry/idempotency, cancellation, pause/resume, human approval, compensation, audit, and terminal failure. Persist durable job state outside process memory. Make resumptions safe after worker restart and duplicated events.

## Model and tool boundaries

Treat model endpoints as rate-limited, variable-latency dependencies with changing versions and output. Set per-task token/cost/time limits, retry policy, concurrency cap, circuit/fallback behavior, provider outage strategy, and model-version recording. Use structured outputs with validation; an output schema does not establish truth or safety. Validate citations/claims when correctness depends on sources.

Give tools narrow capabilities and server-side authorization. Validate arguments and result sizes. Treat prompts, retrieved documents, files, webpages, tool output, and user input as untrusted; instruction-like content inside them must not grant authority. Prevent prompt injection from crossing data/tool trust boundaries. Do not pass secrets or unrestricted credentials into model context. Require approval for consequential or irreversible actions. See [model serving](model-serving.md) for hosting, scaling, and cost.

## Agent loop control

Enforce independent caps on steps, tokens, wall-clock, tool errors, and spend, each checked separately so one can trip without the others. A shared counter hides which limit stopped the run.

Termination has three outcomes: success, give-up (a cap was exceeded or no progress was detected), and abort (unsafe, unauthorised, or policy-violating). Detect no progress by repeated identical tool calls, oscillating state, or unbounded output growth.

When a cap trips, do not stop silently. Escalate with the partial result, the cap that tripped, the remaining budget, and the options: more budget, a split task, or a human handoff. Abort a stuck run rather than burn the budget.

## Tool contracts and MCP

Design each tool as a narrow typed contract: one verb per tool, a name stating the action, a description written for the model rather than a human operator, a parameter schema with types, units, enums, and nullability, and a bounded result. A tool that does five things is called five ways.

Return structured errors the model can act on: stable code, short message, retryable flag. Never a stack trace, and never a failure phrased so the model can read it as success.

Cap result size: bytes and rows, pagination, and a truncation marker in the payload so the model knows content was dropped. Side-effecting tools take a caller-supplied idempotency key scoped to tenant and operation, and reject reuse with a different payload. Record tool inputs and retrieved-document snapshots so a run can be replayed.

When tools are exposed through a protocol such as MCP, treat it as a versioned contract: capability negotiation, schema compatibility, transport auth and whose credentials act, per-tool timeouts, and server-side authorization at the execution boundary. The protocol decides how the model reaches a tool, never what it may do for the current user or tenant. The MCP specification states that tool descriptions are untrusted unless obtained from a trusted server, and that hosts must obtain explicit user consent before invoking a tool.

## Context window budgeting

Treat the context window as a fixed budget to allocate, not a container to fill. Partition it: policy prompt, tool definitions, retrieved context, history, scratchpad, output reserve. Tool definitions and schemas are permanent overhead on every call, so keep the tool count small and schemas narrow.

Prefer targeted retrieval and structured summaries over dumping documents. Long contexts degrade instruction following and recall silently: the model answers fluently while ignoring constraints earlier in the window.

Keep durable state outside the prompt and trim history by deterministic summarisation. Never use the context window as an authorization mechanism: text in the window is data, not a control the code enforces.

## Retrieval and memory

Define corpus ownership, ingestion permissions, source provenance, freshness, deletion propagation, chunking, embedding/model version, access filtering, ranking, citation, and reindex plan. Enforce authorization before retrieval and again before actions. Embeddings and caches can preserve sensitive data. Evaluate retrieval recall/precision, stale/conflicting sources, tenant isolation, and prompt injection. RAG is not a guarantee of factuality.

## Agent memory

Separate three kinds of memory, each with its own store, owner, and lifecycle:

- Working memory: current-run scratch state, discarded at run end, ephemeral and untrusted.
- Episodic memory: past trajectories in an append-only log, used for retrieval, analytics, and replay.
- Semantic memory: durable facts about a user or domain, with provenance, confidence, TTL, and a human correction path.

Decide who may write, what is rejected, and how a user sees, corrects, or deletes it. Memory is an untrusted write path: a poisoned memory becomes durable prompt injection that outlives the run that wrote it. Constrain writers, record provenance, and support revocation.

## Agent-specific threat model

Beyond direct prompt injection, cover:

- Confused deputy: bind every action to the initiating user's permissions, not to the agent's own identity or service credentials.
- Data exfiltration: allowlist egress, strip secret-bearing fields from connector responses and model output, and block unrequested writes.
- Indirect injection: tool output and stored content carry instructions, so writing attacker-controlled text into another system creates a delayed execution path there.
- RAG poisoning: control ingest authorization, provenance, and freshness, and monitor the corpus for unexpected content and drift.
- Memory poisoning: apply the memory write controls to every memory path.
- Sandboxing: code, shell, or browser execution the agent drives runs isolated, network-restricted, resource-capped, with no ambient credentials.

## Agent SLOs, cost, and autonomy

Objectives for the agent, not only the API: task success rate, time-to-completion percentiles, tool error rate, human escalation rate, unsafe action rate, and cost per successful task.

Cost per successful task, not per call, governs design. Track spend by user, tenant, and feature, and enforce per-tenant budgets, a daily ceiling, and a kill switch in code, not in a dashboard.

Reduce cost structurally: cache retrieval and tool results, route easy steps to a smaller model, cap context and fan-out.

State the autonomy level explicitly: read-only, suggest, act with approval, bounded autonomous, and name the condition that moves the system up or down a level.

## Evaluation and observability

Keep a versioned, privacy-reviewed evaluation set from representative tasks and adversarial cases. Measure task success, factual grounding, refusal behavior, tool correctness, latency, cost, safety incidents, and regressions. Use offline tests, shadow, limited canary, human review, and rollback gates as appropriate. Avoid treating a single benchmark or LLM judge as proof.

Trace model and tool calls with redaction; record model/prompt/tool versions, token counts, latency, retries, policy decisions, and outcome labels. Avoid storing raw prompts/outputs by default if they contain personal or confidential data. Set retention and access controls. Observe loops, repeated tool calls, queue age, spend spikes, and rate limits.

## Evaluation method

Score trajectories, not only final answers: right tool, right arguments, safe ordering of side effects, no redundant calls. An answer reached unsafely is not the same result as the same answer reached safely.

Output is non-deterministic, so run each case more than once and report a pass rate with variance.

If an LLM judges the output, validate the judge against human-labelled examples, pin the judge model and prompt version, prefer randomised pairwise comparison over absolute scoring, and measure human agreement rather than assume it.

## Multi-agent systems

Use multiple agents only when specialization, parallel independent work, or review materially improves outcomes. A coordinator needs bounded delegation, typed task inputs/outputs, budgets, timeouts, cancellation, shared-state ownership, conflict resolution, provenance, and final validation. Prevent duplicate side effects and runaway delegation. Do not treat agent agreement as independent evidence when agents share models, sources, or hidden context. Keep deterministic checks outside the model wherever possible.

## Multi-agent topologies

Name the topology, because each fails differently:

- Orchestrator-worker: fan-out multiplies cost; the supervisor becomes a bottleneck and a single point of judgement.
- Supervisor or hierarchical: depth adds latency at every level, and errors propagate silently as each level rationalizes its input.
- Peer debate: agents sharing a model and sources form an echo chamber, so agreement is not independent evidence.
- Pipeline: handoffs lose context and quality, and each stage's output becomes the next stage's unverified premise.

Define shared-state ownership, write-conflict resolution, and provenance for every exchanged artifact. Prefer plan-then-execute when the task decomposes predictably, and react only when the next step depends on a fresh observation. Require a no-progress check on the coordinator so a stalled worker is not retried indefinitely.

## Source caveat

Agent frameworks and provider features change quickly. Browse their current primary docs for APIs, limits, security behavior, pricing, model lifecycle, and orchestration semantics. Keep general principles above separate from framework-specific adapters.
