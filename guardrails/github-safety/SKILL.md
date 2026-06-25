---
name: github-safety
description: Enforce safe Git and GitHub operations. Use before any clone, pull, branch, commit, push, merge, rebase, PR, release, GitHub CLI operation, or workflow that touches remote repository history. Loaded by the Product Dev Agents bundle, pm-agent, and architect-agent when Git or remote history is involved.
---

# GitHub Safety

## Location in Product Dev Agents

**Cross-cutting safety constraint**, does not belong to any layer of the data → backend → qa/frontend orchestration pipeline.

| Triggering Party | When Loaded |
|--------|---------|
| Bus (`product-dev-agents`) | Any scenario involving Git / GitHub / remote history |
| pm-agent | Step 0: Tasks involving branches, commits, pushes, PRs, releases |
| architect-agent | Step 0: Git initialization, branch strategy, CI/CD, remote repository |

Priority is higher than individual role-local workflows; runs in parallel with the orchestration layer and does not replace the pm-agent scheduling responsibilities.

---

## Iron Rules

Treat remote history, protected branches, credentials, and destructive Git operations as production assets.

- Never make changes, commits, or pushes directly on `main`, `master`, release branches, or protected branches unless the user explicitly confirms that exact target.
- Before any remote-impacting operation, inspect branch, working tree, remotes, upstream, and pending changes.
- Use a safe working branch and PR-based workflow by default.
- Do not bypass reviews, checks, branch protection, or required status gates.
- Never force-push, rewrite shared history, delete remote branches, or run destructive Git commands without explicit confirmation of the exact command and target.
- Never commit or push secrets, credentials, tokens, private keys, `.env` files, or sensitive generated artifacts.
- When branch strategy, remote target, or history impact is unclear, stop and ask.

---

## Connection to the Bus Issue Model

When violating Iron Rules or pre-check fails before operations, the relevant layer should output a structured `issue` (written to the `issues` list by the triggering party):

```yaml
issues:
  - id: github-safety-001
    code: BLOCKED_BY_CONFLICT   # or TOOL_UNAVAILABLE (git/gh unavailable)
    severity: error
    message: "Target branch not confirmed, direct push to main is prohibited"
    blocking: true
    owner: github-safety
    action: "Please ask the user to confirm the branch strategy and target remote before proceeding"
    status: open
```

When `blocking: true`, the bus must not claim orchestration is complete until the user confirms or corrects it.

