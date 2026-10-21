# Sample: one-clinic booking system (small-clinic scenario)

> Sample output produced with the `system-design` skill for the `small-clinic` eval case in `evals/cases.json`. Saved as an illustration of answer shape and reasoning, not as a claim of measured improvement. See `evals/README.md` for how to reproduce and score behavior cases.

**Prompt:** Design appointment booking for one clinic with two developers, one location, about 300 appointments per day, and an existing relational database. Receptionists and patients can book or cancel. Avoid double booking. The team can operate one web service and database. Recommend an initial architecture and explain when you would change it.

---

## 1. Facts, assumptions, unknowns

**Facts (from prompt):** one location, ~300 appointments/day, 2 developers, can operate 1 web service + 1 DB, must prevent double booking, book/cancel by receptionists and patients.

**Assumptions (reversible, would confirm):** existing DB is PostgreSQL (adapt below if MySQL); appointments are provider-scoped, fixed-duration slots (e.g., 15–30 min) with possible variable follow-ups; clinic open ~10 h/day; patients book own appointments only; no multi-region or insurance-billing scope in v1.

**Unknowns that would change material decisions:** exact RDBMS version, auth system, reminder/notification needs, no-show/cancellation policy, retention/regulatory jurisdiction for health data. I proceed without inventing traffic or SLO targets; every workload number below is either arithmetic derived from the stated 300/day or an assumption labelled as such.

## 2. Requirements

**Must:** book/cancel without overlapping bookings for the same provider; receptionist can manage any patient, patient only own; durable record; minimal ops.

**Should:** prevent double-click duplicates, show availability quickly, audit who changed what.

**Could:** waitlist, reminders, reporting.

**Out of scope v1:** multi-clinic, online payments, analytics pipeline, active-active HA.

Workload shape, not just average: 300/day over 10 h = 30/h avg. Write rate is 0.0035 writes/s over 24 h (300/86,400) and 0.008 writes/s averaged over the ~10 h the clinic is open (300/36,000). A 10x peak factor (assumed: morning rush plus reminder sends) still lands under 1 write/s; read volume of 5–10x writes is also an assumption, not a measurement. Storage: 300 rows/day × 365 × 5 years ≈ 550k rows, ~190 MB with indexes (~200 MB once idempotency keys are populated) — trivial at this size. Audit rows recording `created_by`, `cancelled_by`, and status changes are additional and are not counted here. No cache, queue, or second service is justified by load.

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
-- btree_gist supplies the GiST operator class for uuid; it is a trusted extension, so a
-- non-superuser holding CREATE on the database can install it.
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE TABLE appointments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_id uuid NOT NULL,
  patient_id uuid NOT NULL,
  during tstzrange NOT NULL,
  status text NOT NULL CHECK (status IN ('booked','cancelled','completed')),
  idempotency_key text,
  request_fingerprint text NOT NULL,
  created_by uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT appointments_patient_idempotency_key UNIQUE (patient_id, idempotency_key)
);
ALTER TABLE appointments ADD CONSTRAINT no_overlap
  EXCLUDE USING gist (provider_id WITH =, during WITH &&)
  WHERE (status = 'booked');
