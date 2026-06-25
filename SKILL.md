---
name: product-dev-agents
description: A product development multi-agent orchestration suite, used for cross-layer product development, requirements with unclear ownership, work requiring coordination among architect/pm/data/backend/qa/frontend, or when the user explicitly requests product-dev agents orchestration. Supports Inline (default) and optional Subagent modes; single-layer database, backend, frontend, QA, or code explanation tasks should directly use the corresponding professional Agent rather than triggering the bus.
---

# Product Dev Agents — Orchestration Bus

## Role

This skill is the orchestration bus. It classifies product-development intent, chooses the first responsible skill, enforces execution mode and dependency order, and returns `bus_output`.

It does not replace professional agents. Product planning, task breakdown, skip decisions, summary, and conflict arbitration belong to [`pm-agent/SKILL.md`](pm-agent/SKILL.md).

Do not use the bus for single-file edits, code explanations, direct calls to a named agent, or tasks that clearly belong to one layer only.

## Must-Read References

- [`references/contracts.md`](references/contracts.md): do not orchestrate multi-agent work until this file has been read. It routes to the required contract references for handoff, context schema, issues, completion checks, and outputs.
- [`agents.yaml`](agents.yaml): read when resolving agent paths, dependencies, produced artifacts, and the QA/frontend integration-check.
- [`guardrails/github-safety/SKILL.md`](guardrails/github-safety/SKILL.md): read before any Git, GitHub, branch, commit, PR, release, push, pull, merge, rebase, or remote history operation.
- [`subagent-orchestration.md`](subagent-orchestration.md): optional Task prompt packaging guide only when `execution_mode: subagent` is requested and Task is available.

## Execution Mode

Default to `inline`.

- `inline`: read each target `{agent}/SKILL.md` in the current session and execute it to its `*_output`.
- `subagent`: use Task subagents only when explicitly requested and available.
- `inline-fallback`: if `execution_mode: subagent` is requested but Task is unavailable, record non-blocking `TOOL_UNAVAILABLE`, continue inline, and set `bus_output.execution_mode_used: inline-fallback`.

```
Required order: pm-agent -> data-agent -> backend-agent -> (qa-agent || frontend-agent)
```

Do not start dependent work in the same batch. Only `qa-agent` and `frontend-agent` may run in parallel, and only after a consumable `backend_output.api_contract` exists.

## Skill Map

| Skill | Role |
|-------|------|
| [`architect-agent/SKILL.md`](architect-agent/SKILL.md) | One-time project initialization and project context file creation |
| [`pm-agent/SKILL.md`](pm-agent/SKILL.md) | Daily entry, task breakdown, routing, summary, conflict arbitration |
| [`data-agent/SKILL.md`](data-agent/SKILL.md) | Data structures, migrations, indexes, data contract |
| [`backend-agent/SKILL.md`](backend-agent/SKILL.md) | API design, backend logic, security review, API contract |
| [`qa-agent/SKILL.md`](qa-agent/SKILL.md) | Test planning, regression risk, coverage, E2E/performance planning |
| [`frontend-agent/SKILL.md`](frontend-agent/SKILL.md) | UI, API binding, state, errors, accessibility, component tests |
| [`guardrails/github-safety/SKILL.md`](guardrails/github-safety/SKILL.md) | Git/GitHub safety rules |
| [`guardrails/backend-security/SKILL.md`](guardrails/backend-security/SKILL.md) | Backend security guardrails |
| [`guardrails/api-contract-principles/SKILL.md`](guardrails/api-contract-principles/SKILL.md) | API contract guardrails |

## Routing

Treat wording examples as hints only. Prefer intent, required artifact, dependencies, and explicit user constraints.

| Intent | Route |
|--------|-------|
| New project or project initialization | `architect-agent`, then `pm-agent` |
| New feature, unclear product work, multi-layer work | `pm-agent` |
| Data structure or migration only | `data-agent` |
| Backend API/logic only | `backend-agent` |
| Frontend UI/API-binding only | `frontend-agent` |
| Test plan, regression, E2E, performance plan | `qa-agent` |
| Review of a specific layer | Target layer directly |
| Unclassified or cross-layer conflict | `pm-agent` |

For feature work, let pm-agent decide layer skips and downstream dispatches. For bug work, route to the layer indicated by evidence; if evidence is incomplete or multi-layer, route to pm-agent.

## Bus Loop

1. Parse `intent`, `scene`, `target_agents`, `skip_agents`, `project_context_path`, `context_schema_version`, and `execution_mode`.
2. If `target_agents` is provided, set `scene_detected: manual-target_agents`; otherwise classify by the routing table.
3. Load [`references/contracts.md`](references/contracts.md) before constructing handoff or validating context; then load the specific contract reference it requires.
4. Read and validate `project_context_path` when present. Missing context is non-blocking for the bus; pm-agent owns temporary assumptions.
5. Verify each target skill path exists before activation.
6. Activate skills in required order using inline or subagent mode; use [`agents.yaml`](agents.yaml) as the dependency map.
7. Stop downstream work on any unresolved `blocking: true` issue.
8. If both qa-agent and frontend-agent ran, perform the integration-check declared in [`agents.yaml`](agents.yaml).
9. Return `bus_output` using the shape in [`references/outputs.md`](references/outputs.md#bus-output) and [`schemas/bus_output.schema.json`](schemas/bus_output.schema.json).

---

## Interface

| Input | Type | Required | Notes |
|------|------|------|------|
| `intent` | string | ✅ | User's original input or intent description |
| `scene` | string | ❌ | Optional scene label; canonical values are defined by the output contract |
| `target_agents` | string[] | ❌ | Explicit agents; overrides automatic routing |
| `project_context_path` | string | ❌ | Caller-provided project context file path |
| `skip_agents` | string[] | ❌ | Agents explicitly skipped by caller |
| `context_schema_version` | string | ❌ | Defaults to the current `schemas/project_context.schema.json` version, used to validate the field contract of `project-context.md` |
| `execution_mode` | enum | ❌ | `inline` default / `subagent` |

Output: `bus_output` as defined in [`references/outputs.md`](references/outputs.md#bus-output).
