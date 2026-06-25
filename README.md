# Product Dev Agents

Product Dev Agents is a contract-driven skill bundle. Unlike general-purpose multi-agent frameworks (such as AutoGen or CrewAI) that can be independently deployed and extended, this project is a narrow-scope skill bundle meant to orchestrate workflows within supported environments.

It supports dual-mode execution:
- **Default Inline**: read each skill's `SKILL.md` in the current session. This works in environments without Subagent or Task support.
- **Optional Subagent**: pass `execution_mode: subagent` to run eligible layers as Task subagents. If Task is unavailable, the bus records `TOOL_UNAVAILABLE`, falls back to Inline, and sets `bus_output.execution_mode_used: inline-fallback`.

## Repository Layout

```text
.
├── SKILL.md                  # Orchestration bus skill
├── architect-agent/SKILL.md
├── pm-agent/SKILL.md
├── data-agent/SKILL.md
├── backend-agent/SKILL.md
├── qa-agent/SKILL.md
├── frontend-agent/SKILL.md
├── guardrails/               # Guardrail skills
│   ├── github-safety/SKILL.md
│   ├── backend-security/SKILL.md
│   └── api-contract-principles/SKILL.md
├── references/contracts.md   # Contract loading index
├── references/*.md           # Handoff, context, output, and issue contracts
├── schemas/*.schema.json     # Schema definitions
├── agents.yaml               # Agent registry and dependency map
├── project-context.md        # Context template
└── subagent-orchestration.md # Optional task templates
```

## Orchestration Contract

The execution mode does not change the contract:

1. `data-agent` runs before `backend-agent`.
2. `backend-agent` must complete before `qa-agent` and `frontend-agent` start.
3. Only `qa-agent` and `frontend-agent` may run in parallel, and only after a consumable `api_contract` exists.
4. Handoffs use the fields declared in `pm_output.dispatches` and each layer's `*_output`.
5. Professional agents do not call each other directly. The bus and `pm-agent` route, summarize, and arbitrate conflicts.
6. Any `blocking: true` issue stops downstream work until the issue is resolved or explicitly accepted by the user.
7. If both `qa-agent` and `frontend-agent` run, the bus or pm-agent must perform the integration-check declared in `agents.yaml` before final summary.

## Contract Sources

- `agents.yaml` is the authoritative registry for agent paths, dependencies, produced artifacts, and the QA/frontend integration-check.
- `schemas/*.schema.json` are the machine-readable contracts for issues, project context, bus output, PM output, and professional agent outputs.
- `references/contracts.md` remains the loading index for humans and agents. It points to the schema and policy files that must be used for validation and recovery.
- `references/state-machine.md` defines run and agent lifecycle states.
- `references/artifact-policy.md` defines artifact reporting and contract artifact expectations.
- `references/retry-policy.md` defines recovery and rerun rules.

## Orchestration Diagram

