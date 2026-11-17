## Goal
- Make `tools/complete_doc_procedure.py` archive a docs-wave procedure through the sanctioned archival function (a staged `git mv`) and refuse, before writing or moving anything, a procedure that still holds an unfinished row, so the tool no longer reopens the failure that the archive-only-after-execution rule closed.

## Priority
Medium

## Scope
- **In-Scope**: (1) replace the plain `rename` with `move_to_done` of `tools/manage_workitem_stage.py`; (2) refuse the archive, with exit `1` and nothing written, moved, or edited, when any Execution Status row is `Pending`, `In Progress`, or `Blocked` after the tool's own update; (3) run the archive refusals (unfinished rows, destination exists, memo line missing) before the first write; (4) refuse a procedure that is not directly under `implementations/`; (5) tests and the tool description.
- **Out-of-Scope**: changing the refusal rule of `close-implementation` (it still refuses `Pending` rows only); retiring the tool; moving the memo workflow out of the tool; making the memo path configurable; rewriting archived procedures; the status value the tool writes and its dry-run option (the prerequisite Plan).
- **Dependencies**: this Plan edits the same file and test module as the status-vocabulary Plan and builds on its test module, its dry run, and its function split, so it lands after its phases 1 and 3 (structured lines below). `tools/TOOL_DESCRIPTIONS.md` is also edited by the other tooling Plans of this batch; the rows differ and the order is settled at implementation time (UNK-03).
  - **Depends on**: plans/20261117-124614_wftool002_status-vocabulary-unify.md | phase 1 | creates `tests/tools/test_complete_doc_procedure.py`, which this Plan extends
  - **Depends on**: plans/20261117-124614_wftool002_status-vocabulary-unify.md | phase 3 | gives the tool its `main(argv)` entry point, `--dry-run`, atomic writes, and the split of `main`, which this Plan changes

## Background
Filed as a follow-up of the status-vocabulary Plan (its UNK-02). The archival guards it sits beside were introduced when `close-implementation` was made to refuse a procedure with a `Pending` row and the archived-status check was added to report a procedure archived with an unfinished row.

## Problem
After the row update the tool calls `proc.rename(DONE_DIR / proc.name)` (`Explicit in code`, `tools/complete_doc_procedure.py` step 3). Only a row whose Status is exactly `Pending` is rewritten, so an `In Progress` or `Blocked` row stays and the procedure is archived anyway; the archived-status check reports it only afterwards (`Explicit in code`). `close-implementation` is the sanctioned wrapper that stages a `git mv`, but it refuses only `Pending` rows (`pending_rows`), so it would not stop an `In Progress` or `Blocked` row either (`Explicit in code`, `cmd_close_implementation`). A plain rename of a tracked file leaves the old path as an unstaged deletion and the new path untracked until staged, while the commit workflow expects archival renames to be staged already (`Strongly implied by code`, `skills/git-commit-and-sync/workflow.md` Phase 2). The tool is in use: the status-vocabulary Plan counted 90 archived procedures carrying its stamp (`Operationally observed` there, not re-measured here).

Found while checking the issue's claims against the code, beyond what it states:
- The tool writes the status rows before it checks the archive destination and the memo line, so a refused archive (destination exists, or `no memo line matched`) leaves the procedure already rewritten (`Explicit in code`). The refusals of REQ-002 therefore have to run before the first write to mean "nothing changed".
- The destination is the module constant `DONE_DIR`, whatever directory the procedure came from, while `move_to_done` derives it from `source.parent / "done"`; a procedure outside `implementations/` would change behavior silently, so it must be refused (`Explicit in code`).
- `move_to_done` stages the uncommitted source before the move (so the rewritten content travels in the staged rename) and asks `origin` whether the destination already exists there; a fetch failure degrades to a no-op (`Explicit in code`, module docstring and `move_to_done`).

