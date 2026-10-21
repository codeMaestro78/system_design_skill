# Model serving and inference infrastructure

Use this for: the inference tier itself, its latency and cost structure, and rollout of model or serving changes. Agent-level design is covered in [AI and agent system architecture](ai-systems.md). Sources: [OWASP LLM risks](sources.md#ai-and-agent-systems), [NIST AI Risk Management Framework](sources.md#ai-and-agent-systems), [Google SRE on non-abstract design](sources.md#sre-reliability-operations), [AWS Builders' Library](sources.md#first-party-engineering-case-studies).

## Inference is a separate tier

A model server owns weights, tokenizer, batching scheduler, key-value cache, and accelerator memory, and it fails differently from the application tier: it saturates on token throughput, degrades in latency rather than in error rate, and a configuration change can alter outputs without changing code. Give it its own SLOs, dashboards, capacity model, and on-call rotation, and treat it as an external dependency with bounded timeouts, concurrency, cancellation, and an evaluated fallback.

## Latency decomposition

| Metric | What it measures | Dominated by | Who feels it |
| --- | --- | --- | --- |
| Time to first token | how long until the user sees anything | queue wait plus prefill | perceived responsiveness |
| Inter-token latency | spacing between generated tokens | decode step time, which grows with batch size | stream smoothness |
| Total latency | queue wait plus prefill plus every decode step | all of the above plus output length | completion time and cost |

Prefill is compute bound and processes prompt tokens in parallel, so a long prompt costs a large one-off term. Decode is memory bandwidth bound and runs one token at a time per sequence, so decode speed is shared across the batch and each added sequence slows the others. The SLOs differ for that reason: time to first token governs whether the feature feels alive, inter-token latency governs whether it feels stuck, and total latency governs capacity and cost. Monitor all three, per model and per task class, against the output length distribution.

```text
total_latency = queue_wait + prefill_time + output_tokens * decode_step_time
prefill_time  = prompt_tokens / prefill_rate
decode_step_time = decode_rate at the current batch size

Illustrative arithmetic with assumed inputs, not measured rates:
prompt 2000 tokens at an assumed 8000 tokens/s prefill  -> 0.25 s prefill
output 200 tokens at an assumed 60 tokens/s decode     -> about 3.3 s decode
total about 3.6 s plus queue wait, with time to first token near 0.25 s plus queue wait
```

## Batching trades latency for throughput

The scheduler groups sequences into a batch so the accelerator amortizes weight reads across them. A larger batch raises aggregate token throughput and per-request decode time, and the queue wait grows once the batch slots are full. Continuous batching admits a new sequence as one finishes, which keeps utilization high under variable load; fixed-window batching waits to fill a window and delays the first request in it; chunked prefill splits a large prefill so long prompts do not stall other decodes. Choose the concurrency limit from the latency budget, not from accelerator memory alone, and measure under realistic concurrency and a realistic mix of prompt and output lengths.

## Quantization changes quality, latency, and memory

Reducing weight precision lowers the bytes read per decode step, which lowers decode time and lets more models or sequences fit in the same accelerator memory. The cost is a change in output distribution: accuracy on reasoning and structured-output tasks can move either way, refusal and format adherence can shift, and thresholds tuned for the full-precision build no longer hold. Measure on the eval set, keep the quantized build as its own model version, and re-baseline every gate. Quantization is a model change, not a deployment detail.

## Key-value cache and prefix reuse

The key-value cache holds attention state per sequence, so its memory grows with context length and bounds concurrency. Reusing the cache for a shared prefix, such as a system prompt, a tool set, or retrieved documents, removes the prefill cost for that prefix and lowers time to first token, but only when the prefix is byte-identical; a partial match silently produces a different prompt from the measured one.

The cache is a security boundary. Cached state contains the literal prompt content, including private context, and a cache keyed only by model version and prefix hash can serve one user's context to another. Key the cache by the authorization scope of the content, partition it by tenant, treat entries as sensitive data under the same controls as the source, and clear a tenant's entries at offboarding. Log cache hits as a fact about the request, because a hit also means the source was not re-read.

## Routing, tiers, and fallbacks

Route by task class, prompt size, latency requirement, and cost budget across model tiers, and route failures to a fallback tier. A cascade that tries a cheap model first and escalates on low confidence has a worst-case latency and cost equal to the sum of both stages, so bound the escalation and trigger it on a measurable, non-protected signal. Every fallback path produces a different output distribution, so evaluate each separately. Keep the router deterministic and logged, and let its failure degrade to a fixed default.

## Deprecation and migration

Model versions are deprecated on a schedule the design does not control, and self-hosted weights age out. Record the exact model identifier and version for every request so a regression can be attributed. Keep the previous version warm for a defined window and route to it as the rollback path, and give long-running work, such as an agent run that captured a model at step one, an explicit policy: finish on the version it started with, or migrate at a checkpoint with re-validation. Treat the deadline as a migration milestone with an owner.

## Accelerator economics

Idle accelerator time is pure cost, so measure utilization first: busy time over provisioned time, per accelerator and model. Capacity and cost then trade three ways. A warm pool holds accelerators ready and pays for the idle ones. Scale-to-zero removes the idle cost and pays a cold start, where weights must be loaded and moved, which suits only traffic that tolerates that delay. A dedicated accelerator gives a capacity guarantee, stable latency, and instance-type control, and costs money while idle; a serverless accelerator scales to zero and bills for active time, and adds cold starts, quotas, and restricted instance types.

```text
cost_per_million_tokens = accelerator_hourly_cost * hours / (tokens_per_hour / 1e6)

Illustrative example with assumed inputs, not vendor pricing:
40 tokens/s decode at batch 8 -> about 115M tokens/hour for that accelerator
at an assumed hourly cost C, cost per million tokens = C / 115
```

The break-even point is a property of cold-start time, hourly cost, and the average request, so compute it rather than assuming the managed default is cheaper.

## Versioning and reproduction

Record the model identifier and version, tokenizer, quantization, adapter or fine-tune version, system prompt version, sampling parameters including seed, safety settings, tool and retrieval versions, cache-hit flag, and the request identifier. A seed plus deterministic settings improves repeatability, but batching, hardware differences, and server-side changes prevent bitwise reproduction, so treat a replay as a re-run. Apply the same redaction and retention rules to prompts, outputs, and traces as to any other personal data; see [security and privacy](security-privacy.md).

## Serving strategies

| Strategy | Latency shape | Cost shape | Operational burden | Use when |
| --- | --- | --- | --- | --- |
| Hosted managed API | variable, provider controlled | per token, no idle cost | lowest | low volume, no latency floor |
| Self-hosted single replica | predictable, no batching benefit | fixed idle cost | full | steady traffic, data residency, cost amortization |
| Self-hosted autoscaled with continuous batching | best throughput per accelerator, degrades under load | scales with demand | high | sustained high volume |
| Serverless accelerator | cold start on scale from zero | pay per active second | medium, quotas, cold starts | spiky or batch-like traffic |
| Asynchronous batch mode | seconds to hours | lowest per token | medium | embedding, classification, offline evaluation |
| On-device or edge inference | no network, bounded model size | no server cost | update complexity | privacy, offline use, tiny models |

## Rollout and shadowing

Roll out a model or serving change by shadowing first: send a fraction of live requests to the candidate, discard its output, and compare quality, latency, and cost. Shadowing doubles the inference cost of the shadowed fraction and copies live user content to the candidate, so it needs the same consent review as production traffic. Then canary: serve a small fraction of real traffic with a rollback that is a routing change, automatic stop conditions on error rate, latency, cost, and evaluation thresholds, and a human-reviewed sample. Gate every stage on an evaluation re-run for the candidate build, and never let a quality regression be discovered by users.
