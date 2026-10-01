# AI and agent systems

Use when a workflow calls models, retrieval, or tools. General distributed-system principles still apply; SDK-specific mechanics require current vendor documentation. Sources: [OWASP LLM risks](sources.md#ai-and-agent-systems), [OpenAI agent guidance](sources.md#ai-and-agent-systems), [NIST AI RMF](sources.md#ai-and-agent-systems).

## Bound the workflow

Treat model and tool calls as unreliable remote calls: set timeouts, bounded retries, rate/token/cost budgets, cancellation, fallback and provider-outage behavior. Persist run and step state for long work; use stable step IDs and idempotency keys for side effects. Define checkpoint and resume semantics, including what happens if a tool succeeded before the process crashed. Keep an audit trail for decisions and actions, with sensitive content redacted.

## Keep authority in code

Prompts, retrieved documents, web pages and tool results are untrusted content. They can contain prompt injection. Retrieval or a guardrail model cannot prove safety. Grant tools only the permissions needed; validate arguments and authorize each real action at the execution boundary. Require explicit human approval for high-impact or irreversible operations according to the actual risk. Approval text inside a prompt is not an enforcement mechanism.

## Make quality observable

Record model, prompt, tool and index versions; evaluate representative tasks for correctness, safety, latency and cost before and after changes. Trace model/tool steps with privacy controls. For retrieval, enforce document access, freshness, provenance and citation checks; stale embeddings or an out-of-date index can make a plausible answer wrong. Specify how humans correct failures and how the system reconciles partially completed actions.

Vendor features such as built-in guardrails, durable checkpoints or approval APIs are implementation options. Verify their exact scope and current behavior before claiming an end-to-end guarantee.
