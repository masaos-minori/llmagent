## Goal
- Make `tools/complete_doc_procedure.py` write the Execution Status value that the shared work item vocabulary defines (`Completed`), bring the tool to the repository's tool conventions (dry run, atomic writes, a testable entry point), and cover it with tests, so no work item tool writes a status outside the vocabulary.

## Priority
Medium

## Scope
- **In-Scope**: (1) one public definition of the completed status in the shared status module and its use by the tool; (2) the tool's entry point, `--dry-run`, and atomic writes; (3) splitting the tool's single oversized function without changing behavior; (4) a new test module for the tool; (5) the tool description rows and the convention paragraph.
- **Out-of-Scope**: changing the status vocabulary; rewriting archived procedures that hold `Done` rows; validating Status values in the checkers (UNK-01); moving the tool's archival step onto `manage_workitem_stage.py close-implementation` (UNK-02); retiring the tool.
- **Dependencies**: N/A: nothing must be done first. `tools/TOOL_DESCRIPTIONS.md` is also edited by the 9 other open Plans of this batch. The structure-gate Plan (wftool001) is archived at `plans/done/20261117-124139_wftool001_gate-workitem-structure.md`, and the two procedures named at the time this Plan was written (`implementations/20261117-151927_06_tools_TOOL_DESCRIPTIONS.md.md` and `implementations/20261117-110514_04_tools_TOOL_DESCRIPTIONS.md.md`) are already under `implementations/done/`, so their rows landed (re-verified in this cycle). The edits here touch other rows than those (see Assumptions), and the order against the 9 open Plans is settled at implementation time (UNK-03).

## Background
Filed from the investigation of the issue -> plan -> implementation toolchain. The tool automates the docs-wave bookkeeping that the batch memo `memo3.md` asks for: it sets the Execution Status rows, inserts a Verification Findings table, removes the document's line from the memo, and archives the procedure. The shared vocabulary lives in `tools/_workitem_status_table.py`.

## Problem
`tools/complete_doc_procedure.py` writes `Done` into Execution Status rows, which is outside the vocabulary (Pending, In Progress, Blocked, Completed, Superseded). Evidence: the tool writes the literal `Done` at line 87 and states it in its module docstring at line 5 (`Explicit in code`, re-verified in this cycle); no test file references it (`Explicit in code`, `rg` over `tests/`); archived procedures hold 732 `Done` rows in 256 files, re-measured in this cycle with the shared parser `parse_execution_status_rows` (`Operationally observed`), where the issue's 790 rows in 270 files counted every `| Done |` cell with `rg` (814 rows in 283 files today, before the newest archives). Which `Done` rows the tool wrote cannot be told from hand-written ones by a derived signature (`Needs confirmation`); the issue's 198 rows in 90 files were not reproduced (identical Started/Completed stamps: 689 rows in 250 files; `Done` rows plus a `### Verification Findings` table: 129 rows in 53 files).

