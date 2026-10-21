<!-- Use when a public or cross-service interface must be precise enough that two teams can implement against it without guessing. -->

# API contract: <API or service boundary>

Owner: <team that owns the contract>
Date: YYYY-MM-DD
Status: Draft | Published | Deprecated
Transport: REST/HTTP | gRPC | GraphQL | Events | Files/batch
Spec source: <OpenAPI document, .proto file, SDL schema, or event schema, and where it lives>
Consumers: <internal and external callers, with their versions>

## 1. Resource and operation model

| Operation | Method and path | Semantics (safe/idempotent/unsafe) | Purpose | Caller | Authorization context | Idempotency |
|---|---|---|---|---|---|---|
| | | | | | | |

State the resource identity, the naming convention, and the HTTP semantics actually used. Do not label JSON over HTTP as REST without resource identity and method semantics. For events, state the topic, key, partition, and delivery semantics.

## 2. Schemas

### Request

| Field | Type | Required | Nullable | Unit/format | Default | Enum values | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

### Response

| Field | Type | Always present | Nullable | Unit/format | Notes |
|---|---|---|---|---|---|
| | | | | | |

### Error body

Problem details shape, per RFC 9457. Use this as the single error representation unless the protocol forbids it.

```json
{
  "type": "https://errors.example.com/<error-type-slug>",
  "title": "<short human-readable summary>",
  "status": 400,
  "detail": "<safe, specific explanation. No stack traces, hostnames, secrets, or personal data>",
  "instance": "<request or correlation id>",
  "code": "<stable machine-readable code>",
  "errors": [
    { "field": "<field path>", "code": "<stable code>", "message": "<safe message>" }
  ]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| type | URI | Yes | Stable, resolvable, one per error class |
| title | string | Yes | Short summary, no detail |
| status | integer | Yes | Matches the HTTP status |
| detail | string | No | Human-readable, safe to show, never internal detail |
| instance | string | Yes | Request or correlation id, echoed in logs |
| code | string | Yes | Stable machine-readable code, the compatibility surface |
| errors | array | No | Field-level detail for validation failures |

Rules: the `code` values are the compatibility surface, never the `title` string. New error classes are additive. A message change is not a breaking change; a code removal or a status change is.

## 3. Status codes

| Status | When it is returned | Client obligation |
|---|---|---|
| 400 | Malformed or invalid request | Fix and do not retry as-is |
| 401 | Not authenticated | Re-authenticate, then retry |
| 403 | Authenticated but not authorized | Do not retry |
| 404 | Resource absent or not visible to this caller | Do not retry |
| 409 | Conflict with current state, including idempotency payload mismatch | Re-read, reconcile |
| 412 | Precondition failed (ETag or If-Match) | Re-read, then retry once |
| 422 | Semantically invalid | Fix and do not retry as-is |
| 429 | Rate or quota exceeded | Retry after Retry-After with backoff and jitter |
| 5xx | Server or dependency failure | Retry with backoff, bounded budget |

Distinguish 401 from 403. Returning 404 instead of 403 hides existence; state the choice.

## 4. Idempotency

Applies to every unsafe operation that a client may retry. A header alone is not a guarantee.

| Property | Rule |
|---|---|
| Key name and format | <header or field, and the accepted format, for example UUIDv4> |
| Caller scope | <the key is unique within a caller identity, a tenant, an endpoint, or a global namespace> |
| Tenant binding | <the key is bound to the tenant from the authenticated context; a key from one tenant replayed under another is rejected> |
| Retention | <duration the key and its stored response are retained> |
| Payload mismatch behaviour | <a replay with the same key and a different body returns 409 with a stable code, never a second effect> |
| Concurrent duplicates | <two in-flight requests with the same key: the second waits, or returns 409 in progress, or replays> |
| Response replay | <the original status and body are returned for the retained window> |
| Atomicity with the business effect | <the key record and the business write commit together, in one transaction, or the effect is not idempotent> |
| Scope of the guarantee | <the guarantee covers the effect of this operation only, and not downstream effects such as emitted events or emails> |

State the retry safety of each operation explicitly: <operation, retry safe yes/no, and the mechanism>.

## 5. Pagination

| Property | Rule |
|---|---|
| Style | <offset, keyset/cursor, or time cursor> |
| Determinism | <ordering tuple, and the tie-breaker that makes it total> |
| Default and maximum page size | <default>, <maximum> |
| Page size ceiling behaviour | <over-large request is clamped or rejected> |
| Token opacity and expiry | <opaque token>, <expiry> |
| Token invalidation | <what happens if the underlying data changed, and whether the token is still valid> |
| Total count | <returned, or omitted, and the cost of returning it> |
| Stable snapshot | <whether the pages reflect a consistent snapshot or a moving target> |
| Empty and last page | <shape of an empty result and how the client detects the end> |

Keyset pagination is required where offset pagination degrades on large or shifting datasets. Say which one applies and why.

## 6. Auth context

| Property | Rule |
|---|---|
| Authentication | <scheme, token type, issuer, audience, expiry, where the token is validated> |
| Authorization | <by action, object, property, and workflow state> |
| Enforcement point | <the service that owns the resource validates authorization, not only the gateway> |
| Tenant binding | <tenant is taken from the authenticated membership, never from a client-supplied body field> |
| Object-level checks | <how ownership is checked for every resource, including nested, batch, export, and background paths> |
| Deny default | <unmatched action or resource> |
| Scope and roles | <scopes or roles, and what each permits> |
| Audit | <which actions are audited, and what the audit record contains> |
| Service-to-service | <workload identity, short-lived credentials, rotation> |

## 7. Rate limits and quotas

| Limit | Scope | Value | Unit | Window | Enforcement point | Response on breach | Header or field |
|---|---|---|---|---|---|---|---|
| | | | requests/s | | | 429 | <Retry-After, quota fields> |

Per-tenant fairness, burst allowance, and the behaviour of long-running operations. State the retry signal the client must honour.

## 8. Compatibility rules

| Rule | Statement |
|---|---|
| Versioning strategy | <URI path, header, media type, date-based, or none. State the default and when a version is added> |
| When to version | <the breaking change that requires a new version> |
| Additive changes | <allowed without a version bump: new optional field, new endpoint, new enum value for a documented open enum> |
| Breaking changes | <removing or renaming a field, changing a type, narrowing validation, changing a default, changing status codes, changing ordering, changing pagination semantics, changing an error code> |
| Unknown field handling | <ignored, or rejected> |
| Enum evolution | <closed enum: new value is breaking. Open enum: clients must tolerate unknown values> |
| Deprecation policy | <how a version is deprecated, notice channel, and the support window> |
| Retirement | <measured usage before removal, and the notice period> |
| Old client behaviour | <the version of the oldest supported client, and what it must keep working> |
| Consumer-driven tests | <which contracts are covered by provider and consumer tests> |
| Event schema evolution | <additive field rules, key changes, and replay of old events> |

State the minimum supported client version and the date it stops being supported.

## 9. Limits, payload, and abuse controls

| Control | Rule |
|---|---|
| Max request body | <bytes> |
| Max batch size | <items> |
| Max query cost | <items scanned, or complexity rule> |
| Timeout | <deadline and the response when it is exceeded> |
| Retry budget | <total deadline and attempt cap> |
| Rate of abuse control | <per-identity and per-tenant limits, and challenge or block behaviour> |

## 10. Examples

Request and response for the primary operation, and one error. Examples are the part most callers copy, so make them real.

```http
POST /v1/<resources> HTTP/1.1
Idempotency-Key: 3f7c1c3e-1b2a-4a1e-9d3f-2c1b6a5d9e01
```

## Before you deliver

- Every operation states its semantics, its authorization context, and whether a retry is safe.
- No invented numbers. Every limit, size, timeout, and window carries units and a source, or is labelled a proposed default with an owner.
- Every field in the contract maps to a requirement, a constraint, or a named risk reduction, and no field is undocumented.
- The error contract is complete, machine-readable, and safe: no internal detail, no secrets, no personal data.
- Idempotency is specified end to end, including the caller scope, the tenant binding, the retention, the payload mismatch behaviour, and the atomicity with the business effect.
- The compatibility rules are explicit, and the oldest supported client version and its end-of-support date are stated.
- Restore and rollback are drills with an owner and a date, not intentions.
