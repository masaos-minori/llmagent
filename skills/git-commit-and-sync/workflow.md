# Git Commit and Sync — Detailed Workflow

## Toolchain

| Command | Phase | Role |
|---|---|---|
| `git status --short` | Check Status | list modified/staged/untracked files |
| `git branch --show-current` | Check Status | confirm current branch |
| `git diff --stat` | Check Status | summarize unstaged changes |
| `git add <files>` | Stage Files | stage explicit paths |
| `git add -A` | Stage Files | stage all changes, only when the user explicitly says "all changes" — See `skills/git-commit-and-sync/SKILL.md`, section "Core rules". |
| `git diff --cached --stat` | Check Staged | verify staged set before commit |
| `git diff --cached --name-only` | Check Staged | list staged file paths |
| `git restore --staged <path>` | Stage Files | unstage one unexpected file by explicit path (never `.`) |
| `uv run python tools/run_validation_gates.py` | Check Staged / Sync | run the gates the change requires (`--base ORIG_HEAD` after a sync) |
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
| `git fetch` + `git rev-parse HEAD`/`@{u}` + `git merge-base HEAD @{u}` + `git branch -r --contains` | Sync (Pre-push recheck) | re-read remote state right before Phase 8; detect a concurrent push or an already-pushed commit |
| `git push` | Push | push to remote automatically once Commit and Sync succeed with no conflicts |
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

Detect an abnormal state with these checks (any hit means stop):

```bash
git status                                  # "rebase in progress", "You have unmerged paths", "All conflicts fixed"
git diff --name-only --diff-filter=U        # unmerged paths remain
test -e "$(git rev-parse --git-path MERGE_HEAD)" && echo merge-in-progress
test -e "$(git rev-parse --git-path BISECT_LOG)" && echo bisect-in-progress
```

An empty `git branch --show-current` means detached HEAD.

Stop if:
- not a Git repository
- branch name cannot be determined (empty `git branch --show-current`)
- Git state is unclear (detached HEAD, bisect, merge or rebase in progress, unmerged paths)

---

## Phase 2: Choose Files

Default: use explicit paths.

```bash
git add scripts/agent.py tests/test_agent.py
```

See `skills/git-commit-and-sync/SKILL.md`, section "Core rules".

Stage only files that implement the current instruction's change. A file `git status`
shows as modified but that this instruction did not touch stays unstaged, unless the user
has said "all changes".

Archival renames already staged by `tools/manage_workitem_stage.py ... --stage-only`
(`issues/done/`, `plans/done/`, `implementations/done/`) are part of the work cycle that
produced them: MUST NOT unstage them, and include them in the commit for that cycle's
change. `git commit` records the whole index, so check them in Phase 1's status output
before committing.

A file already staged before this skill started (other than the archival renames above) is
not part of the chosen set unless the current instruction changed it; Phase 3 reports it as
a mismatch rather than silently committing it.

**Completed when**: every file the current instruction changed is identified as a path to
stage (or the `-A` condition applies). The chosen set is that list plus any pre-staged
archival renames.

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

Also inspect the staged set for files that must not be committed: secrets and credentials
(`.env*`, `*.pem`, `*.key`, tokens in the diff), local databases, and unexpectedly large or
binary files (check `git diff --cached --stat`). A hit is a stop condition — report the path
and ask; MUST NOT commit it.

**Completed when**: `git diff --cached --name-only`'s output exactly matches the file set
chosen in Phase 2 (explicit paths plus pre-staged archival renames).
**Stop and report when**: it does not match (a Phase 2 file is missing from the staged
list, or an extra file appears) — MUST NOT proceed to Phase 4 with an unexplained mismatch.
An extra file that this instruction did not change may be removed from the index with an
explicit path only (`git restore --staged <path>`, never `.`), then re-verify; if the extra
file is an archival rename or its origin is unclear, stop and ask instead.

---

## Phase 4: Check Staged

If `git diff --cached --name-only` returns no output, stop.

Report:
- No staged changes found. Nothing to commit.

Pre-commit validation: run the gates the staged change requires, before committing.

```bash
uv run python tools/run_validation_gates.py
```

