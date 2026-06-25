# Product Dev Agents Contracts

This file is the contract index for the Product Dev Agents bundle. Read it before orchestrating multi-agent work, then load only the referenced contract file required by the current action.

## Authority

- Cross-skill handoff flow: [`handoff.md`](handoff.md)
- Project context schema and temporary assumptions: [`context-schema.md`](context-schema.md)
- Agent input schemas, dispatches, `run_output`, `pm_output`, `bus_output`, and completion checks: [`outputs.md`](outputs.md)
- Issue shape, defaults, and conflict format: [`issues.md`](issues.md)
- Agent registry and dependency map: [`../agents.yaml`](../agents.yaml)
- Runtime state: [`state-machine.md`](state-machine.md)
- Artifact rules: [`artifact-policy.md`](artifact-policy.md)
- Retry and recovery rules: [`retry-policy.md`](retry-policy.md)
- Machine-readable schemas: [`../schemas`](../schemas)

Do not define contract fields in agent skills or prompt templates. Agent skills may describe when to use a contract, but field structure belongs in these references and the matching machine-readable schemas.

## Required Loading

| Action | Read |
|--------|------|
| Validate or construct `project_context` | [`context-schema.md`](context-schema.md) |
| Validate machine-readable output shape | Relevant file in [`../schemas`](../schemas) |
| Resolve agent path, dependency, or produced artifact | [`../agents.yaml`](../agents.yaml) |
| Construct dispatches or runtime handoff | [`handoff.md`](handoff.md) for flow, [`outputs.md`](outputs.md) for fields |
| Return or validate `pm_output` / `bus_output` | [`outputs.md`](outputs.md) |
| Validate a complete run artifact | [`../schemas/run_output.schema.json`](../schemas/run_output.schema.json), then [`../scripts/check_run_output.py`](../scripts/check_run_output.py) |
| Report issues or conflicts | [`issues.md`](issues.md) |
| Check whether orchestration is complete | [`outputs.md`](outputs.md), [`issues.md`](issues.md), [`state-machine.md`](state-machine.md) |
| Recover after blocked or failed work | [`retry-policy.md`](retry-policy.md) |

`context_schema_version` defaults to the current schema in [`../schemas/project_context.schema.json`](../schemas/project_context.schema.json) when omitted.

## Invariants

- Architect writes project context and exits; it is not a daily runtime step.
- pm-agent owns task breakdown, skip decisions, summary, and conflict arbitration.
- Professional agents do not call each other directly.
- `data_contract` and `api_contract` must carry `contract_version` and `updated_at`.
- Downstream agents must return `CONTRACT_MISMATCH` or ask pm-agent to resend when a handoff version is stale.
- Blocking issues must be retained and moved through `open`, `accepted`, `resolved`, or `superseded`; do not delete issue history to make a run appear complete.
