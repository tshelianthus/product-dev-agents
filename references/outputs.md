# Output Contract

This file explains `architect_output`, `pm_output`, `bus_output`, and completion checks. JSON Schema is the only structural authority; this Markdown explains semantics, routing, and completion timing. Any field shown below must match the schema files checked by `scripts/check_contracts.py`.

- [`../schemas/architect_output.schema.json`](../schemas/architect_output.schema.json)
- [`../schemas/dispatches.schema.json`](../schemas/dispatches.schema.json)
- [`../schemas/run_output.schema.json`](../schemas/run_output.schema.json)
- [`../schemas/pm_output.schema.json`](../schemas/pm_output.schema.json)
- [`../schemas/bus_output.schema.json`](../schemas/bus_output.schema.json)

Agent `input_schema` entries in [`../agents.yaml`](../agents.yaml) point at the matching input schema. Daily runtime professional-agent inputs reuse the same dispatch contract that `pm_output.dispatches` uses.

Complete run artifacts must first satisfy [`../schemas/run_output.schema.json`](../schemas/run_output.schema.json), then pass [`../scripts/check_run_output.py`](../scripts/check_run_output.py) for cross-agent runtime invariants.

## Contents

- [Architect Output](#architect-output)
- [PM Output](#pm-output)
- [Bus Output](#bus-output)
- [Completion Standard](#completion-standard)

## Architect Output

```yaml
architect_output:
  project_context_status: created | updated | unchanged | failed
  project_context_path: string
  context_schema_version: string
  initialized_artifacts:
    - path: string
      kind: string
  handoff:
    next_agent: string
    required_inputs: string[]
  issues: []
```

## PM Output

```yaml
pm_output:
  task_card: object
  plan: object
  execution_mode_used: inline | subagent | inline-fallback
  context_schema_version_used: string
  dispatches:
    data:
      task_card: object
      project_context: object
      entities: object[]
      query_paths: string[]
      constraints: object
    backend:
      task_card: object
      project_context: object
      data_contract: object
      security_requirements:
        level: strict | standard
        require_audit_log: boolean
        pii_fields: string[]
      performance_constraints: object
    frontend:
      task_card: object
      project_context: object
      api_contract: object
      design_spec: object
      state_constraints: object
      mock_policy: forbidden | allowed-with-todo
    qa:
      task_card: object
      project_context: object
      api_contract: object
      data_contract: object
      perf_targets: object
      scope: full | functional-only | perf-only | e2e | e2e-only
  summary: string
  handoff:
    next_agent: string
    required_inputs: string[]
  issues: []
```

`pm_summary` is the routed artifact name for `pm_output.summary`, which is the authority for `bus_output.final_summary`.

## Bus Output

```yaml
bus_output:
  context_schema_version: string
  execution_mode_used: inline | subagent | inline-fallback
  scene_detected: new-project | new-feature | bug-fix | review | frontend-only | unclassified | manual-target_agents
  agents_activated: string[]
  agents_skipped:
    - agent: string
      reason: string
  final_summary: string
  pm_summary_ref: string
  artifacts:
    - path: string
      kind: string
  handoff:
    next_agent: string
    required_inputs: string[]
  subagent_runs:
    - agent: string
      status: string
      task_id: string
  run_state:
    status: pending | running | completed | blocked | failed | needs_user_input
    agent_states:
      pm-agent: completed
      data-agent: skipped
      backend-agent: completed
      qa-agent: completed
      frontend-agent: completed
  issues: []
```

`subagent_runs` may be omitted in Inline mode.

`bus_output.run_state` is required by [`../schemas/bus_output.schema.json`](../schemas/bus_output.schema.json) and follows [`state-machine.md`](state-machine.md).

## Completion Standard

An orchestration is complete only when:

- Every activated agent has completed or has been explicitly skipped.
- pm-agent has produced `pm_output.summary`.
- All `blocking: true` issues are resolved or explicitly accepted by the user.
- `bus_output.final_summary` is filled when the bus was used.
- The integration-check in [`../agents.yaml`](../agents.yaml) has passed when both qa-agent and frontend-agent were activated.

`bus_output.final_summary` is a passthrough of `pm_output.summary`; it must not contradict pm-agent.
