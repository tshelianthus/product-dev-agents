# Retry and Recovery Policy

Retries are allowed only when the rerun has a clear changed input, corrected contract, resolved tool failure, or accepted risk. Blind retries are not part of the orchestration contract.

## Retry Triggers

| Trigger | Action |
|---------|--------|
| `CONTRACT_MISMATCH` resolved | Rerun the agent that rejected the contract and every downstream consumer. |
| `UPSTREAM_INCOMPLETE` resolved | Rerun the blocked agent and downstream consumers. |
| `TOOL_UNAVAILABLE` fixed | Rerun the affected agent if the degraded artifact was not accepted. |
| `BLOCKED_BY_CONFLICT` arbitrated | Rerun agents whose outputs conflict with the arbitration decision. |
| User accepts risk | Mark issue `accepted`; rerun only if outputs need to record the acceptance. |

## Retry Limits

- A run may retry the same agent at most once for the same unchanged issue.
- Repeated failure with the same issue moves the run to `needs_user_input` or `failed`.
- Downstream agents must not retry against stale `contract_version` values.

## Recovery Output

Recovered runs must preserve the issue history by updating issue `status` rather than deleting the original issue. Use:

- `resolved` when the problem was fixed
- `accepted` when the user accepted the risk
- `superseded` when a later decision or contract made the issue irrelevant
