## Goal
- Make `tools/complete_doc_procedure.py` archive a docs-wave procedure through the sanctioned archival function (a staged `git mv`) and refuse, before writing or moving anything, a procedure that still holds an unfinished row, so the tool no longer reopens the failure that the archive-only-after-execution rule closed.

## Priority
Medium

## Scope
- **In-Scope**: (1) replace the write-then-`unlink` archival with `move_to_done` of `tools/manage_workitem_stage.py`; (2) refuse the archive, with exit `1` and nothing written, moved, or edited, when any Execution Status row is `Pending`, `In Progress`, or `Blocked` after the tool's own update; (3) run the new refusals before the first write — the destination-exists and memo-line refusals already run before the staged writes (verified in this cycle), so they stay where they are; (4) refuse a procedure that is not directly under `implementations/`; (5) tests and the tool description.
- **Out-of-Scope**: changing the refusal rule of `close-implementation` (it still refuses `Pending` rows only); retiring the tool; moving the memo workflow out of the tool; making the memo path configurable; rewriting archived procedures; the status value the tool writes and its dry-run option (the prerequisite Plan).
- **Dependencies**: this Plan edits the same file and test module as the status-vocabulary Plan and builds on its test module, its dry run, and its function split, so it lands after its phases 1 and 3 (structured lines below). `tools/TOOL_DESCRIPTIONS.md` is also edited by the other tooling Plans of this batch; the rows differ and the order is settled at implementation time (UNK-03).
  - **Depends on**: plans/done/20261117-124614_wftool002_status-vocabulary-unify.md | phase 1 | creates `tests/tools/test_complete_doc_procedure.py`, which this Plan extends (satisfied: the test module exists at 16406 B, re-verified 20261118)
  - **Depends on**: plans/done/20261117-124614_wftool002_status-vocabulary-unify.md | phase 3 | gives the tool its `main(argv)` entry point, `--dry-run`, atomic writes, and the split of `main`, which this Plan changes (satisfied: all five of that Plan's steps are `Completed 20261117-212447` and it is archived, re-verified 20261118)

## Background
Filed as a follow-up of the status-vocabulary Plan (its UNK-02). The archival guards it sits beside were introduced when `close-implementation` was made to refuse a procedure with a `Pending` row and the archived-status check was added to report a procedure archived with an unfinished row.

## Problem
After the row update the tool writes the archive copy with `stage_write(dest, new_text)` and then calls `opts.proc.unlink()` (`Explicit in code`, re-verified 20261118; the plain `proc.rename` the issue names was replaced by the prerequisite Plan's phase 3). Only a row whose Status is exactly `Pending` is rewritten, so an `In Progress` or `Blocked` row stays and the procedure is archived anyway; the archived-status check reports it only afterwards (`Explicit in code`). `close-implementation` is the sanctioned wrapper that stages a `git mv`, but it refuses only `Pending` rows (`pending_rows`), so it would not stop an `In Progress` or `Blocked` row either (`Explicit in code`, `cmd_close_implementation`). Write-then-`unlink` of a tracked file leaves the new path untracked and the old path as an unstaged deletion, exactly like the plain rename did, while the commit workflow expects archival renames to be staged already (`Explicit in code` for the mechanism; `Strongly implied by code`, `skills/git-commit-and-sync/workflow.md` Phase 2). The tool is in use (`Operationally observed`, re-measured 20261118 with `parse_execution_status_rows`): 9381 archived procedures, 256 of them still carrying the old literal `Done` row this tool used to write, 3170 carrying rows with identical `Started`/`Completed` stamps in its `%Y%m%d-%H%M%S` form; 580 archived procedures carry an unfinished row today (1680 `Pending`, 103 `In Progress`, 21 `Blocked`), all of them listed in `tools/check_archived_status_baseline.txt` (584 paths), which is why `tools/check_workitem_structure.py --archived-status` reports no findings. The issue's "90 procedures carrying its stamp" figure is its prerequisite Plan's own unresolved count and is not reproducible.

Found while checking the issue's claims against the code, beyond what it states:
- The issue's write-before-the-checks claim is no longer true: `run` computes the status rewrite, the findings insertion, the destination check, and the memo edit, and only then calls `_commit`, whose writes go through `tools/_atomic_write.py` staged writes — a refused archive leaves the procedure unchanged today (`Explicit in code`, and pinned by `test_taken_archive_destination_is_exit_1` and `test_no_memo_line_match_is_exit_1`). What remains is the order inside `_commit`: the memo line is edited before the archive write and the `unlink`, so a failing move leaves the memo without its line; REQ-002's pre-write refusal discipline therefore applies to the new refusals only.
- The destination is the module constant `DONE_DIR`, whatever directory the procedure came from, while `move_to_done` derives it from `source.parent / "done"`; a procedure outside `implementations/` would change behavior silently, so it must be refused (`Explicit in code`).
- `move_to_done` stages the uncommitted source before the move (so the rewritten content travels in the staged rename) and asks `origin` whether the destination already exists there; a fetch failure degrades to a no-op (`Explicit in code`, module docstring and `move_to_done`).
- `move_to_done` refuses a taken destination itself, but only when it is called — after the tool has already written the rewritten procedure — so the tool must keep its own destination check as a pre-flight check, derived from the procedure's location instead of the `DONE_DIR` constant (REQ-001, REQ-002).
- The existing test module pins the failure this Plan removes: `test_memo_line_is_removed_by_filename` asserts that the archived copy still holds `| Blocked |`, and every archival and dry-run case writes the document outside `implementations/` and repoints `cdp.DONE_DIR` with the `_done_dir` helper — both obsolete under the sanctioned move (destination from `source.parent / "done"`) and the location refusal (re-verified 20261118).

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
| `tools/complete_doc_procedure.py` | Pre-validate, archive through `move_to_done`, remove the memo line last, refuse unfinished rows | Archives with `stage_write` to a `DONE_DIR` copy plus `opts.proc.unlink()`, updates only `Pending` rows, and edits the memo before the move | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-008 / AC-1, AC-2, AC-3, AC-4, AC-5, AC-8 | `_commit` writes `stage_write(dest, new_text)` then `opts.proc.unlink()`; `_complete_status_rows` skips rows whose third cell is not `Pending`; 9657 B of 24576 B, not in the `tools/` size baseline (re-verified 20261118) | `tests/tools/test_complete_doc_procedure.py` | Verified |
| `tests/tools/test_complete_doc_procedure.py` | Add the archival, refusal, dry-run, and order tests | The prerequisite Plan's phase 1 created the module; this Plan restructures its archive fixtures and adds the refusal cases | REQ-006 / AC-6 | 16406 B module; `_done_dir` monkeypatches `cdp.DONE_DIR` and `test_memo_line_is_removed_by_filename` asserts `| Blocked |` in the archived copy; `tests/tools/test_manage_workitem_stage.py` builds a temporary repository with `git.Repo.init` and a committed `.gitkeep` (re-verified 20261118) | The file itself | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | State the archival path, the refusal, and the exit codes | Rows 109 and 257 describe the write-and-delete archive and no unfinished-row refusal | REQ-007 / AC-7 | The two rows for `complete_doc_procedure.py`, at lines 109 and 257 (re-verified 20261118) | `tools/check_tool_descriptions_sync.py` | Verified |

Revalidation (20261118, `plan-to-implementation-procedure` Step 2/3a): the prerequisite Plan is archived in `plans/done/` with all five steps `Completed`, and its phase 3 already replaced the plain `rename` with a staged write plus `unlink` and split `main`, so the Plan's `proc.rename` claim and its `radon` grade E (33) baseline are stale — today `radon cc tools/complete_doc_procedure.py -s -n C` reports nothing and the highest grade is B (9). The "writes before it checks" claim is stale too: the destination and memo refusals already run before the first staged write, so only the new refusals need moving and the memo edit still has to move after the move. Row 2 is no longer a new file (16406 B), and row 3's rows are at lines 109 and 257, not 108 and 255. The unfinished-status tuple is `_UNFINISHED_STATUSES` (`tools/_workitem_status_table.py`, `("Pending", "In Progress", "Blocked")`), private, with `tools/_workitem_stage_parser.py` as the sibling precedent for importing a private name from that module. AC-1's `rg` check was rewritten because no `.rename(` call exists to remove. No row's path, responsibility, requirement link, or evidence type changed; the three rows were re-checked against current source and stay `Verified`, and the section was re-frozen after this single correction cycle.

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
- AC-1 (REQ-001): A finished procedure is archived through the sanctioned function and `git status` shows a staged rename with the rewritten content; the tool calls `move_to_done` and no longer writes an archive copy or unlinks the source (tests; `rg -n "move_to_done" tools/complete_doc_procedure.py` names the call, and `rg -n "DONE_DIR|\.unlink\(" tools/complete_doc_procedure.py` is empty — the `.rename(` check of the issue is vacuous today because no `rename` call remains).
- AC-2 (REQ-002): A procedure with an `In Progress` or `Blocked` row is not archived, the tool exits `1` naming the rows, and the procedure file, the memo, and `implementations/done/` are byte-identical afterwards (tests); an existing destination and a missing memo line refuse the same way (tests).
- AC-3 (REQ-003): A procedure outside `implementations/` exits `2` with nothing changed (test).
- AC-4 (REQ-004): `--dry-run` returns the same exit code as the real run for each refusal and for success, and leaves the procedure, the memo, and `implementations/done/` unchanged (tests).
- AC-5 (REQ-005): After a successful move the memo no longer holds the line and the Verification Findings table is present (tests).
- AC-6 (REQ-006): The test module covers each behavior above and passes with a temporary Git repository.
- AC-7 (REQ-007): `tools/check_tool_descriptions_sync.py` passes and the rows match the tool.
- AC-8 (REQ-008): The `tools/` size gate passes, `radon cc tools/complete_doc_procedure.py -s -n C` reports nothing, and ruff, mypy, and bandit are clean.

## Tests
- `tests/tools/test_complete_doc_procedure.py`: unfinished row (`In Progress`, `Blocked`) blocks the archive; a finished procedure is moved and the rename is staged; `--no-archive` updates rows without the refusal; dry run; destination exists; memo line missing; location refusal; memo line removed after the move; Verification Findings insertion (REQ-001 to REQ-006). The fixture commits the procedure before the run so that the move shows as a rename.
- Fixture restructure the existing module needs (re-verified 20261118): every archival and dry-run case currently writes the document outside `implementations/` and repoints `cdp.DONE_DIR` through `_done_dir`; under `move_to_done` the destination comes from `source.parent / "done"`, so the cases move into a temporary Git repository (`git.Repo.init`, a committed `.gitkeep`, as in `tests/tools/test_manage_workitem_stage.py`) with the document under `implementations/` and an `implementations/done/` directory. `DOC_TEXT` keeps a `Blocked` row for the status-row cases (they run with `--no-archive`), so the archival cases need a finished-rows fixture variant, and the assertion that the archived copy still holds `| Blocked |` is replaced on purpose: archiving such a procedure is what REQ-002 refuses.
- Smoke run: `--dry-run` on a copy of a real procedure in a scratch clone (REQ-004).

## Documentation Impact
N/A for `docs/*.md`: no file under `docs/` changes. The tool description rows change (REQ-007).

## Assumptions
- The memo workflow stays inside the tool and the memo path stays the default `memo3.md` (the issue's two open questions are unchanged; UNK-02). `memo3.md` exists (629 B, re-verified 20261118) and lists procedure documents of earlier batches, which is what the tool's memo fixture models.
- The observable behavior change is the refusal itself: a run whose rows are unfinished, or whose document is outside `implementations/`, now exits non-zero with nothing written, where today it rewrites rows and archives. The "refused archive leaves rows rewritten" state the issue describes no longer exists (staged writes), so the Assumption records the refusal as the change, not the write order.
- Calling `move_to_done` with `stage_only=True` is enough: it stages the rewritten source (its `_auto_commit` runs `git add` for the uncommitted file) and then `git mv`s it; the tool never commits.
- The location refusal (REQ-003) is a usage error (exit 2) checked first, for any run: a procedure must be directly under `implementations/`. It is distinct from the unfinished-row refusal (REQ-002, exit 1), which applies only when archiving. The existing `--no-archive` fixtures must place documents under `implementations/` after the restructure.
- The refusal reuses `_UNFINISHED_STATUSES` (`("Pending", "In Progress", "Blocked")`, line 314 of `tools/_workitem_status_table.py`) by import; `tools/_workitem_stage_parser.py` is the verified sibling precedent for importing a private name from that module (re-verified 20261118), so that module is not a target of this Plan.
- Overlap with the status-vocabulary Plan on the tool and its test was a sequencing dependency and is now satisfied (that Plan is archived with every step `Completed`). Overlap on `tools/TOOL_DESCRIPTIONS.md` is row-level and report-only: three sibling Plans of this batch (`plans/20261117-134238_wftoolfu003_runner-description-drift.md`, `plans/20261117-134334_wftoolfu004_plan-leftover-detection.md`, `plans/20261117-134609_wftoolfu005_plan-prose-dependency-gating.md`) also name the file, none of them the two `complete_doc_procedure.py` rows this Plan edits.
- Updating the existing archival tests is a deliberate characterization change: `test_memo_line_is_removed_by_filename` currently asserts that the archived copy still holds a `Blocked` row, and the fixture layout it relies on (documents outside `implementations/`, a monkeypatched `DONE_DIR`) is what REQ-001 and REQ-003 remove.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `close-implementation` itself should also refuse `In Progress` and `Blocked` rows | A maintainer decision; this Plan adds the check to the docs-wave tool only | File a separate issue if the maintainer wants the shared rule changed | False |
| UNK-02 | Whether the memo workflow should keep archiving inside this tool, and whether the memo path should be configurable | The owner of the batch memo has not decided | Keep the current behavior; revisit only if the owner asks | False |
| UNK-03 | Order against the other Plans editing `tools/TOOL_DESCRIPTIONS.md` (its function-layout half was resolved by verification 20261118: `main` is already split into `parse_args`, `run`, `_preview`, `_commit`) | What the sibling Plans write into the shared description file at implementation time | Read the two `complete_doc_procedure.py` rows at implementation time, after the sibling Plans of this batch | False |

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
- **Baseline**: re-measured 20261118: `radon cc tools/complete_doc_procedure.py -s -n C` reports nothing and the highest grade is B (9) at `_complete_status_rows`; the grade E (33) `main` the prerequisite Plan split is gone. `vulture` and `bandit` findings under `scripts/` are pre-existing and outside the targets; `diff-cover` has no baseline because the tree equals `master`.

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
| All target files | Size gate and archival evidence | `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`; `rg -n "move_to_done" tools/complete_doc_procedure.py`; `rg -n "DONE_DIR|\.unlink\(" tools/complete_doc_procedure.py` | Gate passes; the sanctioned call is present; no archive-copy write or `unlink` remains |

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
| 1 | Tests first: refusals, staged rename, dry run, location, memo order | In Progress | — | — |  |
| 2 | Refusals before the first write | In Progress | — | — |  |
| 3 | Archive through the sanctioned function; memo line last | In Progress | — | — |  |
| 4 | Documentation: the two tool rows | In Progress | — | — |  |
| 5 | Verification: validation sequence, size gate, dry-run smoke | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261118-070621_01_tools_complete_doc_procedure.py.md | 2, 3 | Procedure | Pending | — | — |
| implementations/20261118-070621_02_tests_tools_test_complete_doc_procedure.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-070621_03_tools_TOOL_DESCRIPTIONS.md.md | 4 | Procedure | Pending | — | — |

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
| REQ-001 | Implementation Intent (sanctioned archival); Required Changes | `tools/complete_doc_procedure.py` | Phase 3 | AC-1 | staged-rename test; `rg` for the `move_to_done` call and the absence of `DONE_DIR`/`unlink` | Explicit in issue |
| REQ-002 | Required Changes (refuse unfinished rows); `Problem` evidence on write order | `tools/complete_doc_procedure.py` | Phase 2 | AC-2 | refusal and byte-identity tests | Derived from confirmed evidence |
| REQ-003 | `Problem` evidence on `DONE_DIR` versus `move_to_done` | `tools/complete_doc_procedure.py` | Phase 2 | AC-3 | location test | Derived from confirmed evidence |
| REQ-004 | Required Changes (a dry run moves nothing) | `tools/complete_doc_procedure.py` | Phase 2 | AC-4 | dry-run tests | Explicit in issue |
| REQ-005 | Implementation Intent (memo line removal unchanged) | `tools/complete_doc_procedure.py` | Phase 3 | AC-5 | memo-order and findings tests | Explicit in issue |
| REQ-006 | Required Changes (add tests) | `tests/tools/test_complete_doc_procedure.py` | Phase 1 | AC-6 | the test module | Explicit in issue |
| REQ-007 | Required Changes (update the tool description) | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-7 | `tools/check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-008 | Constraints (tool conventions, size gate) | `tools/complete_doc_procedure.py` | Phase 5 | AC-8 | ruff, mypy, bandit, radon, size gate | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-070621 -->