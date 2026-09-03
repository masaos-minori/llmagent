---
name: git-commit-and-sync
description: |
  Use this skill when managing a complete Git commit and sync workflow.
  Covers: status check, selective staging, conventional commit message creation,
  fetch-based remote sync with automatic fast-forward or non-interactive rebase
  onto the upstream branch, abort-and-report on rebase conflicts, validation, and
  push with approval.
  Forbids destructive commands, interactive/arbitrary rebase, force push, and
  unsafe merge.
---

# Git Commit and Sync Skill

## When to use

- checking Git status, staging files, committing changes
- syncing with the remote via `git fetch`, then fast-forwarding or automatically
  rebasing onto the upstream branch when histories have diverged
- pushing commits after explicit approval
- completing a full safe Git sync flow in one pass

Use this skill only inside a local Git repository.

## When not to use

- interactive rebase (`rebase -i`), rebasing onto anything other than the current
  upstream branch, force push, hard reset, or history rewrite → do not run (this
  skill's own automatic, non-interactive upstream rebase in Phase 7 is not affected
  by this restriction — see Core rules)
- branch deletion or untracked file cleanup → do not run
- conflicts that require product or business decisions → stop and ask
- repository state is unclear (detached HEAD, bisect in progress, rebase already in
  progress, etc.) → stop

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
| 7 | Sync | `git fetch`; fast-forward when possible, else automatic non-interactive rebase onto upstream when histories diverged and the tree is clean; abort and stop on rebase conflict; validate after a successful sync |
| 8 | Ask Before Push | require explicit approval unless already granted |
| 9 | Push | `git push`; report upstream if missing |
| 10 | Report | branch, staged files, commit message, sync/push result, warnings |

See `workflow.md` for detailed phase content including commands and stop conditions.

---

## Fast path

Use only when the user clearly approved all steps AND all conditions hold:

- working tree has no pre-existing conflict, merge, or rebase state
- upstream branch is set (or the user has acknowledged none exists)

Run the full phase sequence: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10. There is no
phase left to skip — Phase 7 already determines internally whether a rebase is
needed at all, and aborts safely on its own if one is attempted and conflicts.

Stop immediately if any command fails or Phase 7 reports a rebase conflict.

---

## Core rules

- Always check status first.
- Use explicit file paths for `git add` by default; never use `git add .`.
- `git add -A` only when the user explicitly says "all changes".
- Never run dangerous commands: `reset --hard`, `clean -fd`, `clean -fdx`, `checkout -- .`, `restore .`, `restore --staged .`. This skill's own procedure never needs them, so — unlike `AGENTS.md` Policy's confirmation-based exception for multi-file/recursive destructive commands — there is no confirmation path to offer here; treat them as forbidden, not as "ask first".
- Never run history-rewriting or unsafe sync commands: `rebase -i`/`rebase --interactive`, `rebase --onto` (or any rebase target other than the current branch's upstream), `rebase --continue`, `rebase --skip`, `commit --amend`, `merge` (other than the fast-forward `merge --ff-only @{u}` step in Phase 7 Sync), `merge --abort`, `pull` (any form — Phase 7 Sync decomposes this into `fetch` followed by fast-forward or rebase instead), `push --force`, `push --force-with-lease`, `push -f`.
- Phase 7 Sync replaces `git pull --ff-only`: run `git fetch`, then fast-forward (`git merge --ff-only @{u}`) when the local branch has not diverged, or run a single non-interactive `git rebase @{u}` when histories have diverged — only when the working tree is clean and an upstream branch exists. If the rebase reports a conflict, immediately run `git rebase --abort`, stop without pushing, and report the conflicted files (captured before the abort). Never run `git rebase --continue`, `git rebase --skip`, or resolve a rebase conflict manually — this skill never resolves rebase conflicts automatically.
- After a successful fast-forward or rebase, run `git status --short`, `git diff --stat`, and applicable validation (see Composition rules) before proceeding to push approval.
- Push only after explicit user approval (this is the git-specific instance of `AGENTS.md` Execution policy's confirmation exception for pushing to remote repos).

---

## Composition rules

- `python-test-and-fix` — if validation fails after a fast-forward or rebase, delegate to this skill
- `python-lint-typecheck` — run lint/type checks as part of post-sync validation when Python files are involved

---

## Improvement feedback

After using this skill:
- if a stop condition was missing for a real failure, add it to workflow.md Phase 7 (Sync)
- if the fast-forward/diverged/up-to-date/ahead-only classification in workflow.md Phase 7 missed a real edge case, document the missing case there — do not add automatic conflict resolution; a rebase conflict is always aborted and reported, never resolved
- if the fast path conditions were wrong, refine them here
