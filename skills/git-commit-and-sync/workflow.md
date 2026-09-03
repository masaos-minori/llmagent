# Git Commit and Sync — Detailed Workflow

## Toolchain

| Command | Phase | Role |
|---|---|---|
| `git status --short` | Check Status | list modified/staged/untracked files |
| `git branch --show-current` | Check Status | confirm current branch |
| `git diff --stat` | Check Status | summarize unstaged changes |
| `git add <files>` | Stage Files | stage explicit paths |
| `git add -A` | Stage Files | stage all changes (user approval required) |
| `git diff --cached --stat` | Check Staged | verify staged set before commit |
| `git diff --cached --name-only` | Check Staged | list staged file paths |
| `git commit -m` | Commit | create conventional commit |
| `git fetch` | Sync | update remote-tracking refs only; never touches the working tree or current branch |
| `git rev-parse --abbrev-ref --symbolic-full-name @{u}` | Sync | confirm an upstream branch exists |
| `git rev-parse HEAD` / `git rev-parse @{u}` / `git merge-base HEAD @{u}` | Sync | classify the sync case: up to date, fast-forward, ahead-only, or diverged |
| `git status --porcelain` | Sync | confirm the working tree is clean before attempting a rebase |
| `git merge --ff-only @{u}` | Sync | fast-forward onto upstream when the local branch has not diverged |
| `git rebase @{u}` | Sync | non-interactive rebase onto upstream when histories have diverged |
| `git diff --name-only --diff-filter=U` | Sync | capture conflicted file paths before aborting a failed rebase |
| `git rebase --abort` | Sync | abandon a conflicted rebase and restore the pre-rebase state |
| `git status --short` / `git diff --stat` | Sync | validate repository state after a successful fast-forward or rebase |
| `git push` | Push | push to remote after approval |
| `git push --set-upstream origin <branch>` | Push | set upstream if missing (suggestion only) |

Forbidden commands: see `SKILL.md` Core rules.

---

## Phase 1: Check Status

```bash
git status --short
git branch --show-current
git diff --stat
```

Report:
- current branch
- changed files (modified, staged, untracked)

Stop if:
- not a Git repository
- branch name cannot be determined
- Git state is unclear (detached HEAD, bisect, rebase in progress)

---

## Phase 2: Choose Files

Default: use explicit paths.

```bash
git add scripts/agent.py tests/test_agent.py
```

Use `git add -A` only when the user says "all changes":

```bash
git add -A
```

Do not use `git add .` — it stages relative to the current directory, which may be unexpected.
Do not stage files unrelated to the task.

---

## Phase 3: Stage Files

```bash
git add <files>
```

Then verify:

```bash
git diff --cached --stat
git diff --cached --name-only
```

Confirm the staged set matches the intended scope.

---

## Phase 4: Check Staged

If `git diff --cached --name-only` returns no output, stop.

Report:
- No staged changes found. Nothing to commit.

---

## Phase 5: Make Commit Message

Read staged diff only. Derive the message from what is actually staged.

Format:

```
<type>: <summary>
```

Allowed types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `build`, `ci`, `perf`, `style`

Examples:
- `docs: update Git workflow skill`
- `fix: handle missing upstream branch`
- `refactor: simplify conflict resolution logic`

Do not reference filenames in the summary unless unavoidable.
Do not fabricate content from unstaged changes.

---

## Phase 6: Commit

```bash
git commit -m "<type>: <summary>"
```

Then verify:

```bash
git status --short
```

Stop if commit fails (see `rules/coding.md` Prohibited behavior (all tasks) for the
`--no-verify` prohibition — not repeated here).

---

## Phase 7: Sync (Fetch, Fast-Forward, or Rebase)

This phase replaces `git pull --ff-only` with `git fetch` followed by an explicit
fast-forward-or-rebase decision, so histories that have diverged from the upstream
branch can be synced automatically instead of stopping outright.

Always run first:

```bash
git fetch
```

`git fetch` only updates remote-tracking refs — it never touches the working tree or
the current branch, so it is always safe to run regardless of repository state.

Confirm an upstream branch exists:

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