How the checkers treat `Done` (the issue's open question): `check_workitem_structure.py --archived-status` classifies a row as unfinished only for Pending, In Progress, and Blocked, so `Done` passes silently (`Explicit in code`); `sync_plan_workitem_status.procedure_outcome` returns `Completed` only when every row is `Completed`, so a procedure with a `Done` row is never reconciled into its Plan (`Explicit in code`); `close_procedures_batch` treats only `Completed` and `N/A` as terminal (`Explicit in code`); `close-implementation` refuses only `Pending` rows (`Explicit in code`). `check_workitem_traceability.py` has no status classification (`Strongly implied by code`).

## Reason for Change
A `Done` row breaks the Plan row reconciliation and the batch close, and no check reports it. The vocabulary was just extended (the `Superseded` status), so divergent writers are likelier to drift. The tool is also the only status writer that is untested, has no dry run, and does not write atomically, and its single function has the highest complexity in the module set it belongs to. Nothing makes the change time-sensitive beyond the next batch run.

## Implementation Intent
Keep the tool, because 90 archived procedures carry its stamp and the memo workflow it automates is live; retiring it would drop a used capability. The status value comes from one public definition next to the existing vocabulary. The tool is brought to the conventions the issue requires, behavior-first: tests are written before the function is split. The archival step and the checker gap stay out of this change (UNK-01, UNK-02).

## Requirements
- `REQ-001`: `tools/_workitem_status_table.py` defines one public constant for the completed status, the vocabulary contains it, and `tools/complete_doc_procedure.py` writes that constant instead of the literal `Done`, including the status its module docstring says the tool writes; no `Done` status text remains in the tool.
- `REQ-002`: The tool's entry point is `main(argv: list[str] | None = None) -> int` with `None` meaning `sys.argv[1:]` documented; `--dry-run` prints the intended change as a unified diff and writes, renames, and edits nothing; every file rewrite goes through `tools/_atomic_write.py`; exit codes `0`, `1`, `2` keep their meaning.
- `REQ-003`: The tool's logic is split into functions of complexity grade below C (it is grade E today) with unchanged behavior.
- `REQ-004`: A new test module covers the written status (equal to the constant and inside the vocabulary), step notes, the Verification Findings insertion and its anchors, the usage errors, the memo line removal, the archive-destination refusal, and the dry run.
- `REQ-005`: `tools/TOOL_DESCRIPTIONS.md` states the written status and lists the tool among the dry-run and atomic-write writers.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/complete_doc_procedure.py` | Use the shared status, add dry run and atomic writes, split `main` | Writes the literal `Done`, has a hand-rolled `main(argv)` with no dry run, and one grade E function | REQ-001, REQ-002, REQ-003 / AC-1, AC-2, AC-3 | line 87 writes `Done` into the row line and line 5 states it in the module docstring; `radon` reports `main` as grade E (33); no `_atomic_write` or `tools.*` import (re-verified in this cycle) | `tests/tools/test_complete_doc_procedure.py` | Verified |
| `tools/_workitem_status_table.py` | Define the public completed-status constant inside the vocabulary | The vocabulary is a private frozenset and no public name exists | REQ-001 / AC-1 | `_VALID_STATUSES` is private; `DONE_STATUS` exists only inside `tools/set_execution_status.py`; five tool modules import this module (checked in Step 3) | `tests/tools/test_complete_doc_procedure.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Update the tool rows and the convention paragraph | The rows do not state the status and the paragraph omits the tool from both writer lists | REQ-005 / AC-5 | Two table rows name the tool; the `--dry-run` and atomic-write paragraphs list the conforming writers and omit it (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |
| `tests/tools/test_complete_doc_procedure.py` | Create the test module | No test references the tool | REQ-004 / AC-4 | New file; the directory `tests/tools/` exists and holds the sibling status-writer tests (checked in Step 3) | The file itself | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/set_execution_status.py` | The conforming sibling status writer: `DONE_STATUS`, `add_dry_run_argument`, `print_dry_run` | `tools/complete_doc_procedure.py` / REQ-002 |
| `tools/_atomic_write.py` | The atomic write and dry-run helpers to reuse | `tools/complete_doc_procedure.py` / REQ-002 |
| `tools/sync_plan_workitem_status.py` | Shows that only all-`Completed` procedures are reconciled | `tools/_workitem_status_table.py` / REQ-001 |
| `tools/close_procedures_batch.py` | Defines `TERMINAL_STATUSES` | `tools/_workitem_status_table.py` / REQ-001 |
| `tests/tools/test_set_execution_status.py` | Fixture and monkeypatch style to follow | `tests/tools/test_complete_doc_procedure.py` / REQ-004 |
| `memo3.md` | The memo whose line the tool removes, to model the memo fixture | `tests/tools/test_complete_doc_procedure.py` / REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001): After a run, every status the tool wrote equals the new constant and belongs to the vocabulary (test); `rg -n '"Done"|\| Done \|' tools/*.py` finds no status write, and `rg -n "Done" tools/complete_doc_procedure.py` reports nothing.
- AC-2 (REQ-002): `--dry-run` prints a unified diff and leaves the procedure, the memo, and `implementations/done/` unchanged (test); exit codes `0`, `1`, `2` hold for success, a missing anchor or memo line, and a usage error (tests).
- AC-3 (REQ-003): `radon cc tools/complete_doc_procedure.py -s -n C` reports nothing, and the characterization tests pass before and after the split.
- AC-4 (REQ-004): The test module covers each behavior listed in REQ-004 and passes.
- AC-5 (REQ-005): `tools/check_tool_descriptions_sync.py` passes and the rows and paragraphs match the tool.

## Tests
- `tests/tools/test_complete_doc_procedure.py` (new): written status, step notes, Verification Findings (with and without the existing section, and the missing `### Blocker Log` anchor), missing anchors, usage errors, memo line removal, memo absent, archive destination exists, dry run (REQ-001, REQ-002, REQ-004).
- Existing tests for the importers of the status module run in Phase 5, because REQ-001 adds a name to a shared module (REQ-001).
- Smoke run: the tool with `--dry-run` on a copy of a real procedure (REQ-002).

## Documentation Impact
N/A for `docs/*.md`: no file under `docs/` changes. The tool description rows and the convention paragraph change (REQ-005).

## Assumptions
- The tool stays in use: `Done` rows sit in 256 archived procedures and `memo3.md` describes the workflow it automates (no skill references it, so use is ad hoc). The issue's 90-file stamp count was not reproduced with a derived signature (see Problem), so the keep decision rests on the live memo workflow, not on the count.
- The archive step keeps its plain `rename`; routing it through `close-implementation` is a separate decision (UNK-02).
- Overlaps reported by `tools/check_plan_target_overlaps.py` in this cycle are compatible, not conflicts:
  - `tools/TOOL_DESCRIPTIONS.md` (10 Plans): row-level. The structure-gate Plan (wftool001) already landed its `check_workitem_structure.py` rows; this Plan edits the `complete_doc_procedure.py` rows and the writer lists of the convention paragraph.
  - `tools/_workitem_status_table.py` with `plans/20261117-133851_wftoolfu001_workitem-status-vocabulary.md`: that Plan names this Plan's Phase 2 as its prerequisite, so this Plan lands first and its public constants sit beside `COMPLETED_STATUS`.
  - `tools/complete_doc_procedure.py` and `tests/tools/test_complete_doc_procedure.py` with `plans/20261117-134130_wftoolfu002_doc-procedure-archival.md`: that Plan names this Plan's Phases 1 and 3 as its prerequisites, so this Plan lands first.
- The added constant is additive: no existing name changes, so the importers of `tools/_workitem_status_table.py` are unaffected.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Checkers accept any Status value, so hand-written `Done` rows pass unnoticed (732 `Done` rows in 256 archived procedures; the tool's share cannot be separated by a derived signature) | No check validates the Status column against the vocabulary | Filed as `plans/20261117-133851_wftoolfu001_workitem-status-vocabulary.md` (that Plan names this Plan's Phase 2 as its prerequisite) | False |
| UNK-02 | The tool archives with a plain `rename` instead of `git mv` through `close-implementation`, which the archival rule requires | Whether the memo workflow may switch to the sanctioned archival path | Filed as `plans/20261117-134130_wftoolfu002_doc-procedure-archival.md` (that Plan names this Plan's Phases 1 and 3 as its prerequisites); this Plan keeps the step unchanged | False |
| UNK-03 | Order against the 9 open Plans of this batch that edit `tools/TOOL_DESCRIPTIONS.md` | The final text of the shared rows in those Plans is not written yet | Row-level edits: land this Plan before the two Plans that name it as a prerequisite, and re-read the two `complete_doc_procedure.py` rows before editing them | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/complete_doc_procedure.py` | Modify | Low: no importer; run by hand; one documented consumer row | 1 | High: single author | not applicable (rsynced) |
| `tools/_workitem_status_table.py` | Modify | Medium: five tool modules import it; the change is one added name | 2 | High: single author | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low: documentation rows read by the sync checker | 74 | High: single author | not applicable (rsynced) |
| `tests/tools/test_complete_doc_procedure.py` | Create | Low | N/A: new file | N/A: new file | not applicable (rsynced) |

## Design
**Classification**: Path B (four target rows, one of them a new file). The four analyses ran once for this cycle.
- **Architecture**: `tools/complete_doc_procedure.py` imports only the standard library today and will import `tools._workitem_status_table` and `tools._atomic_write`, which are tool-internal helpers; the import-linter contracts cover `scripts/` packages and are unaffected.
- **Dependency graphing**: nothing imports the tool or calls it; only `tools/TOOL_DESCRIPTIONS.md` names it. `tools/_workitem_status_table.py` is imported by `tools/_detect_unexecuted_archive.py`, `tools/_workitem_stage_parser.py`, `tools/check_workitem_structure.py`, `tools/manage_workitem_stage.py`, and `tools/sync_plan_workitem_status.py`. The change to it is one added public name, so no consumer scan was needed.
- **Historical**: churn is low for both Python targets and very high for `tools/TOOL_DESCRIPTIONS.md` (conflict risk); every target has one author.
- **Operational**: no port, database, dependency, or lock is involved; the persisted-schema check does not apply.
- **Decision 1, keep or retire**: keep. Alternative: retire in favor of `tools/set_execution_status.py` plus a findings helper. Rejected because the tool's `Done` rows are in 256 archived procedures, the memo workflow it automates exists (`memo3.md`), and the findings table and memo line removal have no equivalent elsewhere.
- **Decision 2, where the constant lives**: add `COMPLETED_STATUS` to `tools/_workitem_status_table.py`, next to the vocabulary. Alternative: import `DONE_STATUS` from `tools/set_execution_status.py`. Rejected because a status writer should not depend on a sibling CLI. Making `tools/set_execution_status.py` use the same name is left out of scope to keep that tool untouched.
- **Decision 3, conventions**: the issue's constraints require dry run and atomic writes for a rewriting tool, so both are in scope. The dry run reuses the diff helpers of `tools/_atomic_write.py`. The plain `rename` archive is unchanged and skipped in a dry run.
- **Decision 4, complexity**: `main` is grade E (`radon`: 33). Characterization tests come first, then the function is split into argument parsing, status update, findings insertion, and archive steps, each below grade C.
- **Existing `Done` rows**: archived procedures keep them (out of scope); the count is reported above.
- **Baseline**: `vulture` and `bandit` findings under `scripts/` are pre-existing and outside the targets; `diff-cover` has no baseline because the tree equals `master`, and the 90% threshold applies at implementation.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Tests first**
   - [ ] Create the test module with the behaviors of REQ-004; the status test and the dry-run test fail first, the rest pass against the current tool (REQ-004; `tests/tools/test_complete_doc_procedure.py`)
2. **Phase 2: Shared constant and status fix**
   - [ ] Add `COMPLETED_STATUS` inside the vocabulary (REQ-001; `tools/_workitem_status_table.py`)
   - [ ] Write the constant instead of `Done` (REQ-001; `tools/complete_doc_procedure.py`)
3. **Phase 3: Conventions and structure**
   - [ ] Give the entry point the `argv: list[str] | None = None` form, add `--dry-run`, and write through the atomic helper (REQ-002; `tools/complete_doc_procedure.py`)
   - [ ] Split `main` into functions below complexity grade C, keeping the tests green (REQ-003; `tools/complete_doc_procedure.py`)
4. **Phase 4: Documentation**
   - [ ] Update the two tool rows and add the tool to the dry-run and atomic-write writer lists (REQ-005; `tools/TOOL_DESCRIPTIONS.md`)
5. **Phase 5: Verification** (no deploy step: no `scripts/` or `config/` file changes)
   - [ ] Run the validation sequence of `rules/toolchain.md` for the changed tools, the tests of the five importers of the status module, `tools/check_tool_descriptions_sync.py`, and a dry run on a copy of a real procedure; confirm no `Done` literal remains and report the archived `Done` count unchanged (REQ-001 to REQ-005; all target files)

### Release units
N/A: no release unit; each phase passes validation alone when applied in order.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/complete_doc_procedure.py` | Unit tests; dry-run smoke on a copy; complexity | `uv run pytest tests/tools/test_complete_doc_procedure.py -v`; `uv run radon cc tools/complete_doc_procedure.py -s -n C`; `uv run bandit tools/complete_doc_procedure.py` | Tests pass; radon reports nothing; bandit clean |
| `tools/_workitem_status_table.py` | Unit and regression tests of the importers | `uv run pytest tests/tools/test_manage_workitem_stage.py tests/tools/test_manage_workitem_stage_new.py tests/tools/test_sync_plan_workitem_status.py tests/tools/test_check_workitem_structure.py -q` | Pass |
| `tools/TOOL_DESCRIPTIONS.md` | Doc consistency | `uv run python tools/check_tool_descriptions_sync.py` | No finding |
| `tests/tools/test_complete_doc_procedure.py` | Self; lint and types | `uv run ruff format tools tests/tools`; `uv run ruff check tools tests/tools`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | Clean |
| All target files | Status-literal evidence and size gate | `rg -n '"Done"' tools/*.py`; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | No status write; size gate passes |

## Risks
- **Risk**: Splitting a grade E function changes behavior → **Mitigation**: write the characterization tests first (Phase 1) and split only while they stay green.
- **Risk**: Adding a name to `tools/_workitem_status_table.py` disturbs its five importers → **Mitigation**: the change is additive; run the importers' tests in Phase 5.
- **Risk**: A dry run still renames the procedure or edits the memo → **Mitigation**: a test asserts that the procedure, the memo, and the archive directory are unchanged after `--dry-run`.
- **Risk**: Operators who run the tool by hand see `Completed` where they saw `Done` → **Mitigation**: the description rows state the status; the old value was outside the vocabulary.
- **Risk**: `tools/TOOL_DESCRIPTIONS.md` has very high churn → **Mitigation**: change only the tool's rows and the two writer lists; rebase through the commit skill and settle the order per UNK-03.
- **Risk**: Hand-written `Done` rows keep appearing because checkers accept them → **Mitigation**: recorded as UNK-01 with a follow-up issue as the resolution path; this Plan does not claim to prevent them.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first: new test module for the tool | Completed | — | 20261117-212254 |  |
| 2 | Shared completed-status constant and the status fix | Completed | — | 20261117-212254 |  |
| 3 | Conventions: entry point, dry run, atomic writes, function split | Completed | — | 20261117-212254 |  |
| 4 | Documentation: tool rows and convention paragraph | Completed | — | 20261117-212254 |  |
| 5 | Verification: validation sequence, importer tests, dry-run smoke | Completed | — | 20261117-212447 | Batch validation: full suite twice (run 1: 1 unrelated flaky tests/rag failure / 12614 passed; run 2: 12615 passed / 7 skipped / 0 failed), coverage xml + diff-cover exit 0 (no coverage lines: tools-only diff vs --cov=scripts), 4 procedures archived via close_procedures_batch.py. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261117-180831_04_tests_tools_test_complete_doc_procedure.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261117-180831_02_tools__workitem_status_table.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261117-180831_01_tools_complete_doc_procedure.py.md | 2, 3 | Procedure | Completed | — | — |
| implementations/20261117-180831_03_tools_TOOL_DESCRIPTIONS.md.md | 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123331_wftool002_status-vocabulary-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-124614
- **Related target files**: `tools/complete_doc_procedure.py`; `tools/_workitem_status_table.py`; `tools/TOOL_DESCRIPTIONS.md`; `tests/tools/test_complete_doc_procedure.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; Required Changes (align the written status) | `tools/_workitem_status_table.py` | Phase 2 | AC-1 | status test; importer tests | Confirmed by repository evidence |
| REQ-001 | Problem; Required Changes (align the written status) | `tools/complete_doc_procedure.py` | Phase 2 | AC-1 | status test; `rg -n '"Done"' tools/*.py` | Confirmed by repository evidence |
| REQ-002 | Constraints (tool conventions: dry run, atomic writes) | `tools/complete_doc_procedure.py` | Phase 3 | AC-2 | dry-run and exit-code tests | Derived from confirmed evidence |
| REQ-003 | Constraints; `radon` baseline (main is grade E) | `tools/complete_doc_procedure.py` | Phase 3 | AC-3 | `radon cc -n C`; characterization tests | Derived from confirmed evidence |
| REQ-004 | Required Changes (add tests, including the written status) | `tests/tools/test_complete_doc_procedure.py` | Phase 1 | AC-4 | the new test module | Explicit in issue |
| REQ-005 | Required Changes (update the tool description) | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-5 | `tools/check_tool_descriptions_sync.py` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261117-180831 -->