```

Why this works — including empty schedules: the database checks the exclusion constraint atomically at insert/commit across concurrent transactions. Two concurrent `INSERT`s for overlapping `during` cannot both commit; one gets `23P01` and the app returns `409 Conflict`. This holds when no conflicting row existed beforehand, unlike `SELECT → INSERT` in `READ COMMITTED`, where both reads see “free” then both insert. Do not rely on in-process locks: with two processes/containers or a restart they diverge.

Range bounds default to `[)`, so adjacent bookings ([09:00,09:30) and [09:30,10:00)) do not conflict, and the constraint is partial on `status = 'booked'`, so a cancelled row stops blocking the time it freed.

Isolation level: the default READ COMMITTED is sufficient here, because the loser of the race is rejected by the constraint at commit (SQLSTATE 23P01) rather than by a stale read, so there is nothing to re-read and retry. Under SERIALIZABLE the same concurrent insert can instead fail with 40001 (serialization_failure), and that one requires retrying the whole transaction, not just the statement.

Timezone: the clinic's local timezone is a decision to make explicitly and store with the clinic (for example `America/New_York`). Keep `during` in UTC as `tstzrange` and build local ranges with `start_local AT TIME ZONE 'America/New_York'` rather than by casting a bare `date`/`timestamp`. A DST transition day is 23 or 25 hours long, so “the clinic's day” is not a fixed 24-hour window: define the local business-day boundary (local midnight to local midnight) and derive slots from the local calendar instead of adding 24 hours.

If the existing DB is MySQL/InnoDB (no exclusion constraints): pre-create fixed `slots(provider_id, starts_at UNIQUE)` and book with one atomic write. Preferred: `UPDATE slots SET status='booked' WHERE provider_id=? AND starts_at=? AND status='free'` — `rows_affected = 1` means this request booked the slot, `0` means the slot was already taken (return 409). `INSERT ... ON DUPLICATE KEY UPDATE status='booked'` also works, but there `rows_affected` is 1 when the row was inserted and 2 when an existing row was updated, so both 1 and 2 mean success and only 0 means the slot was taken; testing `rows_affected == 1` on that path reports a false conflict on a successful booking.

Fixed-slot limitation: the `slots(provider_id, starts_at)` scheme only works if every booking snaps to the grid. Variable-length appointments (the follow-up case in §1) need a booking→slot join table, and the unique key in that table is what prevents double booking:

```sql
CREATE TABLE booking_slots (
  appointment_id uuid NOT NULL REFERENCES appointments(id),
  slot_id uuid NOT NULL REFERENCES slots(id),
  provider_id uuid NOT NULL,
  PRIMARY KEY (appointment_id, slot_id),
  UNIQUE (provider_id, slot_id)
);
```

The booking transaction inserts all of its slot rows and treats a duplicate-key error on `(provider_id, slot_id)` as 409.

Three locking options, in order of preference for PostgreSQL: (1) the exclusion constraint above, which is atomic, needs no application coordination, and is correct even when the conflicting row does not exist yet; (2) a lock row, `SELECT ... FOR UPDATE` on one row per provider, correct only if that row exists and every booking path takes it; (3) `pg_advisory_xact_lock(hashtext(provider_id::text))`, which needs no schema change but needs a stable key, the same lock ordering in every writer, and protects nothing if some path writes without taking it. Option 1 is the recommendation because it is the only one whose correctness does not depend on every writer cooperating.

Idempotency (double-click/retry ≠ double booking): client sends `Idempotency-Key`; the key is scoped to the caller, not global. The constraint is `UNIQUE (patient_id, idempotency_key)` and the lookup uses the authenticated `patient_id`, never a `patient_id` taken from the request body: a global unique key would let one patient's key return another patient's row. On key reuse with a DIFFERENT payload (a different `request_fingerprint`, a hash of the booking request) the server returns `409 Conflict` and never returns the other party's row. On key reuse with the SAME payload it returns the original row. The key column is nullable, so a request that omits the key is accepted but gets no retry protection; the client must send one. Cancellation is `UPDATE ... WHERE id=? AND status='booked'`; freed time becomes bookable; keep cancelled rows for audit.

## 5. Critical flows

Book: `POST /appointments {provider, start, duration, Idempotency-Key}` → authz (the patient id comes from the session, never from the request body) → validate window → single `INSERT` → on `23P01` return 409 with next-available suggestions → on success return booking. Timeout does not mean “not booked” — the client retries with the same key and the same payload and the server returns the existing row; the same key with a different payload is a conflict (409), and the server must not echo the stored row for a different request.

Cancel: `POST /appointments/:id/cancel` → authz (owner or receptionist) → conditional update. Race between two cancels is safe; race between cancel + rebook resolves by transaction order.

## 6. Failure, security, operations (minimal but explicit)

DB is the failure domain. Backups: `pg_basebackup` (or a managed snapshot) plus continuous WAL archiving enables point-in-time recovery; `pg_dump` is a logical, portable fallback only and cannot be replayed to an arbitrary point in time. Quarterly restore drill to a scratch host; document RTO/RPO after one drill. Observability: log booking attempts with provider/time/result; alert on 5xx rate and DB unavailability; track 409 rate (spike = UX or scraping issue), p95 booking latency, backup age. Runbook: “booking 500s” → check DB, queue-free deploy rollback, then run the overlap query below to confirm whether the invariant was breached.

```sql
-- Manual overlap check for one provider and window; lists booked rows that intersect it.
-- Same '&&' overlap operator and '[)' bounds as the exclusion constraint uses.
SELECT a.id, a.patient_id, a.during, a.status
FROM appointments a
WHERE a.provider_id = $1
  AND a.status = 'booked'
  AND a.during && tstzrange($2::timestamptz, $3::timestamptz, '[)');
```

Trust boundaries: patient sees only own bookings; receptionist role checked in server code per request (never trust client tenant/role claim); audit `created_by/cancelled_by`; encrypt in transit, encrypt at rest via managed disk/DB; retention/deletion policy confirmed with clinic before storing health-adjacent notes.

## 7. Trade-offs accepted

Monolith couples deploys but removes network partitions, dual-write, and cache-invalidation failures. Constraint-based correctness costs a Postgres-specific DDL (including the `btree_gist` extension) or slot-table discipline on MySQL and requires clients to handle 409s — cheaper than operating a lock service or queue for 300/day.

*Evidence that would change this answer: different RDBMS, requirement for cross-clinic scheduling, or a hard reminder-delivery SLA that forces async workers.*
