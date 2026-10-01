# Sample: one-clinic booking system (small-clinic scenario)

> Sample output produced with the `system-design` skill for the `small-clinic` eval case in `evals/cases.json`. Saved as an illustration of answer shape and reasoning, not as a claim of measured improvement. See `evals/README.md` for how to reproduce and score behavior cases.

**Prompt:** Design appointment booking for one clinic with two developers, one location, about 300 appointments per day, and an existing relational database. Receptionists and patients can book or cancel. Avoid double booking. The team can operate one web service and database. Recommend an initial architecture and explain when you would change it.

---

## 1. Facts, assumptions, unknowns

**Facts (from prompt):** one location, ~300 appointments/day, 2 developers, can operate 1 web service + 1 DB, must prevent double booking, book/cancel by receptionists and patients.

**Assumptions (reversible, would confirm):** existing DB is PostgreSQL (adapt below if MySQL); appointments are provider-scoped, fixed-duration slots (e.g., 15–30 min) with possible variable follow-ups; clinic open ~10 h/day; patients book own appointments only; no multi-region or insurance-billing scope in v1.

**Unknowns that would change material decisions:** exact RDBMS version, auth system, reminder/notification needs, no-show/cancellation policy, retention/regulatory jurisdiction for health data. I proceed without inventing traffic or SLO targets.

## 2. Requirements

**Must:** book/cancel without overlapping bookings for the same provider; receptionist can manage any patient, patient only own; durable record; minimal ops.

**Should:** prevent double-click duplicates, show availability quickly, audit who changed what.

**Could:** waitlist, reminders, reporting.

**Out of scope v1:** multi-clinic, online payments, analytics pipeline, active-active HA.

Workload shape, not just average: 300/day over 10 h = 30/h avg (~0.008 writes/s). Peak 10x (morning rush + reminders) still <1 write/s; reads 5–10x writes. Storage: 300 rows/day × 365 × 5 years ≈ 550k rows — trivial (<100 MB with indexes). No cache, queue, or second service is justified by load.

## 3. Recommendation: modular monolith

One deployable web service (e.g., Node/Python) + existing relational DB. Modules: scheduling, availability, notifications-stub, admin. No microservices, no Kafka, no Redis in v1 — each would add deployment, monitoring, and failure modes a 2-person team cannot afford at <1 rps.

```mermaid
flowchart LR
  Patient[Patient / Receptionist browser] -->|HTTPS| App[Single web service<br/>scheduling + authz + validation]
  App -->|SQL + constraint| DB[(Relational DB<br/>source of truth)]
```

When to change (measurable triggers): add async reminders/queue only when notification retries block requests or no-show rate justifies it; add read replica/cache only with sustained p95 > target on availability reads; split services only with a second team/ownership boundary or conflicting deploy cadence — not a request-rate threshold alone.

## 4. Data and the double-booking invariant

Owner: `appointments` table owns the invariant “no two booked appointments for the same provider overlap.”

```sql
-- PostgreSQL example; adapt if MySQL (see below)
CREATE TABLE appointments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_id uuid NOT NULL,
  patient_id uuid NOT NULL,
  during tstzrange NOT NULL,
  status text NOT NULL CHECK (status IN ('booked','cancelled','completed')),
  idempotency_key text UNIQUE,
  created_by uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE appointments ADD CONSTRAINT no_overlap
  EXCLUDE USING gist (provider_id WITH =, during WITH &&)
  WHERE (status = 'booked');
```

Why this works — including empty schedules: the database checks the exclusion constraint atomically at insert/commit across concurrent transactions. Two concurrent `INSERT`s for overlapping `during` cannot both commit; one gets `23P01` and the app returns `409 Conflict`. This holds when no conflicting row existed beforehand, unlike `SELECT → INSERT` in `READ COMMITTED`, where both reads see “free” then both insert. Do not rely on in-process locks: with two processes/containers or a restart they diverge.

If the existing DB is MySQL/InnoDB (no exclusion constraints): pre-create fixed `slots(provider_id, starts_at UNIQUE)` and book with `INSERT ... ON DUPLICATE KEY` or `UPDATE slots SET status='booked' WHERE status='free'` and check affected-rows = 1. Same principle — one atomic writer check.

Idempotency (double-click/retry ≠ double booking): client sends `Idempotency-Key`; unique column returns the original booking on retry instead of inserting again. Cancellation is `UPDATE ... WHERE id=? AND status='booked'`; freed time becomes bookable; keep cancelled rows for audit.

## 5. Critical flows

Book: `POST /appointments {provider, start, duration, Idempotency-Key}` → authz → validate window → single `INSERT` → on `23P01` return 409 with next-available suggestions → on success return booking. Timeout does not mean “not booked” — client retries with the same key and the server returns the existing row.

Cancel: `POST /appointments/:id/cancel` → authz (owner or receptionist) → conditional update. Race between two cancels is safe; race between cancel + rebook resolves by transaction order.

## 6. Failure, security, operations (minimal but explicit)

DB is the failure domain. Backups: nightly `pg_dump` + WAL archiving for point-in-time recovery; quarterly restore drill to a scratch host; document RTO/RPO after one drill. Observability: log booking attempts with provider/time/result; alert on 5xx rate and DB unavailability; track 409 rate (spike = UX or scraping issue), p95 booking latency, backup age. Runbook: “booking 500s” → check DB, queue-free deploy rollback, manual overlap query provided.

Trust boundaries: patient sees only own bookings; receptionist role checked in server code per request (never trust client tenant/role claim); audit `created_by/cancelled_by`; encrypt in transit, encrypt at rest via managed disk/DB; retention/deletion policy confirmed with clinic before storing health-adjacent notes.

## 7. Trade-offs accepted

Monolith couples deploys but removes network partitions, dual-write, and cache-invalidation failures. Constraint-based correctness costs a Postgres-specific DDL (or slot-table discipline on MySQL) and requires clients to handle 409s — cheaper than operating a lock service or queue for 300/day.

*Evidence that would change this answer: different RDBMS, requirement for cross-clinic scheduling, or a hard reminder-delivery SLA that forces async workers.*
