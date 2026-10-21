<!-- Use when reliability must be a number with a window, and release risk must be tied to a budget rather than to uptime history. -->

# SLIs, SLOs, and error budget: <service or journey>

Owner: <role accountable for the SLOs>
Last reviewed: YYYY-MM-DD
Measurement source: <the query, dashboard, or service that produces each SLI>

## 1. Scope

Service or journey: <what this covers>
Critical user journeys: <the journeys whose failure is user-visible>
Out of scope: <what is not covered here, and where it is covered>
Users of the objective: <who consumes these numbers, for what decision>

## 2. Service level indicators

An SLI is a measured quantity, not a target. Write the exact computation.

| SLI ID | User journey | Indicator | Definition and computation | Unit | Window | Measurement source |
|---|---|---|---|---|---|---|
| SLI-1 | | | <numerator> / <denominator> | % | <rolling window> | <query or dashboard> |
| SLI-2 | | | | | | |
| SLI-3 | | | | | | |

Include separate indicators for: successful and valid requests, latency, freshness, correctness or completion, and asynchronous job completion, where the design has them. State which indicators are derived from a proxy signal and which are direct.

## 3. Objectives

| Objective | Type | SLI | Target | Window | Basis for the target | Consequence of missing it |
|---|---|---|---|---|---|---|
| SLO-1 | Internal SLO | SLI-1 | <e.g. 99.5%> | <e.g. 28 days> | <derived from the error budget below, or from a stated user need> | <what the team does> |
| SLO-2 | | | | | | |
| SLO-3 | | | | | | |

Type is one of: internal SLO, contractual SLA, regulatory obligation, or provisional assumption. Mark provisional targets explicitly and record who sets the real one.

Availability arithmetic, stated once: <e.g. 99.9% over 28 days leaves 43.2 minutes of unavailability budget, including planned work>

## 4. Error budget

| Objective | Budget per window | Consumption source | Current consumption | Remaining | Policy |
|---|---|---|---|---|---|
| SLO-1 | <minutes or error count per window> | <which alert or SLI consumes it> | <measured> | <remaining> | <what happens at 50%, 100%> |

Policy at partial consumption: <what changes at 50%, for example "reliability work is scheduled ahead of feature work">
Policy at exhaustion: <what happens at 100%, for example "feature releases pause, only reliability and security changes ship, the exception process is named>

## 5. Alert conditions

Alert on symptoms users feel, not on causes. Each condition names the threshold, the window, and the response.

| Alert | Symptom | Condition | Window | Severity | Response | Runbook |
|---|---|---|---|---|---|---|
| A-1 | <user-visible symptom> | <SLI threshold> | | Page/Page+ticket/Ticket | <first action> | [runbook.md](runbook.md) |
| A-2 | | | | | | |

Also record the non-paging signals an operator watches: <queue age, replica lag, saturation, error mix, cost>.

## 6. Data quality and measurement gaps

| SLI | Known gap | Effect on the number | Mitigation | Owner |
|---|---|---|---|---|
| | | | | |

State what the current telemetry cannot measure. A target that cannot be measured is not an SLO.

## 7. Objective review

| Review cadence | Who attends | What is checked | Changes made |
|---|---|---|---|
| | | <SLIs still match user needs, budget consumption, missing indicators> | |

Adjust the target when the user need changes, and record the change with its date and reason. Do not silently move a target after a miss.

## Before you deliver

- Every SLI has an explicit computation, a unit, and a window. "Uptime" is not an SLI until it is defined.
- No invented numbers. Every target has a basis: a user need, a contractual obligation, a stated assumption with an owner, or an error budget arithmetic that is shown.
- Every number carries units and a source, and the target is labelled as SLO, SLA, obligation, or assumption.
- Every component in the measurement path maps to a requirement, a constraint, or a named risk reduction, and unmeasured components are listed in section 6.
- Alerts map to a user-visible symptom and to a runbook that exists.
- Restore and rollback are drills with an owner and a date, not intentions.