```mermaid
flowchart TD
    %% ── Entry ──────────────────────────────────────────────────
    U(["👤 User Intent"]):::entry --> B["🚌 product-dev-agents\nOrchestration Bus"]:::bus

    %% ── Execution Mode Branch ───────────────────────────────────
    B --> M{{"execution_mode?"}}:::decision
    M -->|"inline (default)"| PM
    M -->|"subagent requested"| TA{{"Task tool\navailable?"}}:::decision
    TA -->|yes| PM
    TA -->|no| FB["⚠️ Record TOOL_UNAVAILABLE\nFallback → inline"]:::warn
    FB --> PM

    %% ── Phase 1: PM ─────────────────────────────────────────────
    subgraph PHASE1["Phase 1 · Planning"]
        direction TB
        PM["🗂 pm-agent\nRoute · Break down · Arbitrate"]:::agent
        PM --> TC["task_card\n+ dispatches"]:::artifact
    end

    %% ── Phase 2: Data ───────────────────────────────────────────
    TC --> DA
    subgraph PHASE2["Phase 2 · Data"]
        direction TB
        DA["🗄 data-agent\nSchemas · Migrations · Indexes"]:::agent
        DA --> DC["data_contract"]:::artifact
    end

    %% ── Phase 3: Backend ────────────────────────────────────────
    DC --> BA
    TC --> BA
    subgraph PHASE3["Phase 3 · Backend"]
        direction TB
        BA["⚙️ backend-agent\nAPI Design · Business Logic · Security"]:::agent
        BA --> AC["api_contract\n(OpenAPI)"]:::artifact
    end

    %% ── Phase 4: Parallel QA + Frontend ─────────────────────────
    AC --> GATE{{"consumable\napi_contract?"}}:::decision
    GATE -->|no| STOP["🛑 Stop downstream\nblock: true issue"]:::stop
    GATE -->|yes| QA & FE

    subgraph PHASE4["Phase 4 · Parallel"]
        direction LR
        QA["🧪 qa-agent\nTests · Regression\nE2E · Performance"]:::agent
        FE["🖥 frontend-agent\nUI · API Binding\nState · Accessibility"]:::agent
    end

    %% ── Integration Check ───────────────────────────────────────
    QA & FE --> IC["🔗 Integration Check\n• contract versions match\n• routes & selectors aligned\n• mock_policy honored"]:::check

    %% ── Output ──────────────────────────────────────────────────
    IC --> OUT(["📦 bus_output"]):::output
    STOP --> OUT

    %% ── Guardrails (cross-cutting) ───────────────────────────────
    subgraph GR["🛡 Guardrails  (read before relevant operations)"]
        direction LR
        GH["github-safety"]:::guard
        BS["backend-security"]:::guard
        AP["api-contract-principles"]:::guard
    end
    GR -. "enforced at" .-> B & PM & DA & BA & QA & FE

    %% ── Styles ──────────────────────────────────────────────────
    classDef entry    fill:#6366f1,stroke:#4f46e5,color:#fff,rx:20
    classDef bus      fill:#0f172a,stroke:#6366f1,color:#e2e8f0,font-weight:bold
    classDef decision fill:#1e293b,stroke:#94a3b8,color:#e2e8f0
    classDef agent    fill:#0e7490,stroke:#0891b2,color:#fff
    classDef artifact fill:#134e4a,stroke:#0d9488,color:#d1fae5,shape:parallelogram
    classDef guard    fill:#3b0764,stroke:#7c3aed,color:#ede9fe
    classDef check    fill:#92400e,stroke:#d97706,color:#fef3c7
    classDef output   fill:#166534,stroke:#22c55e,color:#dcfce7,rx:20
    classDef stop     fill:#7f1d1d,stroke:#ef4444,color:#fee2e2
    classDef warn     fill:#78350f,stroke:#f59e0b,color:#fef3c7
```

## Usage

Copy or keep this folder where the skill runner can load skills, then invoke the main bus for product-development work:

```yaml
intent: "YOUR_FEATURE_REQUEST"
execution_mode: inline
```

Use the workspace project's context file if one exists.

Use Subagent mode only when the host environment provides Task/subagent capability:

```yaml
intent: "YOUR_FEATURE_REQUEST"
execution_mode: subagent
```

The default is intentionally Inline so the repository remains compatible with plain sessions and other skill runners.

## Project Context

Use `project-context.md` as the neutral template for the target project's project context file. Replace every `YOUR_...` value with the target project's actual choices. The authoritative schema lives in `schemas/project_context.schema.json`; `references/context-schema.md` explains field responsibility and temporary assumptions. All agents must reject incompatible context versions rather than silently inventing defaults.

## Subagent Prompt Templates

`subagent-orchestration.md` is optional. It is only a Task prompt packaging guide for hosts that support subagents; `SKILL.md` and the files indexed by `references/contracts.md` remain the authority for orchestration behavior and handoff contracts.

## Open Source Notes

This repository is designed to be standalone: all role skills, GitHub safety rules, orchestration contracts, and the project-context template live in this repo. Do not commit private project context, credentials, `.env` files, tokens, customer data, or generated artifacts containing secrets.

## License

MIT. See `LICENSE`.