If this fails (no upstream configured for the current branch), skip the rest of this
phase — there is nothing to compare against — and continue to Phase 8. Phase 9 (Push)
already handles the missing-upstream case for the push itself.

### Classify the sync case

```bash
git rev-parse HEAD
git rev-parse @{u}
git merge-base HEAD @{u}
```

- `HEAD` and `@{u}` identical → already up to date. Continue to Phase 8.
- `HEAD` equals the merge-base (local has not diverged; upstream has new commits) →
  **fast-forward** (below).
- `@{u}` equals the merge-base (upstream has not moved; local is ahead only) →
  nothing to sync. Continue to Phase 8.
- Otherwise (both sides have commits the other lacks since the merge-base) →
  histories have **diverged** → **rebase** (below).

### Fast-forward

```bash
git merge --ff-only @{u}
```

This can only fast-forward or fail cleanly — it never creates a merge commit and
never produces a conflict. If it fails unexpectedly, stop and report the error; do
not fall back to a non-fast-forward merge or a rebase for this case.

### Rebase (only when histories have diverged)

Before rebasing, confirm both preconditions hold:

- **Working tree is clean**: `git status --porcelain` returns no output for tracked
  changes (Phase 6's commit should already have made this true; re-check rather than
  assume).
- **Upstream branch exists**: already confirmed above.

If either precondition fails, stop and report why the rebase cannot proceed — do not
rebase against a dirty tree and do not rebase without a resolvable upstream.

```bash
git rebase @{u}
```

This MUST be a plain, non-interactive rebase onto the current branch's own upstream
only — never `rebase -i`, never `rebase --onto` with a different target.

If the rebase completes with no conflicts, continue to Post-Sync Validation below.

If the rebase reports a conflict, capture the conflicted files **before** aborting —
this information disappears once the rebase is abandoned:

```bash
git diff --name-only --diff-filter=U
```

Then abort immediately:

```bash
git rebase --abort
```

Stop. Do not push. Report:
- `Rebase onto @{u} failed with conflicts. Rebase aborted; branch restored to its pre-rebase state.`
- the conflicted file paths captured above

Do not run `git rebase --continue`, `git rebase --skip`, or attempt to resolve the
conflict manually in any way — this skill never resolves rebase conflicts
automatically, regardless of how small or textual the conflict looks.

### Post-Sync Validation (after a successful fast-forward or rebase)

```bash
git status --short
git diff --stat
```

If Python files were touched by the fast-forward or rebase, run:

```bash
uv run pytest tests/ -x -q
```

Delegate to `python-test-and-fix` if validation fails, or to `python-lint-typecheck`
for lint/type checks, per `SKILL.md` Composition rules.

Stop if:
- `git fetch` fails.
- The fast-forward merge fails for a reason other than needing a rebase (e.g.
  uncommitted local changes blocking it).
- The rebase reports a conflict (handled above — always abort and report; never
  continue, skip, or resolve manually).
- Post-sync validation (status/diff review, or tests) fails.

Do not run the commands `SKILL.md` Core rules forbids: `git pull` in any form,
`git rebase -i`/`--interactive`, `git rebase --onto` to any target other than the
current branch's upstream, `git rebase --continue`, `git rebase --skip`, `git merge`
other than the `--ff-only` step above, `git merge --abort`.

---

## Phase 8: Ask Before Push

Unless the user already approved push in this session, ask:

> Commit complete. Sync succeeded. Approve `git push`?

Do not push without explicit approval.

---

## Phase 9: Push

```bash
git push
```

If upstream is missing, stop. Report:

> Current branch has no upstream branch.
> Suggested command: `git push --set-upstream origin <branch>`

Do not run the suggestion without user approval.

---

## Phase 10: Report

Report:
- branch and commit SHA
- staged files
- commit message
- sync result (already up to date, fast-forwarded, rebased onto upstream, aborted
  due to a rebase conflict — with the conflicted file paths, or skipped because no
  upstream exists)
- validation result (if status/diff review or tests were run after a successful
  sync)
- push result (or reason push was skipped)
- remaining uncommitted changes
- stop conditions triggered, with explanation
- warnings

Prohibited behavior: see `SKILL.md` Core rules.
