## Goal
Implement `tools/manage_workitem_stage.py`, a CLI with subcommands `close-issue`,
`close-plan`, and `close-implementation` that performs the archival `git mv` for each
workflow stage transition, blocking `close-implementation` when the target's
Execution Status table still has a `Pending` row unless overridden (REQ-001, REQ-002,
REQ-003, REQ-004, REQ-005, REQ-006).

## Scope
- In scope: `close-issue`/`close-plan`/`close-implementation` subcommands; a shared
  move helper (`git mv` semantics via GitPython); Execution Status table parsing and
  `Pending`-row block for `close-implementation`; `--force`/`--reason` override;
  clear success/failure result printing with correct exit codes.
- Out of scope: judging whether a plan/issue is actually ready to close (stays with
  the invoking agent/human); `close-plan` verifying a downstream implementation
  procedure already references it (deferred, UNK-01); editing the substantive
  content of any moved file beyond the move itself; any approval prompt on the move.

## Assumptions
- The three `done/` destination directories (`issues/done/`, `plans/done/`,
  `implementations/done/`) already exist and do not need to be created by this
  tool.
- `close-issue`/`close-plan` do not parse any file content — only
  `close-implementation` does (only implementation procedures carry an Execution
  Status table under this Plan's scope).
- GitPython's move API (`Repo.git.mv(src, dst)` or equivalent) is sufficient to
  perform a `git mv` that Git records as a rename; the exact call is UNK-02,
  resolved during this implementation.

## Design decisions
- One shared move helper (source/destination existence checks, `git mv`
  invocation, structured success/failure result) used by all three subcommands —
  `close-issue` and `close-plan` are otherwise identical apart from their
  directory pair; `close-implementation` layers the Execution Status
  parse-and-block check on top of the same helper before invoking it.
- Execution Status parsing uses a simple line-based Markdown table parser (row
  splitting on `|`), not a general Markdown parser dependency — consistent with
  this repo's existing `tools/` scripts, none of which pull in a
  Markdown-table-parsing library for this kind of check.
- The move itself uses GitPython (`import git`, lazily, matching
  `scripts/shared/git_helper.py`'s `get_repo_info()` pattern: `import git` inside
  the function body, then `git.Repo(path, search_parent_directories=True)`), not
  `subprocess`-invoked `git mv` — keeps the dependency surface consistent with the
  rest of the repo's git-touching code.

## Alternatives considered
- `subprocess`-invoked `git mv` CLI call instead of GitPython: not chosen as the
  primary approach — the Plan's Design section specifies GitPython for
  consistency with `scripts/shared/git_helper.py`'s existing pattern; a
  subprocess fallback remains available if GitPython's move API proves
  insufficient during this implementation (per the Plan's Scope), to be recorded
  here if that fallback is actually used.
- `close-plan` verifying a downstream implementation-procedure reference before
  allowing the move: rejected for this Plan's scope (UNK-01) — deferred to avoid
  duplicating validation logic that may belong in the separately-tracked
  traceability-checker tool instead.

## Implementation
### Target file
`tools/manage_workitem_stage.py`

### Procedure
1. Parse CLI arguments via `argparse` with subparsers: `close-issue <issue-path>`,
   `close-plan <plan-path>`, `close-implementation <implementation-path>
   [--force] [--reason "..."]`.
2. Shared move helper: given a source path and its `done/` sibling directory,
   compute the destination path; refuse (print error, exit non-zero, no move) if
   the source does not exist or the destination already exists; otherwise perform
   the `git mv`-equivalent move via GitPython and report success with the
   resulting path.
3. `close-issue`/`close-plan`: call the shared move helper directly against
   `issues/{file}.md` -> `issues/done/{file}.md` (or the `plans/` equivalent). No
   file-content parsing.
4. `close-implementation`: before calling the shared move helper, read the target
   file's `### Execution Status` table (per `templates/execution-status.md`'s
   `Step | Description | Status | Started | Completed | Notes` columns) and check
   every row's `Status` column; if any row is `Pending`, refuse (print which
   row(s) are blocking by `Step`/`Description`, exit non-zero, no move) unless
   both `--force` and `--reason` were supplied, in which case proceed and include
   the supplied reason in the printed result.
5. All subcommands exit `0` on success, non-zero on any refusal or `git mv`
   failure.

