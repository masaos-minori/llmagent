## Goal
- Create `tools/fill_affected_areas.py`, a read-only tool that prints the mechanical columns of a Plan's `Affected areas` table for the Plan's target files, and writes them only with `--insert` (`REQ-001` to `REQ-005`: Change, Churn, Bus Factor, deploy impact, no-hang git calls; `REQ-007`: output equals the manual commands).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new module only. The tests are `tests/tools/test_fill_affected_areas.py` (separate document, because `tools/TOOL_DESCRIPTIONS.md` also names it in `Related Tests`, so it is not a companion), the inventory row, and the skill references are separate documents.
- Out of scope: any change to `tools/amend_plan.py`, `.mailmap`, gate definitions.

## Assumptions
- The Plan's frozen rows are the source of the file list; `Blast Radius` is never computed.
- Bus factor rule (user decision 2026-11-27, Plan UNK-01): lowercased `%an`, top share strictly above 70 percent is `High`.
- `deploy/deploy.sh` is the authority for the deploy mapping; the rsync lines it relies on (`scripts/`, `tests/`, `docs/`, `registry/`) are recorded as constants and asserted by a test.
- The module must stay at or below 24576 B: `tools/` is covered by the `check-module-size-tools` hook (`tools/check_module_size.py --scripts-dir tools`), and a new file has no baseline entry. If the draft grows past about 20000 B, move the git and deploy helpers to `tools/_affected_areas_git.py` and raise it as a Plan amendment (fallout class) before continuing.
- Plan step 3 (verification on three Plans) is carried out by `code-implementation` from the Plan, not by this document.

## Design decisions
- Reuse `Refusal`, `_section`, `_table`, `_first_cell`, `_row` from `tools/amend_plan.py` (`import amend_plan`; `tests/conftest.py` puts `tools/` on `sys.path`, and the CLI runs with its own directory first on `sys.path`). Repository evidence: `_row` at `tools/amend_plan.py:109`, `_first_cell` at 113, `_section` at 125, `_table` at 143, `Refusal` at 76.
- Pure helpers are separate from IO so they unit-test without git: `change_kind(responsibility)`, `bus_factor(authors)`, `deploy_impact(path, change, deploy_text)`, `size_note(path, root)`, and `git_log(root, args)`, the only function that runs git.
- Write path: build the new Plan text in memory (only the `## Affected areas` table lines change), then `atomic_write_text`, or `print_dry_run` for `--dry-run`.

## Alternatives considered
- Copy the parsing helpers instead of importing them: rejected, it duplicates about 40 lines that the Issue says to reuse.
- Author-count bus factor or `.mailmap`: rejected by the user (UNK-01); the printed percentage lets the author judge the two-name case (UNK-02).
- `git shortlog -sn`: rejected, it reads standard input without a revision; `git log --format=%an HEAD -- <file>` is used instead.

## Implementation
### Target file
`tools/fill_affected_areas.py` (new)

### Procedure
1. Module docstring (usage, exit codes 0 success, 1 refusal or no target rows, 2 usage error), `from __future__ import annotations`, constants: `CHURN_SINCE = "30.days"`, `HIGH_SHARE = 0.70`, `PLACEHOLDER = "TODO: author judgment"`, `NEW = "N/A (new)"`, `RSYNCED_DIRS = ("scripts/", "tests/", "docs/", "registry/")`, `CREATE_HINTS = ("create", "new", "generated")`, `DELETE_HINTS = ("delete", "remove")`.
2. Parse: read the Plan, find `## Implementation Target Files` with `_section`/`_table`, take for each data row the first cell as the path (`_first_cell`) and the second cell as `Change Responsibility`, skipping placeholder cells; zero rows raises `Refusal`.
3. Per target compute the six cells (functions below), print the markdown rows to standard output, then a `Notes` block with one size line per `scripts/**/*.py` target.
4. `--insert`: locate `## Affected areas` and its table, keep every existing row whose first cell is a target path unchanged (its `Blast Radius` is preserved and its mechanical cells are replaced by the computed ones), append a row for each target missing from the table (replacing a placeholder row), leave all other lines untouched, then write atomically; `--dry-run` prints the diff and writes nothing. Without `--insert` the Plan is never opened for writing.
5. `main(argv: list[str] | None = None) -> int` with `argparse` (`plan`, `--insert`, `--root`, `--since` default `30.days`, `add_dry_run_argument`), and the `__main__` block calls `sys.exit(main())`.

