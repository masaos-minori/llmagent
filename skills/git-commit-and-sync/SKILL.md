---
name: git-commit-and-sync
description: |
  Use this skill when managing a complete Git commit and sync workflow.
  Covers: status check, selective staging, conventional commit message creation,
  fetch-based remote sync with automatic fast-forward or non-interactive rebase
  onto the upstream branch, abort-and-report on rebase conflicts, validation, and
  automatic push once commit, sync, and validation all succeed with no conflicts.
  Forbids destructive commands, interactive/arbitrary rebase, force push, and
  unsafe merge.
---

# Git Commit and Sync Skill

## When to use

- checking Git status, staging files, committing changes
- syncing with the remote via `git fetch`, then fast-forwarding or automatically
  rebasing onto the upstream branch when histories have diverged
- pushing commits automatically once commit, sync, and validation all succeed
  cleanly — unless the user's current instructions say not to push, or ask for
  confirmation first (see Core rules)
- completing a full safe Git sync flow in one pass

Use this skill only inside a local Git repository.

## When not to use

- interactive rebase (`rebase -i`), rebasing onto anything other than the current
  upstream branch, force push, hard reset, or history rewrite → MUST NOT run (this
  skill's own automatic, non-interactive upstream rebase in Phase 7 is not affected
  — see Core rules)
- branch deletion or untracked file cleanup → MUST NOT run
- conflicts that require product or business decisions → stop and ask
- repository state is unclear (detached HEAD, bisect in progress, rebase already in
  progress, etc.) → stop

---

## Phase overview

| Phase | Name | Goal |
|---|---|---|
| 1 | Check Status | branch, changed files, staged/unstaged/untracked |
| 2 | Choose Files | explicit paths by default; `git add -A` only if user says "all" |
| 3 | Stage Files | run `git add`; verify staged set with `--cached` diff; stop on secrets/large files |
| 4 | Check Staged | abort if nothing staged; run `tools/run_validation_gates.py` before committing (it also sees unstaged changes of parallel sessions); any `Fail` stops here |
| 5 | Make Commit Message | derive from staged diff; `<type>[(<scope>)]: <summary>` in English, body for the reason |
| 6 | Commit | `git commit -m`; check status after (a hook's stash can make a parallel session's unstaged files look missing: wait and re-check); on hook failure fix, re-stage, new commit |
| 7 | Sync | `git fetch`; fast-forward when possible, else automatic non-interactive rebase onto upstream when histories diverged and the tree is clean; abort and stop on rebase conflict; validate after a successful sync (a failure unrelated to this change is reported as a warning, not a stop); skip Phase 8 when a dirty tree blocks the rebase; re-fetch and re-classify right before push (skip if the commit is already on the remote, stop if the remote advanced) |
| 8 | Push | `git push` automatically once Commit and Sync succeeded with no conflicts; stop and report on missing upstream, rejection, or a "do not push"/confirm-first instruction |
| 9 | Report | branch, staged files, commit message, sync/push result, other commits published, ignored unrelated gate failures, warnings |

See `workflow.md` for detailed phase content including commands and stop conditions.

---

## Fast path

Push needs no separate approval step (see Phase 8), so the full sequence 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 runs whenever these conditions hold:

- working tree has no pre-existing conflict, merge, or rebase state
- upstream branch is set (or the user has acknowledged none exists)

No phase is skipped. Phase 7 determines internally whether a rebase is needed and aborts safely if it conflicts. Phase 8 pushes automatically unless a stop condition fires or the user's current instructions say otherwise.

Stop immediately if any command fails, Phase 7 reports a rebase conflict, or
Phase 8's push is rejected.

---

## Core rules

