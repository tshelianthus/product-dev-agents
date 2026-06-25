---
name: api-contract-principles
description: API contract guardrails for the Product Dev Agents bundle. Use when backend-agent exports or reviews API contracts consumed by frontend-agent and qa-agent, especially OpenAPI or equivalent machine-readable API descriptions. This is a cross-cutting rules skill, not a professional delivery layer.
---

# API Contract Principles

## Position

Apply these guardrails when producing `backend_output.api_contract`. The contract is the handoff artifact for frontend-agent and qa-agent.

## Guardrails

- Prefer the repository's existing contract source of truth and generation tool.
- If no generator exists, produce a valid OpenAPI 3.x document or an equivalent machine-readable contract that frontend and QA can consume.
- Store or reference the contract in the project's documented contract location; if no location exists, use the location declared in `project_context` or record an issue asking pm-agent to choose one.
- Expand API version prefixes into concrete path strings in exported contracts; do not leave template placeholders in final `paths`.
- Include request schemas, response schemas, status codes, error shapes, authentication requirements, and examples only when they are consistent with the real contract.
- Preserve `contract_version` and `updated_at` on `api_contract`.
- If generation/export tooling is unavailable, return a hand-written contract draft with `TOOL_UNAVAILABLE` and mark whether it is sufficient for frontend/QA or blocking.
- Never mention a framework-specific export path unless it is discovered in the target repository or provided by `project_context`.

## Output Contract

`backend_output.api_contract` must contain enough structured data for downstream agents:

```yaml
api_contract:
  contract_version: string | int
  updated_at: string
  format: openapi-3.x | other
  source: generated | handwritten | existing
  document: object | string
  path: string
```