### Method
- `change_kind(responsibility)`: lowercase the text; `Create` if any create hint appears, else `Delete` if any delete hint appears, else `Modify` (create wins when both appear, matching `tools/audit_plan_target_paths.py:CREATE_HINTS`).
- `git_log(root, args)`: `subprocess.run(["git", "-C", str(root), "log", *args], capture_output=True, text=True, stdin=subprocess.DEVNULL, check=False)`; a non-zero return code raises `Refusal` carrying stderr. Every call names `HEAD` before `--` (`REQ-005`). Mark the call `# nosec B603 — fixed argv, no shell`.
- Churn: `len(git_log(root, ["--since=" + since, "--format=%H", "HEAD", "--", path]).split())`.
- `bus_factor(names)`: `Counter(n.lower() for n in names)`; empty means `N/A: no history`; share = top count / total; `High ({pct}% single author)` when share is above `HIGH_SHARE` (new), else `Low ({pct}% top author)`, with `pct = round(share * 100)`. Names come from `git_log(root, ["--format=%an", "HEAD", "--", path]).splitlines()`.
- `Create` rows: `Churn` and `Bus Factor` are `N/A (new)` without running git. `Delete` rows and `Modify` rows use history; a `Modify` row with zero commits prints `N/A: no history`.
- `deploy_impact(path, change, deploy_text)`: `config/*.toml` with `Create` gives `add cp line`, with `Delete` gives `remove cp line`, with `Modify` scans `deploy_text` (new) lines for `config/<name>` and gives `existing cp line at deploy/deploy.sh:{N}; no change needed`, else `Needs review: no cp line`; a path starting with an `RSYNCED_DIRS` (new) entry gives `not applicable (rsynced)`; any other path gives `not applicable (not rsynced)`. `deploy_text` (new) is read once from `<root>/deploy/deploy.sh`; a missing file raises `Refusal`.
- `size_note(path, root)`: for `scripts/**/*.py` only, `{path}: {bytes} B, headroom {24576 - bytes} B` using `check_module_size.DEFAULT_LIMIT`; a file that does not exist yet prints `new file`.

### Details
- Output row format: `| \`path\` | Change | TODO: author judgment | churn | bus factor | deploy |`, matching `templates/plan.md`.
- A cell never contains an unescaped `|` (use `_row`, which does not escape; paths and generated values contain none).
- Type annotations are required on every function (`mypy` covers `tools/`).

## Compatibility considerations
- New file, no caller. Importing private names of `tools/amend_plan.py` couples the two tools; `tests/tools/test_fill_affected_areas.py` imports both so a rename there fails the tests at once.
- Output wording of the bus factor and deploy cells follows existing Plans (`High (...)`, `not applicable (rsynced)`).

## Security considerations
- `subprocess` is used with a fixed argument list and no shell; the only variable inputs are repository paths read from the Plan, passed after `--` so they cannot be read as options. Standard input is closed.
- `--insert` writes only the Plan file given on the command line, through `tools/_atomic_write.py`.

## Rollback considerations
- Revert the commit. The tool is not wired into any gate or hook, so nothing else changes.

## Validation plan
- `uv run ruff format tools/fill_affected_areas.py` then `uv run ruff check tools/fill_affected_areas.py --fix`, then confirm `uv run ruff check tools/fill_affected_areas.py`.
- `uv run mypy tools/fill_affected_areas.py`; `uv run bandit tools/fill_affected_areas.py`.
- `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` (size gate).
- Smoke test on live Plans: `uv run python tools/fill_affected_areas.py plans/20261126-152931_mcpci001_cicd-credential-config-contract.md` and compare each Churn and Bus Factor with the manual commands.

## Completion criteria
- The tool prints six-column rows for a live Plan and a `Notes` block for `scripts/` targets; default run leaves the Plan byte-identical; `--insert` changes only `Affected areas`; no git call reads standard input; lint, type, bandit, and the size gate pass.

## Out of Scope
- Blast radius or dependency graphs; changes to `tools/amend_plan.py`; gate definitions or a `rules/tool-gates.md` row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tools/fill_affected_areas.py` per Procedure/Method/Details | Pending | — | — | |
| 2 | Run `tests/tools/test_fill_affected_areas.py` (written by its own procedure) | Pending | — | — | Needs the procedure for seq 02 |
| 3 | Run ruff, mypy, bandit, and the tools size gate on the file | Pending | — | — | |
| 4 | Smoke test on three live Plans and compare with the manual commands (Plan `REQ-007`); stop and report on a disagreement | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (rows and Change), `REQ-002` (churn, bus factor), `REQ-003` (deploy impact, size note), `REQ-004` (read-only, `--insert`), `REQ-005` (stdin closed), `REQ-007` (equality check)
- **Source issue**: issues/20261126-151440_wfeff005_affected-areas-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-085326_wfeff005_affected-areas-tool.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-090100
- **Related target files**: `tools/fill_affected_areas.py`