- Always check status first.
- Use explicit file paths for `git add` by default; never use `git add .`.
- `git add -A` only when the user explicitly says "all changes".
- Never run dangerous commands: `reset --hard`, `clean -fd`, `clean -fdx`, `checkout -- .`, `restore .`, `restore --staged .`. Unlike `AGENTS.md` Policy's confirmation-based exception for multi-file/recursive destructive commands, there is no confirmation path here; treat them as forbidden, not "ask first". Recover a clean state with Phase 1's status check plus Phase 2's explicit-path staging, without discarding work. The only permitted unstaging is `git restore --staged <explicit path>` for a single unexpected file (Phase 3); the whole-tree forms `restore .` and `restore --staged .` stay forbidden.
- Never run history-rewriting or unsafe sync commands: `rebase -i`/`rebase --interactive`, `rebase --onto` (or any rebase target other than the current branch's upstream), `rebase --continue`, `rebase --skip`, `commit --amend`, `merge` (other than the fast-forward `merge --ff-only @{u}` step in Phase 7 Sync), `merge --abort`, `pull` (any form — Phase 7 Sync decomposes this into `fetch` followed by fast-forward or rebase), `push --force`, `push --force-with-lease`, `push -f`.
- Phase 7 Sync replaces `git pull --ff-only`: run `git fetch`, then fast-forward (`git merge --ff-only @{u}`) when the local branch has not diverged, or run a single non-interactive `git rebase @{u}` when histories have diverged — only when the working tree is clean and an upstream branch exists. If the rebase reports a conflict, immediately run `git rebase --abort`, stop without pushing, and report the conflicted files (captured before the abort). Never resolve a rebase conflict manually or automatically (`--continue`/`--skip` are in the forbidden list above).
- After a successful fast-forward or rebase, run `git status --short`, `git diff --stat`, and applicable validation (see Composition rules) before proceeding to Phase 8 (Push).
- Push automatically (Phase 8) once Commit and Sync have both succeeded with no conflicts — no approval prompt is required by default; this is a deliberate, narrower exception to `AGENTS.md` Execution policy's general confirmation expectation for pushing to remote repos, scoped to this skill's own push step and recorded in `AGENTS.md` Execution policy. These safety conditions still apply and are never skipped:
  - Never push after an aborted rebase (Phase 7 already stopped before Phase 8), and never resolve a rebase or merge conflict automatically to force a push through.
  - Never use `push --force`, `push --force-with-lease`, `push -f`, or any other history-rewriting operation to make a push succeed (see the "Never run" list above).
  - Phase 7's Pre-push recheck runs immediately before Phase 8; if it shows the commit is already on the remote, do not push, and if it shows the remote advanced after Sync, stop (no automatic re-sync, no force).
  - If `git push` is rejected for any reason (including a non-fast-forward rejection from a remote that advanced again after Phase 7's sync) or the push destination cannot be determined safely (e.g. no upstream), stop and report the problem — MUST NOT retry, force, or re-run Sync automatically.
  - If the user's current instructions say not to push, or ask for confirmation before pushing, follow that instruction instead of this default — a live, narrower instruction always overrides this skill's own default per `rules/ai-execution.md` Instruction Precedence.

---

## Composition rules

- `python-test-and-fix` — if tests fail in pre-commit or post-sync validation, delegate to this skill
- `python-lint-typecheck` — if lint/type gates reported by `tools/run_validation_gates.py` fail (pre-commit or post-sync) and Python files are involved, delegate to this skill

---

## Improvement feedback

After using this skill:
- if a stop condition was missing for a real failure, add it to workflow.md Phase 7 (Sync) or Phase 8 (Push), whichever the failure belongs to
- if the fast-forward/diverged/up-to-date/ahead-only classification in workflow.md Phase 7 missed a real edge case, document the missing case there — MUST NOT add automatic conflict resolution; a rebase conflict is always aborted and reported, never resolved
- if a new kind of push rejection was found, add it to workflow.md Phase 8 as its own stop condition — MUST NOT add automatic retry, force, or conflict resolution to make the push succeed
- if the fast path conditions were wrong, refine them here
