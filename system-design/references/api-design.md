# API and contract design

## Begin with consumers and semantics

Identify callers (browser, mobile, partner, internal service, batch, webhook), user journeys, resource/command model, authorization context, traffic, compatibility period, and transport requirements. Keep public contracts separate from internal database schemas. Define behavior, not just JSON shape.

Compare REST/HTTP, RPC/gRPC, GraphQL, event, and file/batch interfaces based on interaction, streaming, browser compatibility, payload efficiency, tooling, caching, versioning, and operational constraints. Do not label JSON-over-HTTP as REST without resource and HTTP semantics. GraphQL flexibility adds query-cost, resolver authorization, and N+1 controls; RPC can create chatty interfaces; binary RPC may increase tooling/proxy friction.

## Contract checklist

- Resource identity, names, methods/actions, request/response schemas, required/optional/null behavior, defaults, enums, units, and validation.
- Authentication and authorization by action, object, property, tenant, and workflow state.
- HTTP status semantics, headers, conditional requests/caching, stable machine-readable errors, and safe messages.
- Filtering, ordering, deterministic pagination, page size limits, and token expiry/opacity.
- Payload limits, rate limits, quotas, deadlines, `Retry-After`, concurrency, and abuse controls.
- Partial update semantics, field masks, optimistic concurrency/ETags, and conflict responses.
- Async operation acceptance, status resource, progress, cancellation, deduplication, and expiry.
- Webhook signing, replay window, retries, delivery IDs, ordering, and consumer idempotency.
- Compatibility policy, deprecation/support window, migration examples, and generated contract validation.

Use OpenAPI for HTTP contract description when it fits; use `.proto` and compatibility checks for gRPC; GraphQL SDL/schema validation for GraphQL. A schema tool does not prove authorization, semantics, performance, or end-to-end compatibility. Test negative authorization and old-client behavior.

## HTTP, retries, and idempotency

Follow RFC 9110 semantics for safe and idempotent methods. A timeout is ambiguous: the server may have committed before the response was lost. Never blindly retry side effects. For retryable create/payment/job operations, define an idempotency key's caller scope, tenant binding, retention, payload mismatch behavior, concurrent duplicates, response replay, and atomicity with the business effect. A header alone is not a guarantee.

Bound retries and coordinate a total deadline/retry budget across layers. Use backoff and jitter for transient failures where retry can help. Respect throttling signals. Avoid retry storms, nested retry multiplication, and retrying permanent validation/authorization errors.

## Errors and compatibility

Return correct protocol status plus stable machine-readable code/type, safe detail, and request/correlation identifier. RFC 9457 problem details can standardize HTTP error bodies; avoid leaking stack traces, internal hostnames, secrets, or personal data. Treat status, schema, enum meaning, ordering, defaults, and pagination behavior as compatibility surfaces. Additive changes can still break clients if their assumptions are undocumented.

Choose and document a versioning/deprecation model. Version only when needed; preserve old behavior for a stated support window; measure usage before retirement. Consumer-driven contract tests help independently deployed services, but complement provider tests, security testing, schema compatibility, and integration tests.

## Security/API abuse review

Check object-, property-, and function-level authorization; mass assignment; cross-tenant access; excessive data exposure; SSRF; injection; unbounded list/query cost; batch amplification; unsafe upstream data; and inventory of old endpoints. Validate authorization inside the service that owns the resource, not only at a gateway. API keys identify a client/application in some contexts but are not end-user authentication or a hard billing/security boundary by default.

## Recommended sources

Use RFC 9110 and RFC 9457 for HTTP semantics/errors; OpenAPI specification for HTTP description; RFC 9700 and current OpenID specifications for OAuth/OIDC security; OWASP API Security Top 10 as awareness input, not exhaustive assurance. Google AIPs are useful published conventions, not universal standards. Verify current versions when working on a specific contract. See [sources](sources.md).
