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
| `git pull --ff-only` | Pull | safe remote sync; abort on diverge |
| `git diff --check` | Resolve Conflicts | detect remaining conflict markers |
| `git push` | Push | push to remote after approval |
| `git push --set-upstream origin <branch>` | Push | set upstream if missing (suggestion only) |

Forbidden commands — never run:
`reset --hard`, `clean -fd`, `clean -fdx`, `checkout -- .`, `restore .`, `restore --staged .`,
`rebase`, `commit --amend`, `merge`, `merge --abort`,
`pull` (without `--ff-only`), `pull --rebase`, `push --force`, `push --force-with-lease`, `push -f`

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

Stop if commit fails. Do not bypass Git hooks (`--no-verify`).

---

## Phase 7: Pull

Before push, always run:

```bash
git pull --ff-only
```

If pull succeeds with no conflicts, continue to Phase 10.
If pull produces conflict markers, continue to Phase 8.

Stop if:
- Fast-forward is not possible (diverged history). Report: `Fast-forward pull failed. No push was performed.`
- Pull exits with an error unrelated to conflicts.

Do not run `git pull`, `git pull --rebase`, `git merge`, or `git rebase`.

---

## Phase 8: Resolve Conflicts

Resolve conflicts only when ALL conditions hold:

- File is a text file (not binary, not lock file, not migration file).
- Conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) are visible.
- The correct result is clear from context without product decisions.
- The change is small (fewer than ~30 conflicted lines).
- Validation can be run after the fix.

Inspect conflict state:

```bash
git status --short
git diff --name-only
```

For each conflicted file:

1. Read both sides (`HEAD` and incoming).
2. Keep the correct code; combine only when both sides are needed.
3. Remove all conflict markers.
4. Preserve formatting and indentation.
5. Do not remove unrelated code or invent behavior.

Validate after editing:

```bash
git diff --check
git diff --stat
git status --short
```

If Python files are involved, run:

```bash
uv run pytest tests/ -x -q
```

Stop conflict resolution if:
- File is binary
- Conflict is large or spans logical sections
- File is a lock file and the correct version is unclear
- File is a migration and ordering is unclear
- File contains security, authentication, or data deletion logic
- File affects a public API contract
- The correct resolution is not obvious
- Tests fail
- Validation cannot be run

When stopping, report:
- conflicted files
- unclear points
- suggested next action for the user

---

## Phase 9: Commit Conflict Resolution

Stage only resolved files:

```bash
git add <resolved-files>
git diff --cached --stat
git diff --cached --name-only
```

Commit:

```bash
git commit -m "fix: resolve merge conflicts"
```

Use a more specific message when appropriate:

```bash
git commit -m "fix: resolve workflow documentation conflict"
```

---

## Phase 10: Ask Before Push

Unless the user already approved push in this session, ask:

> Commit complete. Pull succeeded. Approve `git push`?

Do not push without explicit approval.

---

## Phase 11: Push

```bash
git push
```

If upstream is missing, stop. Report:

> Current branch has no upstream branch.
> Suggested command: `git push --set-upstream origin <branch>`

Do not run the suggestion without user approval.

---

## Phase 12: Report

Report:
- branch
- staged files
- commit message
- pull result (fast-forward, conflict resolved, or failed)
- conflict files and resolution summary (if applicable)
- validation result (if tests were run)
- push result
- remaining uncommitted changes
- warnings

---

## Output expectations

- branch and commit SHA
- list of committed files
- pull result and conflict summary
- push result or reason push was skipped
- any stop conditions triggered with explanation

---

## Prohibited behavior

- do not run destructive git commands
- do not force push under any circumstances
- do not rebase or amend published commits
- do not push without user approval
- do not resolve conflicts that require business or product decisions
- do not stage files unrelated to the task
- do not invent commit messages from unstaged changes