## Reason for Change
- The tool reopens, for `In Progress` and `Blocked` rows, the failure the archive-only-after-execution rule closed: a procedure with unfinished work can enter `implementations/done/` and hide it. No archival step refuses those rows.
- A non-staged move can be committed in part, leaving an added file and a deleted file in different commits.
- The memo workflow is live (the tool also removes the procedure's line from the batch memo), so the archive step should not be dropped from it. Nothing makes the change urgent beyond the next batch run.

## Implementation Intent
- Archival goes through `move_to_done(source, kind="implementation procedure", stage_only=True)`, called as a function. Calling the function rather than the command keeps one process, reuses its destination, repository, and remote checks, and lets the test use a temporary repository.
- The tool checks everything that can refuse before it writes anything: the procedure's location, the status table, the unfinished rows after the planned update, the destination, and the memo line. It then writes the procedure, moves it, and removes the memo line last, so a failing move never leaves the memo without its line.
- The unfinished set is `Pending`, `In Progress`, and `Blocked`, the same set the sanctioned rewrite and the archived-status check use. A refusal applies when the tool archives; `--no-archive` keeps updating rows without the refusal.
- The memo line removal and the Verification Findings insertion keep their behavior.

## Requirements
- `REQ-001`: With archival on, the tool moves the procedure with `move_to_done` and no other method; the move is staged as a Git rename carrying the rewritten content; the existing refusal when the destination exists is kept.
- `REQ-002`: With archival on, the tool exits `1` and lists the rows when any row is `Pending`, `In Progress`, or `Blocked` after its own update; before the first write it also refuses a destination that exists and a memo line that is missing; on any of these refusals the procedure, the memo, and `implementations/done/` are unchanged.
- `REQ-003`: A procedure that is not directly under `implementations/` is a usage error (exit `2`) with nothing changed.
- `REQ-004`: `--dry-run` runs the same refusals and reports the same exit code, and moves, writes, and edits nothing.
- `REQ-005`: The memo line is removed after a successful move and the Verification Findings table is inserted as before.
- `REQ-006`: Tests cover an unfinished row blocking the move, a finished procedure moved and staged as a rename, the dry run, the all-or-nothing refusals, the location refusal, and the memo order, using a temporary Git repository.
- `REQ-007`: `tools/TOOL_DESCRIPTIONS.md` states the sanctioned archival, the unfinished-row refusal, and the exit codes.
- `REQ-008`: The changed tool keeps the `tools/` size gate, adds no function of complexity grade C or worse, and passes ruff, mypy, and bandit.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/complete_doc_procedure.py` | Pre-validate, archive through `move_to_done`, remove the memo line last, refuse unfinished rows | Archives with a plain `proc.rename`, updates only `Pending` rows, writes before it checks the destination and the memo line | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-008 / AC-1, AC-2, AC-3, AC-4, AC-5, AC-8 | `proc.rename(DONE_DIR / proc.name)` and the `cells[2] != "Pending"` skip; 5095 B of 24576 B; not in the size baseline (checked in Step 3) | `tests/tools/test_complete_doc_procedure.py` | Verified |
| `tests/tools/test_complete_doc_procedure.py` | Add the archival, refusal, dry-run, and order tests | New file at the time of this Plan: the prerequisite Plan's phase 1 creates it; if it is absent when this Plan starts, create it with the fixtures first. The directory `tests/tools/` exists | REQ-006 / AC-6 | No test references the tool today; `tests/tools/test_manage_workitem_stage.py` builds a temporary repository with `git.Repo.init` and a committed `.gitkeep` (checked in Step 3) | The file itself | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | State the archival path, the refusal, and the exit codes | Rows 108 and 255 describe a rename-style archive and no unfinished-row refusal | REQ-007 / AC-7 | The two rows for `complete_doc_procedure.py` (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/manage_workitem_stage.py` | `move_to_done` (staging, destination, remote checks) and `cmd_close_implementation` (the sanctioned refusal) | `tools/complete_doc_procedure.py` / REQ-001 |
| `tools/_workitem_status_table.py` | `parse_execution_status_rows` and the unfinished-status tuple the refusal reuses | `tools/complete_doc_procedure.py` / REQ-002 |
| `tests/tools/test_manage_workitem_stage.py` | Temporary-repository fixture style to follow | `tests/tools/test_complete_doc_procedure.py` / REQ-006 |
| `skills/git-commit-and-sync/workflow.md` | Phase 2 expectation that archival renames are already staged | `tools/complete_doc_procedure.py` / REQ-001 |
| `memo3.md` | The default memo whose line the tool removes, to model the memo fixture | `tests/tools/test_complete_doc_procedure.py` / REQ-005 |

## Acceptance Criteria
- AC-1 (REQ-001): A finished procedure is archived through the sanctioned function and `git status` shows a staged rename with the rewritten content; no `rename` call remains in the tool (test; `rg -n "\.rename\(" tools/complete_doc_procedure.py` is empty).
- AC-2 (REQ-002): A procedure with an `In Progress` or `Blocked` row is not archived, the tool exits `1` naming the rows, and the procedure file, the memo, and `implementations/done/` are byte-identical afterwards (tests); an existing destination and a missing memo line refuse the same way (tests).
- AC-3 (REQ-003): A procedure outside `implementations/` exits `2` with nothing changed (test).
- AC-4 (REQ-004): `--dry-run` returns the same exit code as the real run for each refusal and for success, and leaves the procedure, the memo, and `implementations/done/` unchanged (tests).
- AC-5 (REQ-005): After a successful move the memo no longer holds the line and the Verification Findings table is present (tests).
- AC-6 (REQ-006): The test module covers each behavior above and passes with a temporary Git repository.
- AC-7 (REQ-007): `tools/check_tool_descriptions_sync.py` passes and the rows match the tool.
- AC-8 (REQ-008): The `tools/` size gate passes, `radon cc tools/complete_doc_procedure.py -s -n C` reports nothing, and ruff, mypy, and bandit are clean.

## Tests
- `tests/tools/test_complete_doc_procedure.py`: unfinished row (`In Progress`, `Blocked`) blocks the archive; a finished procedure is moved and the rename is staged; `--no-archive` updates rows without the refusal; dry run; destination exists; memo line missing; location refusal; memo line removed after the move; Verification Findings insertion (REQ-001 to REQ-006). The fixture commits the procedure before the run so that the move shows as a rename.
- Smoke run: `--dry-run` on a copy of a real procedure in a scratch clone (REQ-004).

## Documentation Impact
N/A for `docs/*.md`: no file under `docs/` changes. The tool description rows change (REQ-007).

## Assumptions
- The memo workflow stays inside the tool and the memo path stays the default `memo3.md` (the issue's two open questions are unchanged; UNK-02).
- Writing the procedure only after all refusals changes one observable behavior: a refused archive no longer leaves the status rows rewritten. This follows from the issue's "no move" intent and is recorded here because the issue does not state it; the alternative is to keep writing first.
- Calling `move_to_done` with `stage_only=True` is enough: it stages the rewritten source and then moves it; the tool never commits.
- The refusal reuses the existing unfinished-status tuple of `tools/_workitem_status_table.py` by import (a sibling helper already imports a private name from that module), so that module is not a target of this Plan. If the prerequisite Plans rename it, the procedure reads the then-current name.
- Overlap with the status-vocabulary Plan on the tool and its test is a sequencing dependency, declared above. Overlap on `tools/TOOL_DESCRIPTIONS.md` is row-level: this Plan edits only the two `complete_doc_procedure.py` rows.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `close-implementation` itself should also refuse `In Progress` and `Blocked` rows | A maintainer decision; this Plan adds the check to the docs-wave tool only | File a separate issue if the maintainer wants the shared rule changed | False |
| UNK-02 | Whether the memo workflow should keep archiving inside this tool, and whether the memo path should be configurable | The owner of the batch memo has not decided | Keep the current behavior; revisit only if the owner asks | False |
| UNK-03 | Final names after the prerequisite Plan splits `main`, and order against the other Plans editing `tools/TOOL_DESCRIPTIONS.md` | The tool's function layout after the prerequisite phases | Read the tool and the shared rows at implementation time, after the prerequisite phases | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/complete_doc_procedure.py` | Modify | Low: no importer; run by hand | N/A: Path A | N/A: Path A | not applicable (rsynced) |
| `tests/tools/test_complete_doc_procedure.py` | Modify | Low | N/A: Path A | N/A: Path A | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low: documentation rows read by the sync checker | N/A: Path A | N/A: Path A | not applicable (rsynced) |

## Design
**Classification**: Path A (three target rows; a command-line tool with no importer, no schema, and no runtime interface). Step 3's direct verification ran once; the validation baseline ran once.
- **Direct verification**: `tools/complete_doc_procedure.py` imports only the standard library; nothing imports it, and only `tools/TOOL_DESCRIPTIONS.md` names it (`rg`). `move_to_done` and `parse_execution_status_rows` exist as described (checked in Step 3).
- **Decision 1, function or command**: call `move_to_done` as a function. Alternative: run `manage_workitem_stage.py close-implementation` as a subprocess. Rejected because the command's `Pending`-only refusal duplicates a weaker check, its output would have to be parsed, and the test could not use one repository.
- **Decision 2, order**: refusals first, then write, then move, then memo. Alternative: keep write, memo, move. Rejected because a refusal after the first write leaves a half-applied change, and a failed move after the memo edit loses the line.
- **Decision 3, refusal scope**: only when archiving, and only for the three unfinished statuses; out-of-vocabulary values are the checker's concern (the status-value Plan).
- **Baseline**: `radon` grades `main` as E (33), which the prerequisite Plan splits before this Plan starts; `vulture` and `bandit` findings under `scripts/` are pre-existing and outside the targets; `diff-cover` has no baseline because the tree equals `master`.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Tests first**
   - [ ] Add the refusal, archival, dry-run, location, and memo-order tests; the unfinished-row, staged-rename, all-or-nothing, and location tests fail first (REQ-001 to REQ-006; `tests/tools/test_complete_doc_procedure.py`)
2. **Phase 2: Refusals before writes**
   - [ ] Compute the planned update in memory, refuse unfinished rows, an existing destination, and a missing memo line, and refuse a location outside `implementations/`, all before the first write (REQ-002, REQ-003, REQ-004; `tools/complete_doc_procedure.py`)
3. **Phase 3: Sanctioned archival**
   - [ ] Replace the plain rename with `move_to_done`, and remove the memo line after the move (REQ-001, REQ-005; `tools/complete_doc_procedure.py`)
4. **Phase 4: Documentation**
   - [ ] Update the two tool rows (REQ-007; `tools/TOOL_DESCRIPTIONS.md`)
5. **Phase 5: Verification** (no deploy step: no `scripts/` or `config/` file changes)
   - [ ] Run the validation sequence of `rules/toolchain.md` for the changed tool, the size gate, and `tools/check_tool_descriptions_sync.py`; smoke-run `--dry-run` on a copy of a real procedure (REQ-001 to REQ-008; all target files)

### Release units
N/A: no release unit; each phase passes validation alone when applied in order.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/complete_doc_procedure.py` | Unit tests with a temporary Git repository; dry-run smoke on a copy | `uv run pytest tests/tools/test_complete_doc_procedure.py -v`; `uv run radon cc tools/complete_doc_procedure.py -s -n C`; `uv run bandit tools/complete_doc_procedure.py` | Tests pass; radon reports nothing; bandit clean |
| `tests/tools/test_complete_doc_procedure.py` | Self; lint and types | `uv run ruff format tools tests/tools`; `uv run ruff check tools tests/tools`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | Clean |
| `tools/TOOL_DESCRIPTIONS.md` | Doc consistency | `uv run python tools/check_tool_descriptions_sync.py` | No finding |
| All target files | Size gate and rename evidence | `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`; `rg -n "\.rename\(" tools/complete_doc_procedure.py` | Gate passes; no `rename` call |

## Risks
- **Risk**: The prerequisite split changes the function layout this Plan edits → **Mitigation**: the Plan depends on that phase and reads the then-current file at implementation time (UNK-03).
- **Risk**: `move_to_done` asks `origin` about the destination and may fail or stall on a network problem → **Mitigation**: its fetch failure degrades to a no-op by design, and tests use a repository without a remote.
- **Risk**: A refused run no longer rewrites rows, which an operator might rely on → **Mitigation**: the behavior change is stated in Assumptions and in the tool description, and the old behavior left a half-applied state.
- **Risk**: The staged rename carries a rewritten file whose mode or encoding changed → **Mitigation**: the test compares the staged content with the rewritten content.
- **Risk**: `tools/TOOL_DESCRIPTIONS.md` has very high churn → **Mitigation**: change only the two rows and settle the order per UNK-03.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first: refusals, staged rename, dry run, location, memo order | Pending | — | — | |
| 2 | Refusals before the first write | Pending | — | — | |
| 3 | Archive through the sanctioned function; memo line last | Pending | — | — | |
| 4 | Documentation: the two tool rows | Pending | — | — | |
| 5 | Verification: validation sequence, size gate, dry-run smoke | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-132202_wftoolfu002_doc-procedure-archival.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-134130
- **Related target files**: `tools/complete_doc_procedure.py`; `tests/tools/test_complete_doc_procedure.py`; `tools/TOOL_DESCRIPTIONS.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent (sanctioned archival); Required Changes | `tools/complete_doc_procedure.py` | Phase 3 | AC-1 | staged-rename test; `rg` for `rename(` | Explicit in issue |
| REQ-002 | Required Changes (refuse unfinished rows); `Problem` evidence on write order | `tools/complete_doc_procedure.py` | Phase 2 | AC-2 | refusal and byte-identity tests | Derived from confirmed evidence |
| REQ-003 | `Problem` evidence on `DONE_DIR` versus `move_to_done` | `tools/complete_doc_procedure.py` | Phase 2 | AC-3 | location test | Derived from confirmed evidence |
| REQ-004 | Required Changes (a dry run moves nothing) | `tools/complete_doc_procedure.py` | Phase 2 | AC-4 | dry-run tests | Explicit in issue |
| REQ-005 | Implementation Intent (memo line removal unchanged) | `tools/complete_doc_procedure.py` | Phase 3 | AC-5 | memo-order and findings tests | Explicit in issue |
| REQ-006 | Required Changes (add tests) | `tests/tools/test_complete_doc_procedure.py` | Phase 1 | AC-6 | the test module | Explicit in issue |
| REQ-007 | Required Changes (update the tool description) | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-7 | `tools/check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-008 | Constraints (tool conventions, size gate) | `tools/complete_doc_procedure.py` | Phase 5 | AC-8 | ruff, mypy, bandit, radon, size gate | Explicit in issue |
