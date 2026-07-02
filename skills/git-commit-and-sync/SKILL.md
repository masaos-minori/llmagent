---
name: git-commit-and-sync
description: |
  Use this skill when managing a complete Git commit and sync workflow.
  Covers: status check, selective staging, conventional commit message creation,
  fast-forward pull, simple conflict resolution, validation, and push with approval.
  Forbids destructive commands, history rewrite, force push, and unsafe merge.
---

# Git Commit and Sync Skill

## When to use

- checking Git status, staging files, committing changes
- pulling remote changes and pushing commits
- resolving simple text conflicts after `git pull --ff-only`
- completing a full safe Git sync flow in one pass

Use this skill only inside a local Git repository.

## When not to use

- rebase, force push, hard reset, or history rewrite → do not run
- branch deletion or untracked file cleanup → do not run
- conflicts that require product or business decisions → stop and ask
- repository state is unclear (detached HEAD, bisect in progress, etc.) → stop

---

## Phase overview

| Phase | Name | Goal |
|---|---|---|
| 1 | Check Status | branch, changed files, staged/unstaged/untracked |
| 2 | Choose Files | explicit paths by default; `git add -A` only if user says "all" |
| 3 | Stage Files | run `git add`; verify staged set with `--cached` diff |
| 4 | Check Staged | abort if nothing staged |
| 5 | Make Commit Message | derive from staged diff; use conventional commit format |
| 6 | Commit | `git commit -m`; check status after |
| 7 | Pull | `git pull --ff-only`; stop if fast-forward not possible |
| 8 | Resolve Conflicts | text-only, obvious, small changes; validate after edit |
| 9 | Commit Resolution | stage resolved files; `fix: resolve conflicts` message |
| 10 | Ask Before Push | require explicit approval unless already granted |
| 11 | Push | `git push`; report upstream if missing |
| 12 | Report | branch, staged files, commit message, pull/push result, warnings |

See `workflow.md` for detailed phase content including commands and stop conditions.

---

## Fast path

Use only when the user clearly approved all steps AND all conditions hold:

- no conflict files exist
- no unresolved merge state
- upstream branch is set

Run phases: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 10 → 11 → 12. Skip 8, 9.

Stop immediately if any command fails.

---

## Core rules

- Always check status first.
- Use explicit file paths for `git add` by default; never use `git add .`.
- `git add -A` only when the user explicitly says "all changes".
- Never run dangerous commands: `reset --hard`, `clean -fd`, `checkout -- .`, `restore .`.
- Never force push, rebase, merge, or amend.
- Run `git pull --ff-only` before every push; if fast-forward is not possible, stop and report the divergence to the user — do not rebase or merge without explicit instruction.
- Resolve only simple text conflicts; stop at any ambiguity.
- Push only after explicit user approval.

---

## Composition rules

- `python-test-and-fix` — if validation fails after conflict resolution, delegate to this skill
- `python-lint-typecheck` — run lint/type checks as part of conflict resolution validation when Python files are involved

---

## Improvement feedback

After using this skill:
- if a stop condition was missing for a real failure, add it to workflow.md Phase 7 or Phase 8
- if a conflict pattern proved safe to resolve automatically, document it in workflow.md Phase 8
- if the fast path conditions were wrong, refine them here