It maps changed files to the checkers in `routing.md` "When to run which tool" and
`rules/toolchain.md` (fast mode by default; `--full` only when the user asks). It also
satisfies `AGENTS.md` Global Rule 9 for `docs/` and `tools/` changes. A `Fail` or `Blocked`
summary is a stop condition; fix the cause (delegating per `SKILL.md` Composition rules),
re-stage explicit paths, and re-run Phase 3. If the staged change is non-code only (e.g.
workflow artifacts under `issues/`/`plans/`/`implementations/`) and the tool reports no
applicable gate, continue.

---

## Phase 5: Make Commit Message

Sub-steps in order: classify (5a), flag mixed concerns if any (5b), write the message (5c).

### Step 5a: Classify the staged diff by type

Read staged diff only — never unstaged changes. Classify what the staged diff actually
does against the Allowed types below:

`feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `build`, `ci`, `perf`, `style`

Project-specific addition: `plan` — generating or archiving
`issues/` → `plans/` → `implementations/` workflow artifacts (`issue-to-plan`,
`plan-to-implementation-procedure`, `code-implementation`), e.g. `plan: generate implementation
procedures for <topic>`. Use it instead of `docs`/`chore` only when the staged diff is
entirely such output — a commit mixing it with an unrelated `feat`/`fix` change still
follows Step 5b (MUST NOT silently fold it into `plan`).

### Step 5b: Flag mixed concerns

If the staged diff matches more than one type above (e.g. a `feat` change and an unrelated
`docs` fix staged together), report this to the user before committing — MUST NOT silently
pick one type and omit the other's intent from the summary. Proceed to 5c with the user's
choice (one combined message, or split into separate commits) once acknowledged.

### Step 5c: Write the message

Format:

```
<type>[(<scope>)]: <summary>

[body: why the change was made]

