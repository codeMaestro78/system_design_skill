# AI and agent systems

Use this for: a fast pass on an AI feature or agent workflow before the full architecture review.

Sources: [OWASP LLM risks](sources.md#ai-and-agent-systems), [OpenAI agent guidance](sources.md#ai-and-agent-systems), [NIST AI RMF](sources.md#ai-and-agent-systems).

**Canonical guide:** [AI and agent system architecture](ai-systems.md). That file is the source of truth for loop control, tool contracts, retrieval and memory design, evaluation, and multi-agent topology; this page is only a first pass.

## Decision rules

- **Tools stay narrow.** One verb per tool, typed parameters, bounded results. Authorization happens in code at the execution boundary, never in the prompt and never in the transport credentials of the tool server.
- **Actions run as the user, not as the agent.** Bind every action to the initiating user's permissions, never to the agent's own identity or service credentials. Allowlist egress, strip secret-bearing fields from connector responses and model output, and block unrequested writes.
- **Everything from the world is untrusted.** Prompts, retrieved documents, web pages, files, tool output, and stored memory are data. Instruction-like text inside them grants no authority.
- **Retrieval is authorized twice.** Enforce access filtering and authorization before retrieval and again before the action. RAG is not a guarantee of factuality, and an injected document is a delayed execution path.
- **Memory and execution are attack surfaces.** Keep working, episodic, and semantic memory in separate stores with provenance, revocation, and a human correction path, because a poisoned memory outlives the run that wrote it. Run any code, shell, or browser execution the agent drives isolated, network-restricted, and resource-capped, with no ambient credentials.
- **Irreversible actions need a human.** Require explicit approval for consequential operations. Approval text inside a prompt is content, not a control.
- **The loop is bounded.** Independent caps on steps, tokens, wall-clock, tool errors, and spend. Termination is success, give-up (cap exceeded or no progress), or abort (unsafe or unauthorized); a tripped cap escalates with the partial result instead of stopping silently.
- **Tools return actionable errors.** Stable code, short message, and a retryable flag, never a stack trace and never a failure the model can read as success. Side-effecting tools take a caller-supplied idempotency key scoped to tenant and operation and reject reuse with a different payload.
- **Context is a budget.** Allocate the window across policy, tool schemas, retrieved context, history, scratchpad, and output reserve. Never rely on the window for authorization.
- **Cost and autonomy are explicit.** Cost per successful task governs design, with per-tenant budgets, a daily ceiling, and a kill switch enforced in code. The autonomy level (read-only, suggest, act with approval, bounded autonomous) is stated rather than implied, together with the condition that moves it up or down.
- **Trajectories are scored.** Right tool, right arguments, safe order, no redundant calls, and every case run more than once with a pass rate. A single benchmark or LLM judge is not proof.
- **Multi-agent only when it pays.** Name the topology and cap delegation. Keep deterministic checks outside the model wherever possible, and prevent duplicate side effects and runaway delegation. Agents that share a model and sources make agreement weak evidence.

Vendor features such as built-in guardrails, durable checkpoints, or approval APIs are implementation options. Verify their exact scope and current behavior before claiming an end-to-end guarantee.

## Where to go next

- Full loop control, tool contracts, retrieval, memory, and evaluation: [AI and agent system architecture](ai-systems.md).
- Tenancy, authorization, and secret boundaries: [security, privacy, and threat modeling](security-privacy.md).
- Hosting, scaling, and cost of the model call: [model serving](model-serving.md).
