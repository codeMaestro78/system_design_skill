<!-- Use when a production incident has been resolved and the record must capture symptom, timeline, hypotheses, contributing conditions, and corrective work without blame. -->

# Incident report: <short title>

Incident ID: <identifier>
Severity: SEV1 | SEV2 | SEV3 | SEV4
Status: Resolved | Monitoring | Closed
Started: YYYY-MM-DD HH:MM UTC
Detected by: <monitoring, user report, or internal notice>
Mitigated: YYYY-MM-DD HH:MM UTC
Fully resolved: YYYY-MM-DD HH:MM UTC
Duration: <hours and minutes>
Incident commander: <role or name>
Scribe: <role or name>
Services affected: <components, and the blast radius>
Data impact: <records, requests, or users affected, and whether data was lost or corrupted>

## 1. User-visible symptom

What a user experienced, in their terms, before any internal analysis.

> <the symptom as a user described it>

| Aspect | Detail |
|---|---|
| What the user saw | |
| Scope | <percent of requests, all users, one tenant, one region> |
| First observed | <timestamp, and the source of that observation> |
| Last observed | <timestamp, and the evidence it stopped> |
| Workaround used | <what users did to work around it, if any> |

## 2. Timeline

One row per meaningful event. Times in UTC. Include detection, decision, action, and verification events, not only failures.

| Time (UTC) | Event | Evidence | Actor or system |
|---|---|---|---|
| | | | |
| | | | |

Durations that matter: time to detect, time to acknowledge, time to contain, time to mitigate, time to resolve.

| Interval | Duration | Why it mattered |
|---|---|---|
| Detection to acknowledgement | | |
| Acknowledgement to containment | | |
| Containment to resolution | | |

## 3. Impact

| Dimension | Measured | Source | Notes |
|---|---|---|---|
| Requests failed | | | |
| Users affected | | | |
| Downtime by service | | | |
| Error budget consumed | <percentage of the window budget> | | |
| Data lost | | | |
| Data corrupted | | | |
| Downstream or dependent services affected | | | |
| Cost impact | | | |
| SLA or SLO breach | | | |

## 4. Containment and recovery

What was done to stop the impact, and what it cost.

| Action | Time | Effect | Side effect or risk | Reversible | Who decided |
|---|---|---|---|---|---|
| | | | | | |

| Action | Time | Effect | How recovery was verified |
|---|---|---|---|
| | | | |

Distinguish containment (the bleeding stopped) from recovery (the system is healthy and verified). State what was still degraded after containment.

## 5. Root cause analysis

Hypotheses were ranked and tested, not assumed. Each hypothesis is falsifiable and carries the evidence that moved it.

| Rank | Hypothesis | Test performed | Result | Confidence | Conclusion |
|---|---|---|---|---|---|
| 1 | | | | High/Medium/Low | Confirmed / Rejected / Inconclusive |
| 2 | | | | | |
| 3 | | | | | |

| Rank | Contributing condition | Category | Evidence | Owner | Status |
|---|---|---|---|---|---|
| 1 | | Technical / Process / Design / Communication | | | Open/Accepted/Closed |
| 2 | | | | | |

Root cause statement: <the mechanism that produced the failure, in two or three sentences, supported by the evidence above>

## 6. What went well

- <mechanism or practice that limited impact or sped recovery>

## 7. What did not go well

- <gap that increased detection time, blast radius, or recovery time, described as a system condition rather than a person>

## 8. Where we got lucky

- <condition that could have made the outcome worse, and the cheap change that would have prevented it>

## 9. Corrective actions

Every action has an owner, a date, and a verification method. An action without a date is a wish.

| ID | Action | Type | Owner | Due | Priority | Verification | Status |
|---|---|---|---|---|---|---|---|
| CA-1 | | Prevention/Detection/Mitigation | | YYYY-MM-DD | P0/P1/P2 | <how it will be proven> | Open/In progress/Done |
| CA-2 | | | | | | | |

| ID | Action | Type | Owner | Due | Priority | Verification | Status |
|---|---|---|---|---|---|---|---|
| CA-3 | | | | | | | | |

## 10. Follow-up on actions

| ID | Committed date | Revised date | Reason for the change | Verified on | Evidence link |
|---|---|---|---|---|---|
| | | | | | |

## Before you deliver

- The user-visible symptom and the scope of impact come before any internal analysis, and impact figures cite a measurement source.
- No invented numbers. Every duration, count, and percentage carries units and a source, or is labelled as an estimate with the reasoning.
- The timeline covers detection, decision, action, and verification, in UTC, with evidence for each entry.
- Every hypothesis in the ranked list names the test that was run and the result, including the ones that were rejected.
- Contributing conditions describe system state, not individuals. No names are attached to mistakes.
- Every corrective action has an owner, a date, and a verification method, and a revised date is explained if it changes.
- Detection gaps are addressed explicitly, so the next occurrence is caught earlier rather than reported by a user.
- Restore and rollback are drills with an owner and a date, not intentions.
