---
name: backend-security
description: Backend security guardrails for the Product Dev Agents bundle. Use when backend-agent designs, reviews, or modifies APIs, authorization, audit logging, sensitive data handling, file upload, rate limiting, or server-side validation. This is a cross-cutting rules skill, not a data/backend/qa/frontend orchestration layer.
---

# Backend Security

## Position

Apply these guardrails before backend-agent finalizes API design or implementation notes. This skill does not call other agents and does not replace pm-agent arbitration.

## Guardrails

- Treat the server as the only security boundary; frontend visibility or disabled controls are not authorization.
- Require authentication for protected operations and explicit authorization for resource ownership, roles, tenant boundaries, and administrative actions.
- Validate and constrain all untrusted input, including path params, query params, request bodies, file uploads, headers, and webhook payloads.
- Keep sensitive fields out of responses, logs, errors, metrics, traces, and client-visible debug output unless explicitly required and masked.
- For writes and privileged reads, consider auditability: actor, target, action, result, timestamp, and correlation id.
- Bound expensive operations: pagination, batch size, payload size, rate limits, timeouts, and idempotency for retryable writes.
- Prefer project-standard error codes and avoid leaking internal implementation details.
- If `security_requirements` is absent, apply baseline guardrails and record that no task-specific security level was provided.

## Output Contract

Return security findings inside the caller's normal output:

```yaml
security_review:
  applied_guardrails:
    - authentication
    - authorization
    - sensitive_data
  risks:
    - severity: warning | error
      message: string
      blocking: boolean
      action: string
```

Blocking security findings must also appear in the shared `issues` list with owner `backend-agent` or `backend-security`.