### Method
Single-entry-point CLI (`main()`) using `argparse` with `subparsers.add_parser()`
per subcommand, mirroring `tools/manage_frontmatter.py`'s
`subparsers = parser.add_subparsers(dest="subcommand")` / `add_parser =
subparsers.add_parser(...)` structure. Each subcommand backed by its own `cmd_*`
function (`cmd_close_issue`, `cmd_close_plan`, `cmd_close_implementation`)
importable for direct unit testing, matching
`tests/tools/test_manage_frontmatter.py`'s `from tools.manage_frontmatter import
cmd_add_missing` precedent. Git move via lazy `import git` inside the move
helper, matching `scripts/shared/git_helper.py`'s `get_repo_info()` — `import git`
and `import git.exc` inside the function body, then `git.Repo(path,
search_parent_directories=True)`.

### Details
- Shared move helper signature: takes source path, destination directory, and
  returns a structured result (success/failure, resulting path or error reason) —
  no printing inside the helper itself; each `cmd_*` function does the printing,
  so tests can assert on the structured result directly without capturing stdout.
- Execution Status table parser: locate the `### Execution Status` heading, then
  parse the next Markdown table (skip the header row and the `|---|` separator
  row), extracting each data row's `Status` column value; a row with `Status ==
  "Pending"` is blocking.
- `--reason` is required alongside `--force` (both must be present to override) —
  `--force` alone without `--reason` is itself a refusal (per REQ-004's exact
  phrasing: "both `--force` and a required `--reason`").
- Before moving, check the source file's git status (per the Plan's Risks
  mitigation) — if the file has uncommitted local modifications, surface a clear
  error via the shared move helper's failure result rather than silently
  proceeding with an ambiguous git-mv outcome.

## Compatibility considerations
New, standalone file; no existing caller (Blast Radius: new file, no prior
history, confirmed in the Plan's Affected areas). Not imported by `scripts/`, so
the `skills/DESIGN.md` import-layer contract does not apply (`tools/` is a
separate scope per `routing.md` Tools section).

## Security considerations
- The `git mv` operation only ever targets paths explicitly passed as CLI
  arguments by the invoking caller — no path is derived from unvalidated external
  input beyond the CLI's own arguments.
- GitPython calls use its object API (`Repo.git.mv(...)` or equivalent), not a
  raw shell string — no `shell=True` subprocess invocation.
- `uv run bandit -r tools/manage_workitem_stage.py -c pyproject.toml` must report
  no new high/medium findings; the repo's existing `tools/` bandit baseline is 0
  issues.

## Rollback considerations
New file only; rollback is deleting `tools/manage_workitem_stage.py`. The tool's
own moves are themselves Git renames — any move it performs can be reverted with
a normal `git mv` back, or `git revert`/`git reset` on the commit that recorded
it, same as any other Git rename.

## Validation plan
- `uv run pytest tests/tools/test_manage_workitem_stage.py -v` — once created
  (see `implementations/20260901-114646_03_tests_tools_test_manage_workitem_stage_py.md`),
  all cases (3 successful moves, 1 blocked-Pending case, 1 forced-override case)
  must pass.
- `uv run ruff check tools/manage_workitem_stage.py`; `uv run mypy
  tools/manage_workitem_stage.py` — no new errors.
- `uv run bandit -r tools/manage_workitem_stage.py -c pyproject.toml` — no new
  findings.

## Completion criteria
- `tools/manage_workitem_stage.py` exists and implements all three subcommands.
- AC-1: `close-issue`/`close-plan` each correctly `git mv` the target file,
  preserving Git history, and refuse when source is missing or destination
  exists.
- AC-2: `close-implementation` refuses a `Pending`-row move unless `--force
  --reason` is given, naming the blocking row(s).
- AC-3: a forced move proceeds and the printed result includes the resulting
  path and the supplied reason.

## Out of scope
- Deciding whether a plan/issue is actually ready to close.
- `close-plan` verifying a downstream implementation-procedure reference (UNK-01).
- Editing the substantive content of any file being moved beyond the move
  itself.
- A human-approval prompt on the move.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by `implementations/20260901-114646_03_tests_tools_test_manage_workitem_stage_py.md` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Covered by `implementations/20260901-114646_02_tools_TOOL_DESCRIPTIONS_md.md` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006
- **Source issue**: `issues/20260831-194739_tool004_manage_workitem_stage_transitions.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-110946_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-114646
- **Related target files**: `tools/manage_workitem_stage.py`
