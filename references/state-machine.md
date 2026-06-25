# Orchestration State Machine

This file defines runtime state for Product Dev Agents orchestration. The bus owns orchestration state. pm-agent owns product decisions and conflict arbitration.

## Run Status

| Status | Meaning |
|--------|---------|
| `pending` | Run was accepted but no agent has started. |
| `running` | At least one activated agent is executing. |
| `completed` | All activated agents completed or were explicitly skipped, and no open blocking issue remains. |
| `blocked` | A blocking issue prevents downstream work. |
| `failed` | A required agent or validation step failed without a defined fallback. |
| `needs_user_input` | Progress requires a user decision, such as accepting a risk or choosing between conflicting designs. |

## Agent Status

| Status | Meaning |
|--------|---------|
| `pending` | Agent is selected but waiting for dependencies. |
| `running` | Agent is active. |
| `skipped` | Agent was intentionally skipped with a recorded reason. |
| `completed` | Agent returned its required output and schema checks passed. |
| `blocked` | Agent cannot continue because an upstream contract or required decision is missing. |
| `failed` | Agent failed and no fallback output is consumable. |
| `needs_user_input` | Agent requires a user decision before it can continue. |

## Transitions

1. Start in `pending`.
2. Move to `running` when pm-agent begins.
3. Mark each selected professional agent `pending` until dependencies are complete or skipped.
4. Mark an agent `completed` only after its output has the required top-level fields and any declared `*_contract` includes `contract_version` and `updated_at`.
5. Mark an agent `skipped` only when the skip reason is recorded in `bus_output.agents_skipped`.
6. Move the run to `blocked` when any open issue has `blocking: true`.
7. Move the run to `needs_user_input` when pm-agent cannot arbitrate without a product, security, or delivery tradeoff decision.
8. Resume from `blocked` or `needs_user_input` by updating issue `status` to `resolved`, `accepted`, or `superseded`, then rerunning affected downstream agents.
9. Move to `completed` only after integration-check passes when both qa-agent and frontend-agent were activated.

## Rerun Scope

When an upstream contract changes:

- `data_contract` changed: rerun backend-agent, then qa-agent and frontend-agent.
- `api_contract` changed: rerun qa-agent and frontend-agent.
- `project_context` changed: rerun every activated agent that consumed the previous context version.
- Non-blocking issue accepted: rerun only agents whose outputs explicitly depended on that issue.

Do not reuse stale downstream outputs after a contract version changes.
