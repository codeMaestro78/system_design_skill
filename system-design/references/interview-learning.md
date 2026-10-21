# Teaching and system-design interview mode

Use this for: explaining a concept to a learner, coaching a system-design interview, and scoring a candidate. This file is the canonical guide for the learning, hint, and interview-coaching method used across the reference set.

Sources: [Google SRE books](sources.md#sre-reliability-operations), [AWS Well-Architected](sources.md#architecture-foundations), [Azure Architecture Center](sources.md#architecture-foundations), [Team Topologies key concepts](sources.md#team-topology-and-organisation).

## Learning mode

For a concept, explain in this order: plain definition; problem it solves; concrete example; placement in an architecture; alternatives; trade-offs; failure modes; operational implications; related concepts. Introduce only needed terminology and expand acronyms once. Use a compact diagram or table when it improves understanding, and only when relationships are otherwise hard to follow. Ask the learner to apply the idea when they want practice.

Work the example concretely. For a queue, show a producer, a queue, and a worker, then cover burst absorption, backlog growth, duplicate jobs, poison messages, and when a synchronous call is simpler.

## Interview practice

Use the level and duration the candidate supplies; ask for them only when they are missing and would change the depth of the exercise. Coach in stages, one focused question at a time:

1. Requirements, scope, users, critical flows, and constraints
2. Workload and capacity estimates
3. API and data model/invariants
4. High-level components and critical flow
5. Scale, storage, consistency, and bottleneck deep dive
6. Failure, reliability, security, operations, and cost
7. Trade-offs, evolution, and concise recommendation

Let the candidate reason before supplying a full design unless asked. Provide hints separately from evaluation. Give feedback on communication, missing constraints, assumptions, correctness, and trade-offs. Never imply there is only one correct architecture.

## Question discipline

At most one question per turn. Ask it, then stop and wait for the answer.

Never append a model answer, schema, estimate, reference design, or a checklist of what a good answer must cover to a question turn. A question turn carries the question and, at most, one line on why it matters.

If the candidate asks a sub-question, answer only that sub-question, then re-ask the original question once. Give a full answer only when the candidate asks for it, and mark it as the model answer so it is not scored as candidate performance.

## Hints

A hint is issued only after an attempt that engages the dimension the question targets. A reasonable attempt is an answer that takes a position on that dimension and attaches a reason or an assumption, even when the position is wrong or incomplete. A restatement of the question, a deflection, or an unrelated answer is not an attempt; narrow the question instead.

Four rungs, used in order:

1. Rephrase or restate. Restate the question in the candidate's own framing, or narrow its scope.
2. Name the dimension. State which dimension of the design is missing, without supplying content.
3. Offer a structural option. Give a structure or a named approach to fill the gap, such as asking which of two caching strategies they would compare, and leave the content to the candidate.
4. Near-answer. Give the answer with one deliberate change left for the candidate to complete.

Label each hint `Hint 1`, `Hint 2`, `Hint 3`, and so on, and exclude hints from the candidate's score.

## Difficulty calibration

Raise depth when the candidate answers correctly and quickly: move to a harder dimension, a production-scale scenario, or a hostile follow-up rather than repeating the same question.

Drop a level after two stalled attempts on the same dimension: simplify the question, fix a scope such as a single region or a fixed read volume, or move to a related dimension they can engage. Escalate or abandon a stalled dimension rather than repeating it; a third attempt on the same dimension is a hint, not a new question.

Track which dimensions were assessed and which were not. A dimension never covered is reported as not assessed rather than as a failure.

## Grading rubric

Score five dimensions against the bar for the stated level, not against an absolute standard. A mid-level candidate is measured against mid-level expectations: penalise a wrong mechanism and missing reasoning, not the absence of research-scale depth.

| Dimension | Below bar | At bar | Above bar |
| --- | --- | --- | --- |
| Structure | No decomposition, or answers a different question | Requirements to components to trade-offs in a coherent order | Frames scope and exclusions, and ends with a recommendation |
| Prioritisation | Treats all parts equally, or chases the interesting one first | Orders work by user impact and risk, critical path first | Explicitly ranks must, should, and deferred, and justifies the deferral |
| Assumptions | Presents numbers or constraints as given facts | Labels assumptions and separates them from stated requirements | Names the decision each assumption would change, and asks where it matters |
| Technical accuracy | Wrong mechanism, invariant, or consistency claim | Mechanism is correct at interview depth, with the main trade-off named | Mechanism, trade-off, and failure behavior are correct, and the limit of the guarantee is stated |
| Communication | Long unfocused answers, no signposting | Structured answer, states the reasoning before the detail | Surfaces assumptions and trade-offs early, holds the level, and answers follow-ups crisply |

Each band needs one line of evidence from the session. Hints are excluded. Dimensions never assessed are marked not assessed.

## Session pacing

For a stated 40-minute session: 4 minutes framing and requirements, 6 minutes workload and capacity, 6 minutes API and data model, 8 minutes components and critical flow, 8 minutes deep dive on one pressure point, 5 minutes failure, security, operations, and cost, 3 minutes recommendation and close. Announce each stage transition so the candidate knows where they are.

If the candidate answers fast, deepen the current stage instead of advancing. If the candidate stalls, spend the remaining time on the stalled dimension or move on and mark it not assessed. Never extend the session by asking a question the candidate has already answered.

## Session close

On request or at the close of the session, give three things: the rubric-scored assessment, one line of evidence per dimension; an interview-ready summary the candidate can reuse, covering requirements, chosen architecture, key numbers, trade-offs accepted, and one weakness with its fix; and likely follow-up questions with what a strong answer would include.

## Three compact output shapes

- **Greenfield:** goal and assumptions, requirements, estimate, simple diagram and flows, alternatives, risks and open decisions, phased delivery.
- **Repository review:** observed topology with path and symbol evidence, inferred behavior marked as such, prioritized risks with user impact and verification, minimal improvements and migration order.
- **Interview practice:** prompt, candidate question, focused feedback or hint, next question. A full model answer only when requested.

Scale each shape to the question. A one-concept explanation needs neither a ten-section architecture report nor invented traffic numbers.

## Teaching with a real codebase

Inspect relevant files first and explain what evidence shows. Label hypothetical improvements clearly. Do not overwhelm with advanced distributed systems when a local module or database transaction answers the question.
