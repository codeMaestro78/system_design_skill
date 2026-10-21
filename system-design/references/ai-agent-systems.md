# AI and agent systems

First pass for a workflow that calls models, retrieval, or tools. The canonical guide holds the reasoning and the mechanisms: [AI and agent system architecture](ai-systems.md). Sources: [OWASP LLM risks](sources.md#ai-and-agent-systems), [OpenAI agent guidance](sources.md#ai-and-agent-systems), [NIST AI RMF](sources.md#ai-and-agent-systems).

## Decision rules

- **Tools stay narrow.** One verb per tool, typed parameters, bounded results. Authorization happens in code at the execution boundary, never in the prompt and never in the transport credentials of the tool server.
- **Everything from the world is untrusted.** Prompts, retrieved documents, web pages, files, tool output, and stored memory are data. Instruction-like text inside them grants no authority.
- **Irreversible actions need a human.** Require explicit approval for consequential operations. Approval text inside a prompt is content, not a control.
- **The loop is bounded.** Independent caps on steps, tokens, wall-clock, tool errors, and spend. A tripped cap escalates with the partial result instead of stopping silently.
- **Context is a budget.** Allocate the window across policy, tool schemas, retrieved context, history, and output reserve. Never rely on the window for authorization.
- **Cost and autonomy are explicit.** Cost per successful task governs design, and the autonomy level (read-only, suggest, act with approval, bounded autonomous) is stated rather than implied.
- **Trajectories are scored.** Right tool, right arguments, safe order, no redundant calls, and every case run more than once with a pass rate.
- **Multi-agent only when it pays.** Name the topology and cap delegation. Agents that share a model and sources make agreement weak evidence.

Vendor features such as built-in guardrails, durable checkpoints, or approval APIs are implementation options. Verify their exact scope and current behavior before claiming an end-to-end guarantee.
