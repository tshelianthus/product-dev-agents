# Handoff Flow Contract

This file defines runtime context flow. Field shapes live in [`outputs.md`](outputs.md); this file must not duplicate `pm_output.dispatches`.

## Context Passing

| Direction | Method | Content |
|-----------|--------|---------|
| architect -> all | persisted file | project context file with stack, conventions, and toolchain constraints |
| pm -> data | runtime handoff | task card, entities, query paths, project context |
| data -> backend | runtime handoff | data contract with schema definitions and constraints |
| backend -> qa | runtime handoff | API contract |
| backend -> frontend | runtime handoff | API contract |

## Field Authority

- pm-agent dispatch fields: [`outputs.md`](outputs.md#pm-output)
- bus output fields: [`outputs.md`](outputs.md#bus-output)
- issue and conflict fields: [`issues.md`](issues.md)

`data_contract` and `api_contract` must carry `contract_version` and `updated_at`. Downstream agents must reject stale versions.
