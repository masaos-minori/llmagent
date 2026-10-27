# Git Commit and Sync — Detailed Workflow

## Toolchain

Every command is given in its phase below. Gate runner: `uv run python tools/run_validation_gates.py` (Check Staged; `--base ORIG_HEAD` after a sync). `git fetch` only updates remote-tracking refs and never touches the working tree or current branch.

Forbidden commands: see `SKILL.md` Core rules.

---

## Phase 1: Check Status

```bash
git status --short
git branch --show-current
git diff --stat
```

Report the current branch and the changed files (modified, staged, untracked).

Detect an abnormal state with these checks (any hit means stop):

```bash
git status                                  # "rebase in progress", "You have unmerged paths", "All conflicts fixed"
git diff --name-only --diff-filter=U        # unmerged paths remain
test -e "$(git rev-parse --git-path MERGE_HEAD)" && echo merge-in-progress
test -e "$(git rev-parse --git-path BISECT_LOG)" && echo bisect-in-progress
```

An empty `git branch --show-current` means detached HEAD.

Stop if: not a Git repository; branch name cannot be determined; Git state is unclear (detached HEAD, bisect, merge or rebase in progress, unmerged paths).

---

## Phase 2: Choose Files

Default: explicit paths (`git add scripts/agent.py tests/test_agent.py`); see `skills/git-commit-and-sync/SKILL.md`, section "Core rules".

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

If `git diff --cached --name-only` returns no output, stop and report: No staged changes found. Nothing to commit.

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

What the gates see: `tools/run_validation_gates.py` selects the staged files (diffed
against `--base`, default `master`) plus every unstaged tracked change in the working tree
(`_changed_files`). Another session's unstaged edits therefore also select gates and can
make one fail. Read the summary's file list and compare it with Phase 3's staged set.

Only `Fail` and `Blocked` rows matter; `Not available` rows (a gate whose command needs a
runtime argument) are not failures.

An unrelated gate failure is a failure that this change cannot have caused. A `Fail` is
unrelated only when both hold:

- the gate's output names none of the files in the staged set (Phase 4) or in the diff the
  sync brought in (Phase 7), or the command itself errors before checking anything (a usage
  error, exit code 2); and
- the same gate did not report `Pass` earlier in this run.

In Phase 4, treat every `Fail` as a stop condition regardless: the staged set is yours to
fix. In Phase 7 (post-sync), an unrelated failure does not block Phase 8; it MUST be
reported in Phase 9 as a warning with the gate name, the command, and the exit code. If
the classification is unclear, stop and ask. An unrelated failure of the tool itself is
not fixed by this skill; point the user to an Issue (`issue-creator`).

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

MUST NOT reference filenames in the summary unless unavoidable.
MUST NOT fabricate content from unstaged changes.

**Completed when**: the message's `<type>` matches 5a's classification (or the user's 5b
choice) and its summary describes only what is actually staged.

---

## Phase 6: Commit

```bash
git commit -m "<type>[(<scope>)]: <summary>" -m "<body>" -m "<trailer>"
```

Omit the `-m` parts that are not needed (each `-m` adds one paragraph). The trailer goes
last, as its own `-m`, so it stays separated from the body by a blank line.

Then verify:

```bash
git status --short
git rev-parse HEAD    # record this SHA for Phase 7's pre-push recheck and the report
```

Compare this status with Phase 1's. A `pre-commit` run stashes unstaged tracked changes
and restores them afterwards, so with parallel sessions an unstaged file can briefly look
missing. If one from Phase 1 is absent, wait a short time and re-run `git status --short`.
Do not recreate, revert, or `git stash pop` anything; if it is still absent after a few
checks, stop and report.

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

Because the histories have diverged, a push would be rejected as non-fast-forward. Skip
Phase 8 entirely in this case (do not attempt the push) and go to Phase 9.

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

Stop. MUST NOT push. Report `Rebase onto @{u} failed with conflicts. Rebase aborted; branch restored to its pre-rebase state.` plus the conflicted file paths captured above.

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
also run the tests. Start with the touched files under `tests/` plus, for each touched
`scripts/<path>/<name>.py`, the matching `tests/<path>/test_<name>.py` when it exists
(`git diff --name-only ORIG_HEAD HEAD` lists them). Run the whole suite only when no
matching test file exists or the user asks:

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
  ahead only) → record the commits the push will publish, then proceed to Phase 8 (Push):

  ```bash
  git log --oneline @{u}..HEAD
  ```

  Any commit in this list that this run did not create (for example one a parallel
  session committed but has not pushed, or one carried over by a rebase) is published
  too. Do not stop for it, but list it in Phase 9 under "other commits published".
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

The Phase 6 commit SHA lets this recheck identify the commit even if its SHA changes.

Stop if: `git fetch` fails (including the recheck's); the fast-forward merge fails for a
reason other than needing a rebase (e.g. uncommitted local changes blocking it); the
rebase reports a conflict (always abort and report; `SKILL.md` Core rules); post-sync
validation (status/diff review, or tests) fails, unless it is an unrelated gate failure
under Phase 4's rule (report it as a warning instead).

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
- branch and commit SHA; staged files; commit message
- pre-push recheck result (proceeded, already on upstream, or remote advanced, with the SHAs)
- sync result (already up to date, fast-forwarded, rebased, aborted due to a rebase conflict with the conflicted paths, or skipped because no upstream exists); pre-rebase SHA only when a rebase ran
- validation result (Phase 4 gates, and status/diff review or tests after a successful sync)
- unrelated gate failures ignored under Phase 4's rule (gate, command, exit code), if any
- push result (or reason push was skipped)
- other commits published (in the pre-push `@{u}..HEAD` list, not created by this run), if any
- remaining uncommitted changes (and whether Phase 6's check found any unstaged file temporarily missing)
- stop conditions triggered, with explanation; warnings

Prohibited behavior: see `SKILL.md` Core rules.
