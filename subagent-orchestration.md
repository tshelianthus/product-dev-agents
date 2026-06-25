# Subagent Task Prompt Templates

This file is an optional prompt template pack for hosts that support Task/subagent execution. It is not the source of truth for orchestration contracts.

Authority order:

1. `SKILL.md` defines execution mode, dependency order, fallback behavior, and completion rules.
2. `references/contracts.md` indexes the authoritative contract references for handoff flow, context schema, contract versioning, outputs, and issues.
3. This file only shows how to package those contracts into Task prompts.

The default execution mode remains Inline. Use these templates only when `execution_mode: subagent` is explicitly requested and the Task tool is available.

Subagent mode is host-specific; Task is a placeholder for the host's subagent primitive.

## Mode Rules

- Use the same handoff fields, issue model, skip rules, and completion rules as Inline mode.
- If Task is unavailable, record a non-blocking `TOOL_UNAVAILABLE` issue and continue Inline with `bus_output.execution_mode_used: inline-fallback`.
- Never start dependent layers in the same batch.
- Run `data-agent` before `backend-agent`.
- Run `qa-agent` and `frontend-agent` only after `backend-agent` has produced a consumable `backend_output.api_contract`.
- Let only the parent bus or `pm-agent` route, summarize, and arbitrate conflicts.

## Generic Task Prompt

```text
Use the skill at {agent_skill_path}.

User intent:
{intent}

Execution mode:
subagent

Handoff JSON:
{handoff_json}

Requirements:
- Read and follow {agent_skill_path}.
- Treat the handoff JSON as the only upstream contract for this run.
- Produce the exact {expected_output_name} structure defined by the skill.
- Preserve contract_version and updated_at fields on any *_contract you consume or produce.
- Report issues with code, severity, message, blocking, owner, and action.
- Do not call other professional agents directly. Return handoff requests to the parent.
```

## Agent Task Packaging

Construct `{handoff_json}` from [`references/handoff.md`](references/handoff.md) and [`references/outputs.md`](references/outputs.md). This file must not repeat per-agent field schemas.

| Agent | Skill path | Expected output | Start rule |
|-------|------------|-----------------|------------|
| data-agent | `data-agent/SKILL.md` | `data_output` | Start before backend unless explicitly skipped |
| backend-agent | `backend-agent/SKILL.md` | `backend_output` | Start after data completes or no-data-change skip is recorded |
| qa-agent | `qa-agent/SKILL.md` | `qa_output` | Start after backend produces consumable `api_contract` |
| frontend-agent | `frontend-agent/SKILL.md` | `frontend_output` | Start after backend produces consumable `api_contract`; may batch with QA |

## Parent Aggregation

After subagents return, aggregate into `bus_output` as defined in [`references/outputs.md`](references/outputs.md#bus-output). `final_summary` must pass through `pm_output.summary`.
