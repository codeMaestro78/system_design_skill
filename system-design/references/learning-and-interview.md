# Learning and interview mode

First pass for explaining a concept and coaching a system-design interview. The canonical guide holds the stage ladder, hint ladder, rubric, and pacing: [interview and teaching mode](interview-learning.md).

## Explain a concept

Plain definition, the problem it solves, a tiny concrete example, where it fits in a system, trade-offs and failure modes, then related concepts. Define acronyms on first use. Use a diagram only when relationships are otherwise hard to follow. For a queue, show a producer, a queue, and a worker, and cover burst absorption, backlog growth, duplicate jobs, poison messages, and when a synchronous call is simpler.

## Coach an interview

Use the level and duration the candidate supplies and ask for them only when missing. Present the design prompt, then ask one focused question per turn and wait for the answer. Never append a model answer, schema, estimate, or reference design to a question turn; if the candidate asks a sub-question, answer only that sub-question.

Give a hint only after an attempt that engages the dimension, and label it `Hint 1`, `Hint 2`, and so on so it is not scored as the candidate's work. Rungs, in order: rephrase or restate, name the missed dimension, offer a structural option, give the near-answer. Raise depth when the candidate answers correctly and quickly, drop a level after two stalled attempts on the same dimension, and escalate or abandon a stalled dimension rather than repeating it.

Evaluate structure, prioritisation, assumptions, technical accuracy, and communication against the stated level. On request, give the scored assessment, an interview-ready summary, and likely follow-ups.

## Three compact output shapes

- **Greenfield:** goal and assumptions, requirements, estimate, diagram and flows, alternatives, risks and open decisions, phased delivery.
- **Repository review:** observed topology with path and symbol evidence, inferred behavior marked as such, prioritized risks with user impact, minimal improvements and migration order.
- **Interview practice:** prompt, candidate question, focused feedback or hint, next question. A full model answer only when requested.

Scale each shape to the question. A one-concept explanation needs neither a ten-section architecture report nor invented traffic numbers.
