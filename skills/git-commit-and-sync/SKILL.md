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
| 8 | Push | `git push` automatically once Commit and Sync succeeded with no conflicts; stop and report on missing upstream, rejection, or a "do not push"/confirm-first instruction |
| 9 | Report | branch, staged files, commit message, sync/push result, warnings |

See `workflow.md` for detailed phase content including commands and stop conditions.

---

## Fast path

There is only one path now — push no longer needs a separate approval step (see
Phase 8), so the full sequence runs whenever these conditions hold:

- working tree has no pre-existing conflict, merge, or rebase state
- upstream branch is set (or the user has acknowledged none exists)

Run the full phase sequence: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9. There is no phase
left to skip — Phase 7 already determines internally whether a rebase is needed at
all and aborts safely on its own if one is attempted and conflicts; Phase 8 pushes
automatically unless a stop condition fires or the user's current instructions say
otherwise.

Stop immediately if any command fails, Phase 7 reports a rebase conflict, or
Phase 8's push is rejected.

---

## Core rules

- Always check status first.
- Use explicit file paths for `git add` by default; never use `git add .`.
- `git add -A` only when the user explicitly says "all changes".
- Never run dangerous commands: `reset --hard`, `clean -fd`, `clean -fdx`, `checkout -- .`, `restore .`, `restore --staged .`. This skill's own procedure never needs them, so — unlike `AGENTS.md` Policy's confirmation-based exception for multi-file/recursive destructive commands — there is no confirmation path to offer here; treat them as forbidden, not as "ask first".
- Never run history-rewriting or unsafe sync commands: `rebase -i`/`rebase --interactive`, `rebase --onto` (or any rebase target other than the current branch's upstream), `rebase --continue`, `rebase --skip`, `commit --amend`, `merge` (other than the fast-forward `merge --ff-only @{u}` step in Phase 7 Sync), `merge --abort`, `pull` (any form — Phase 7 Sync decomposes this into `fetch` followed by fast-forward or rebase instead), `push --force`, `push --force-with-lease`, `push -f`.
- Phase 7 Sync replaces `git pull --ff-only`: run `git fetch`, then fast-forward (`git merge --ff-only @{u}`) when the local branch has not diverged, or run a single non-interactive `git rebase @{u}` when histories have diverged — only when the working tree is clean and an upstream branch exists. If the rebase reports a conflict, immediately run `git rebase --abort`, stop without pushing, and report the conflicted files (captured before the abort). Never run `git rebase --continue`, `git rebase --skip`, or resolve a rebase conflict manually — this skill never resolves rebase conflicts automatically.
- After a successful fast-forward or rebase, run `git status --short`, `git diff --stat`, and applicable validation (see Composition rules) before proceeding to Phase 8 (Push).
- Push automatically (Phase 8) once Commit and Sync have both succeeded with no conflicts — no approval prompt is required for this step by default; this is a deliberate, narrower exception to `AGENTS.md` Execution policy's general confirmation expectation for pushing to remote repos, scoped to exactly this skill's own push step. The following safety conditions still apply and are never skipped:
  - If Phase 7's rebase reported a conflict, Phase 7 already stopped before Phase 8 is reached — never push after an aborted rebase.
  - Never resolve a rebase or merge conflict automatically to force a push through.
  - Never use `push --force`, `push --force-with-lease`, `push -f`, or any other history-rewriting operation to make a push succeed (see the "Never run" list above — unchanged).
  - If `git push` is rejected for any reason (including a non-fast-forward rejection from a remote that advanced again after Phase 7's sync) or the push destination cannot be determined safely (e.g. no upstream), stop and report the problem — do not retry, force, or re-run Sync automatically.
  - If the user's current instructions say not to push, or ask for confirmation before pushing, follow that instruction instead of this default — a live, narrower instruction always overrides this skill's own default per `rules/ai-execution.md` Instruction Precedence.

---

## Composition rules

- `python-test-and-fix` — if validation fails after a fast-forward or rebase, delegate to this skill
- `python-lint-typecheck` — run lint/type checks as part of post-sync validation when Python files are involved

---

## Improvement feedback

After using this skill:
- if a stop condition was missing for a real failure, add it to workflow.md Phase 7 (Sync) or Phase 8 (Push), whichever the failure belongs to
- if the fast-forward/diverged/up-to-date/ahead-only classification in workflow.md Phase 7 missed a real edge case, document the missing case there — do not add automatic conflict resolution; a rebase conflict is always aborted and reported, never resolved
- if a new kind of push rejection was found, add it to workflow.md Phase 8 as its own stop condition — do not add automatic retry, force, or conflict resolution to make the push succeed
- if the fast path conditions were wrong, refine them here
