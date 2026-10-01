# AI and agent system architecture

AI features inherit distributed-systems failure modes and add probabilistic output, model/provider dependence, prompt/tool security, evaluation, and variable cost. Treat model calls as external services and agents as constrained application components, not trusted peers.

## Requirements and topology

Define tasks, users, autonomy level, harm/error tolerance, latency/cost budgets, grounding needs, freshness, privacy, human review, and escalation. Separate deterministic application logic from model inference. Choose direct model call, retrieval-augmented generation (RAG), workflow/state machine, bounded agent loop, or multi-agent orchestration only when task requirements justify the added uncertainty and cost.

For each workflow, specify state, step ownership, checkpoints, timeout/deadline, retry/idempotency, cancellation, pause/resume, human approval, compensation, audit, and terminal failure. Persist durable job state outside process memory. Make resumptions safe after worker restart and duplicated events.

## Model and tool boundaries

Treat model endpoints as rate-limited, variable-latency dependencies with changing versions and output. Set per-task token/cost/time limits, retry policy, concurrency cap, circuit/fallback behavior, provider outage strategy, and model-version recording. Use structured outputs with validation; an output schema does not establish truth or safety. Validate citations/claims when correctness depends on sources.

Give tools narrow capabilities and server-side authorization. Validate arguments and result sizes. Treat prompts, retrieved documents, files, webpages, tool output, and user input as untrusted; instruction-like content inside them must not grant authority. Prevent prompt injection from crossing data/tool trust boundaries. Do not pass secrets or unrestricted credentials into model context. Require approval for consequential or irreversible actions.

## Retrieval and memory

Define corpus ownership, ingestion permissions, source provenance, freshness, deletion propagation, chunking, embedding/model version, access filtering, ranking, citation, and reindex plan. Enforce authorization before retrieval and again before actions. Embeddings and caches can preserve sensitive data. Evaluate retrieval recall/precision, stale/conflicting sources, tenant isolation, and prompt injection. RAG is not a guarantee of factuality.

## Evaluation and observability

Keep a versioned, privacy-reviewed evaluation set from representative tasks and adversarial cases. Measure task success, factual grounding, refusal behavior, tool correctness, latency, cost, safety incidents, and regressions. Use offline tests, shadow, limited canary, human review, and rollback gates as appropriate. Avoid treating a single benchmark or LLM judge as proof.

Trace model and tool calls with redaction; record model/prompt/tool versions, token counts, latency, retries, policy decisions, and outcome labels. Avoid storing raw prompts/outputs by default if they contain personal or confidential data. Set retention and access controls. Observe loops, repeated tool calls, queue age, spend spikes, and rate limits.

## Multi-agent systems

Use multiple agents only when specialization, parallel independent work, or review materially improves outcomes. A coordinator needs bounded delegation, typed task inputs/outputs, budgets, timeouts, cancellation, shared-state ownership, conflict resolution, provenance, and final validation. Prevent duplicate side effects and runaway delegation. Do not treat agent agreement as independent evidence when agents share models, sources, or hidden context. Keep deterministic checks outside the model wherever possible.

## Source caveat

Agent frameworks and provider features change quickly. Browse their current primary docs for APIs, limits, security behavior, pricing, model lifecycle, and orchestration semantics. Keep general principles above separate from framework-specific adapters.