[trailer lines required by the session, e.g. Co-Authored-By]
```

- Write the message in English (matches the existing history).
- `(<scope>)` is optional; use it when the change belongs to a tracked work item or module,
  e.g. `plan(125756): re-take test anchors`. Keep the summary within about 72 characters.
- Add a body when the reason is not obvious from the summary (`AGENTS.md` Global Rule 6: a
  commit needs a clear message explaining the reason). A summary-only message is acceptable
  only for a self-explanatory change.
- Append any trailer the session's attribution instruction requires (for example
  `Co-Authored-By`); omit it when no such instruction exists. Never invent one.

Example: `fix: handle missing upstream branch`

MUST NOT reference filenames in the summary unless unavoidable.
MUST NOT fabricate content from unstaged changes.

**Completed when**: the message's `<type>` matches 5a's classification (or the user's 5b
choice) and its summary describes only what is actually staged.

---

## Phase 6: Commit

```bash
git commit -m "<type>[(<scope>)]: <summary>" -m "<body>" -m "<trailer>"
```

Omit the `-m` parts that are not needed (each `-m` adds one paragraph).

Then verify:

```bash
git status --short
git rev-parse HEAD    # record this SHA for Phase 7's pre-push recheck and the report
```

Stop if commit fails (see `rules/coding.md` Prohibited behavior (all tasks) for the
`--no-verify` prohibition — not repeated here).

A pre-commit hook failure means no commit was created (so there is nothing to amend;
`commit --amend` stays forbidden). Recovery:

1. Read the hook output and fix the cause (if a hook reformatted files, the changes are in
   the working tree but not staged).
2. Re-stage the affected files with explicit paths and re-run Phase 3's verification.
3. Create a new commit with the same message.

Each repeat of the same hook failure counts toward `AGENTS.md` Attempt Limit (3); after
that, stop and report what was tried.

---

## Phase 7: Sync (Fetch, Fast-Forward, or Rebase)

Replaces `git pull --ff-only`: `git fetch`, then an explicit fast-forward-or-rebase decision.

Always run first:

```bash
git fetch
```

`git fetch` only updates remote-tracking refs, so it is always safe to run.

Confirm an upstream branch exists:

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

If this fails (no upstream configured), skip the rest of this phase and continue to Phase 8
(Push), which handles the missing-upstream case.

### Classify the sync case

```bash
git rev-parse HEAD
git rev-parse @{u}
git merge-base HEAD @{u}
```

- `HEAD` and `@{u}` identical → already up to date. Continue to Phase 8 (Push).
- `HEAD` equals the merge-base (local has not diverged; upstream has new commits) →
  **fast-forward** (below).
- `@{u}` equals the merge-base (upstream has not moved; local is ahead only) →
  nothing to sync. Continue to Phase 8 (Push).
- Otherwise (both sides have commits the other lacks since the merge-base) →
  histories have **diverged** → **rebase** (below).

### Fast-forward

```bash
git merge --ff-only @{u}
```

If it fails unexpectedly, stop and report the error; MUST NOT fall back to a
non-fast-forward merge or a rebase for this case.

### Rebase (only when histories have diverged)

Before rebasing, confirm both preconditions hold:

- **Working tree is clean**: `git status --porcelain --untracked-files=no` returns no
  output (tracked changes only; untracked files do not block a rebase). Re-check; MUST NOT
  assume Phase 6 made it true.
- **Upstream branch exists**: already confirmed above.

If either precondition fails, stop and report why the rebase cannot proceed — MUST NOT
rebase against a dirty tree and MUST NOT rebase without a resolvable upstream. No
`stash`/`autostash` workaround is allowed.

A dirty tree is expected when Phase 2 left unrelated modified files unstaged. In that case
the commit exists locally but is unpushed; report:
- `Committed locally; sync skipped because tracked files are modified: <paths>.`
- the options for the user: commit or discard those changes themselves, then re-invoke
  this skill

Record the pre-rebase SHA (the `git rev-parse HEAD` output from the classification step)
so it can be reported.

```bash
git rebase @{u}
```

This MUST be a plain, non-interactive rebase onto the current branch's own upstream
only — never `rebase -i`, never `rebase --onto` with a different target.

If the rebase completes with no conflicts, continue to Post-Sync Validation below.

If the rebase reports a conflict, capture the conflicted files before aborting:

```bash
git diff --name-only --diff-filter=U
```

Then abort immediately:

```bash
git rebase --abort
```

Stop. MUST NOT push. Report:
- `Rebase onto @{u} failed with conflicts. Rebase aborted; branch restored to its pre-rebase state.`
- the conflicted file paths captured above

Never continue, skip, or manually resolve the rebase, however small or textual the conflict looks. See `skills/git-commit-and-sync/SKILL.md`, section "Core rules".

### Post-Sync Validation (after a successful fast-forward or rebase)

```bash
git status --short
git diff --stat
```

Then run the gates for what the sync brought in (`ORIG_HEAD` points at the pre-sync tip):

```bash
uv run python tools/run_validation_gates.py --base ORIG_HEAD
```

If Python files under `scripts/` or `tests/` were touched by the fast-forward or rebase,
also run the tests; start with the test files mirroring the touched modules, and run the
whole suite only when the touched scope is unclear or the user asks:

```bash
uv run pytest tests/ -x -q
```

Delegate to `python-test-and-fix` if tests fail, or to `python-lint-typecheck` if
lint/type gates fail, per `SKILL.md` Composition rules.

If validation fails after a rebase, the branch stays in its rebased state and is not
pushed. MUST NOT roll back with `reset --hard`; report the pre-rebase SHA recorded above
and the failing output, and let the user decide.

### Pre-push recheck (last step of Phase 7, runs on every path that reaches Phase 8)

Another session or writer may have pushed (or rebased and pushed this very commit)
between the Sync decision and the push, so re-read the remote state once more right
before Phase 8. This includes the "already up to date" and "ahead only" paths and the
paths where the rebase/fast-forward just succeeded. It does not apply when no upstream
exists (Phase 8 stops on that case itself):

```bash
git fetch
git rev-parse HEAD
git rev-parse @{u}
git merge-base HEAD @{u}
```

Classify again and act:

- `@{u}` equals the merge-base and `HEAD` differs (upstream unchanged since Sync; local
  ahead only) → proceed to Phase 8 (Push).
- `HEAD` and `@{u}` identical → the commit is already on the remote (for example another
  session pushed it). Do not push. Confirm with `git branch -r --contains HEAD`, skip
  Phase 8, and report `already on upstream; no push needed` with the SHA.
- `HEAD` is an ancestor of `@{u}` (`HEAD` equals the merge-base, upstream has new
  commits) and `git branch -r --contains <commit SHA recorded in Phase 6>` lists the
  upstream branch → the commit reached the remote, possibly rebased under a different
  SHA by another writer. Do not push; report both SHAs and which upstream commit contains
  the change (compare subject lines with `git log --oneline @{u} -n 20`).
- Otherwise, when `@{u}` moved since Sync (it is no longer the merge-base of a local-
  ahead state, or histories diverged again) → stop before Phase 8 and report that the
  remote advanced after Sync, with the old and new `@{u}` SHAs. MUST NOT push into a
  predictable non-fast-forward rejection, MUST NOT re-run Sync automatically, and MUST
  NOT force; re-invoking this skill is the remedy (same as the transient rejection
  handling in Phase 8).

Record the commit SHA from Phase 6 (`git rev-parse HEAD` right after the commit) so this
recheck can identify the commit even if its SHA changes.

Stop if:
- `git fetch` fails (including the recheck's fetch).
- The fast-forward merge fails for a reason other than needing a rebase (e.g.
  uncommitted local changes blocking it).
- The rebase reports a conflict (handled above — always abort and report; see
  `skills/git-commit-and-sync/SKILL.md`, section "Core rules").
- Post-sync validation (status/diff review, or tests) fails.

MUST NOT run the commands `SKILL.md` Core rules forbids.

---

## Phase 8: Push

Push automatically once Phase 6 (Commit) and Phase 7 (Sync, including its Pre-push
recheck) have both succeeded with no conflicts and the recheck allowed proceeding — no
approval prompt is required for this step by default.

```bash
git push
```

If upstream is missing, stop. Report:

> Current branch has no upstream branch.
> Suggested command: `git push --set-upstream origin <branch>`

MUST NOT run the suggestion without user approval.

If an upstream exists but `git push` fails because the push target cannot be resolved
(for example `push.default=simple` with an upstream branch name that differs from the local
name), stop and report the exact message and `git config --get push.default`; MUST NOT
pass an explicit refspec or change the configuration on the user's behalf.

If `git push` is rejected for any other reason — most commonly a non-fast-forward
rejection because the remote advanced again after Phase 7's sync completed — apply
`SKILL.md` Core rules' push-rejection handling and report the exact rejection message.

### Transient non-fast-forward rejection (no retry)

A non-fast-forward rejection right after a successful rebase usually means the remote
advanced during the rebase-to-push window (a concurrent writer).

MUST NOT retry the push and MUST NOT re-run Sync automatically (`SKILL.md` Core rules). Stop,
report the exact rejection message, and never escalate to `force push`. Flag in the report
that the remote appears to be under active concurrent writes; re-invoking this skill after
the remote settles is then the likely remedy.

MUST NOT proceed to `git push` at all if:
- Phase 7 aborted a rebase due to a conflict (defense-in-depth reminder; Phase 7 already
  stops before this phase).
- Phase 7's Pre-push recheck found the commit already on the remote, or the remote
  advanced after Sync.
- Post-sync validation (Phase 7) failed.
- The user's current instructions say not to push, or ask for confirmation before
  pushing — follow that instruction instead of this phase's default (see `SKILL.md`
  Core rules). When the user has specifically asked for confirmation this way, ask:
  `Commit complete. Sync succeeded. Approve git push?` — only when the user requests it.

---

## Phase 9: Report

Report:
- branch and commit SHA
- staged files
- commit message
- pre-push recheck result (proceeded, already on upstream, or remote advanced — with the
  SHAs involved)
- sync result (already up to date, fast-forwarded, rebased onto upstream, aborted
  due to a rebase conflict — with the conflicted file paths, or skipped because no
  upstream exists)
- pre-rebase SHA (only when a rebase ran)
- validation result (Phase 4 gates, and status/diff review or tests after a successful
  sync)
- push result (or reason push was skipped)
- remaining uncommitted changes
- stop conditions triggered, with explanation
- warnings

Prohibited behavior: see `SKILL.md` Core rules.
