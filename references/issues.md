# Issue Contract

This file explains issue defaults and conflict reporting. The machine-readable authority is [`../schemas/issue.schema.json`](../schemas/issue.schema.json).

## Issue Shape

```yaml
issue:
  id: string
  code: CTX_MISSING | TOOL_UNAVAILABLE | UPSTREAM_INCOMPLETE | CONTRACT_MISMATCH | BLOCKED_BY_CONFLICT
  severity: warning | error
  message: string
  blocking: true | false
  owner: product-dev-agents | pm-agent | data-agent | backend-agent | frontend-agent | qa-agent | architect-agent | github-safety | backend-security | api-contract-principles
  action: string
  status: open | accepted | resolved | superseded
  blocks: string[]
  related_artifacts:
    - path: string
      kind: string
  resolution: string
  accepted_by: string
  accepted_at: string
```

## Issue Defaults

When Product Dev Agents itself creates an issue, use these defaults unless a more specific skill overrides them:

| Code | Owner | Severity | Blocking | Action |
|------|-------|----------|----------|--------|
| `CTX_MISSING` | product-dev-agents | warning | false | Continue via pm-agent temporary assumptions; ask user to complete project context file |
| `CONTRACT_MISMATCH` | product-dev-agents | error | true | Upgrade the project context file or provide compatible `context_schema_version` |
| `TOOL_UNAVAILABLE` | product-dev-agents | warning | false | Use fallback or ask whether to skip/stop |
| `UPSTREAM_INCOMPLETE` | pm-agent | error | true | Ask upstream to complete required output and rerun affected layers |
| `BLOCKED_BY_CONFLICT` | pm-agent | error | true | Wait for pm-agent arbitration before downstream work |

New issues default to `status: open`. Accepted risks must use `status: accepted`; fixed issues must use `status: resolved`; outdated issues must use `status: superseded`.

## Conflict Format

Professional agents must not negotiate directly. Report cross-layer conflicts to pm-agent:

```text
CONFLICT [source-agent] vs [target-agent]: [description]
Suggestion: [arbitration proposal]
Blocking: yes | no
```

If a target skill path is missing or unreadable, create `TOOL_UNAVAILABLE`, list affected chain steps, and ask whether to skip the layer or stop the orchestration.

Do not remove historical issues during recovery. Update `status` according to [`retry-policy.md`](retry-policy.md).
