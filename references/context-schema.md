# Context Schema Contract

This file explains the project context file field responsibility and pm-agent temporary assumptions. The machine-readable authority is [`../schemas/project_context.schema.json`](../schemas/project_context.schema.json).

## Contents

- [`schema_version` Responsibility](#schema_version-responsibility)
- [Unified Context Schema](#unified-context-schema)
- [Temporary Project Context](#temporary-project-context)

## `schema_version` Responsibility

1. Bus: read `project_context_path`; if present and `schema_version` differs from `context_schema_version`, return blocking `CONTRACT_MISMATCH`.
2. pm-agent: use the same rule and write `pm_output.context_schema_version_used`.
3. architect/data/backend/frontend/qa: reject unsupported context schemas with `CTX_MISSING` or `CONTRACT_MISMATCH`; do not silently parse unknown versions.

`context_schema_version` defaults to the current schema version in [`../schemas/project_context.schema.json`](../schemas/project_context.schema.json) when omitted.

## Unified Context Schema

All agents reading the project context file must use these field paths. Do not add new top-level fields without bumping `schema_version`.

```yaml
schema_version: "1.1"
tech_stack:
  language: string
  backend_framework: string
  frontend_framework: string
  database: string
  migration_tool: string
  package_manager:
    backend: string
    frontend: string
conventions:
  naming:
    api_path_style: string
    db_object_style: string
    component_style: string
    error_code_style: string
  api:
    version_prefix: string
  commit:
    format: string
toolchain:
  lint:
    backend: string[]
    frontend: string[]
  test:
    backend: string[]
    frontend: string[]
  build:
    backend: string[]
    frontend: string[]
  typecheck:
    backend: string[]
    frontend: string[]
  migrate: string[]
ci:
  platform: string
  pipeline_path: string
repo:
  layout:
    api: string
    backend: string
    frontend: string
    tests: string
    migrations: string
  api_contract_paths: string[]
  migration_paths: string[]
  test_paths: string[]
  generated_code_policy: string
runtime:
  auth_model: string
  tenancy_model: string
  environment_policy: string
  deployment_target: string
  observability: string
  feature_flag_policy: string
quality_gates:
  required_before_summary: string[]
issues:
  - id: string
    code: string
    severity: "warning" | "error"
    message: string
    blocking: boolean
    owner: string
    action: string
    status: string
```

When `project-context.md` is missing or incomplete, only pm-agent may create temporary assumptions for the current task. data/backend/frontend/qa must not independently choose default stack values.

## Temporary Project Context

When an existing project lacks `project-context.md`, pm-agent may create one-task temporary assumptions. These assumptions use the same shape as [Unified Context Schema](#unified-context-schema), but they are runtime handoff data, not a persisted project decision.

Temporary assumptions must:

- Set `schema_version` to the current `context_schema_version`.
- Mark inferred fields as temporary in `pm_output.issues` and affected dispatches.
- Include a non-blocking `CTX_MISSING` issue owned by `pm-agent`.
- Avoid inventing stack values when repository evidence is insufficient; request confirmation instead.
