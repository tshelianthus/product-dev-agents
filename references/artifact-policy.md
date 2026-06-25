# Artifact Policy

Artifacts are files, contracts, generated code, migration plans, test plans, screenshots, reports, or other durable outputs created or referenced during orchestration.

## Rules

- Every artifact reported in `bus_output.artifacts` must include `path` and `kind`.
- Generated artifacts must be written only when the user requested implementation or the active agent is explicitly responsible for file generation.
- Draft artifacts must be labeled as drafts and must not be described as executed, verified, or deployed.
- API and data contracts are artifacts even when they are embedded in agent output rather than written to disk.
- Secret-bearing files, real credentials, customer data, private environment files, and generated artifacts containing secrets must not be committed or listed as shareable outputs.

## Contract Artifacts

`data_contract` and `api_contract` must include:

- `contract_version`
- `updated_at`
- enough structure for the declared downstream consumers to validate fields, operations, or paths

If a contract is degraded because a tool is unavailable, the artifact must still preserve these fields and carry a `TOOL_UNAVAILABLE` issue.

## Integration Artifacts

When both qa-agent and frontend-agent run, the bus or pm-agent must verify:

- frontend handoff includes routes or selectors required by E2E planning
- QA coverage references the same API contract version as frontend binding
- mock artifacts comply with `mock_policy`
- unresolved blocking issues are not hidden behind a final summary
