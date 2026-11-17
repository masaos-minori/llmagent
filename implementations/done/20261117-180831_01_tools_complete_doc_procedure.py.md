## Goal
Make `tools/complete_doc_procedure.py` write the shared `Completed` status instead of the
non-standard `Done`, route every file rewrite through `tools/_atomic_write.py`, add the
standard `--dry-run` preview, and split the grade E `main` into functions below complexity
grade C, with behavior and exit codes otherwise unchanged.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file procedure for row 1 of the plan's frozen `Implementation Target Files` table:
`tools/complete_doc_procedure.py` (REQ-001, REQ-002, REQ-003; AC-1, AC-2, AC-3).

This document covers exactly one file. It does not carry the test module as a companion:
`tests/tools/test_complete_doc_procedure.py` is a frozen-table row (seq 04) named by two
other rows in their `Related Tests` cells, so under the `SKILL.md` "One target file = one
procedure document" exception it fails the companion condition "exactly one other row names
it" and keeps its own document. It also does not declare COMPLETED_STATUS: that name is
created by the row 2 document (seq 02) in `tools/_workitem_status_table.py`.

## Assumptions
- Plan phase order and seq order differ. The frozen table positions are `seq`, not the work
  order. The plan lands its phases as: Phase 1 = the seq 04 test module (characterization
  tests first), Phase 2 = seq 02 (COMPLETED_STATUS in `tools/_workitem_status_table.py`)
  then this document's status fix, Phase 3 = this document's dry-run, atomic-write, and
  function-split steps, Phase 4 = the seq 03 `tools/TOOL_DESCRIPTIONS.md` row. Do not
  execute documents in raw seq order.
- COMPLETED_STATUS is referenced here but declared in the seq 02 document; this document
  imports it and MUST NOT define it. It is written without backticks because the
  `tools/stale_detector.py` sibling rule resolves (new)-marked names only from lower-seq
  siblings, and seq 02 is a higher-seq sibling.
- Overlap findings against `plans/20261117-133851_wftoolfu001_workitem-status-vocabulary.md`
  (`tools/_workitem_status_table.py`) and `plans/20261117-134130_wftoolfu002_doc-procedure-archival.md`
  (`tools/complete_doc_procedure.py`) are compatible sequencing dependencies, not conflicts:
  both plans name this plan as their prerequisite, so this document lands first.
- The stamp behavior is characterization-pinned: `time.strftime("%Y%m%d-%H%M%S")` (line 65)
  fills both the Started and Completed cells with the same value; it stays unchanged (AC-3).
- Historical `Done` rows in archived procedures are not rewritten (plan out of scope; the
  follow-up plan `plans/20261117-134130_wftoolfu002_doc-procedure-archival.md` covers them).

## Design decisions
- Status value source (plan Design Decision 2): import the shared COMPLETED_STATUS from
  `tools/_workitem_status_table.py`; do not import `DONE_STATUS` from
  `tools/set_execution_status.py` (a status writer must not depend on a sibling CLI). The
  import needs the sibling-import shim written before it, as in `tools/set_execution_status.py`
  line 36 (`if __package__ in (None, ""): sys.path.insert(...)`); the constant is at line 42
  of that file today as the conforming precedent.
- Keep the hand-rolled option loop (lines 46-63) inside a parsed-arguments function rather
  than migrating to `argparse`: the seq 04 characterization tests pin the tool's own usage
  messages (for example `unknown option: ` and `--vf needs ITEM|FINDING|ACTION:`), and
  `argparse` would replace them with its own usage text and exit semantics while adding no
  required behavior. `--dry-run` is added as one more branch with the same flag name and
  store-true semantics the shared helpers define.
- Diff preview reuses `print_dry_run` and `render_diff` from `tools/_atomic_write.py` (plan
  Design Decision 3); `stage_write` and `StagedWrite.commit` replace the two direct
  `write_text` calls. The archive keeps its move semantics (the destination-exists refusal
  and the placement under `implementations/done/` are unchanged), performed through a staged
  write at the destination followed by removing the source, and is skipped in a dry run.
- Write ordering: validation-first, then commit. Anchors, `--vf` format, the destination
  check, and the memo-line match are all decided before content is committed; the commit
  order stays procedure content, memo line, archive move. Exit codes `0`, `1`, `2` keep their
  current meanings and the current stderr messages stay byte-identical for the paths the
  seq 04 characterization tests pin.

## Alternatives considered
- Import `DONE_STATUS` from `tools/set_execution_status.py`: rejected by plan Design
  Decision 2 (sibling CLI dependency).
- Migrate argument parsing to `argparse` and reuse `add_dry_run_argument`: rejected here for
  the characterization-message reason above; `tools/set_execution_status.py` remains the
  convention model for the entry point signature only.
- Rewrite historical `Done` rows in the same pass: rejected by the plan (out of scope;
  follow-up plan filed).

## Implementation
### Target file
`tools/complete_doc_procedure.py` (Modify). The path already exists; no (new) marker.

### Procedure
1. Add the sibling-import shim and import COMPLETED_STATUS from
   `tools._workitem_status_table` and `print_dry_run`, `render_diff`, `stage_write` from
   `tools._atomic_write`, following the import order of `tools/set_execution_status.py`.
2. Rewrite the status fix (plan Phase 2): replace the literal `Done` written at line 87 with
   COMPLETED_STATUS, and state `Completed` in the module docstring (line 5) so a search
   for `Done` in this file reports nothing (AC-1).
3. Add the dry run (plan Phase 3): `--dry-run` flag through the option loop; when set, the
   tool performs every validation, prints the unified diff of the procedure status/findings
   change with `print_dry_run`, prints the memo diff and the intended archive line when
   archiving, writes, renames, and edits nothing, and exits with the same codes a real run
   would return (AC-2, REQ-002).
4. Route the file rewrites through the atomic helper (plan Phase 3): replace
   `proc.write_text` (line 115) and `memo.write_text` (line 131) with staged writes
   committed in place, and replace `proc.rename` (line 135) with a staged write of the new
   procedure text at `DONE_DIR / proc.name` (constant at line 30) followed by removing the
   source path; the destination-exists refusal (line 120) runs before any commit.
5. Split `main` (plan Phase 3, REQ-003): extract argument parsing, the status-row update,
   the `### Verification Findings` insertion, and the memo-removal-plus-archive step into
   module-level functions, each below `radon` grade C (AC-3: `radon cc
   tools/complete_doc_procedure.py -s -n C` reports nothing), and give the entry point the
   `main(argv: list[str] | None = None) -> int` form with `None` meaning `sys.argv[1:]`,
   documented. The current `main` is at line 33 and is grade E (33).

### Method
- Keep the module's constants (`REPO`, `DONE_DIR`), the `Pending`-row filter, the step-note
  filling, the single `stamp` value, the findings-table shape, and every stderr message
  pinned above unchanged; move them into the extracted functions without editing their text.
- Function extraction is behavior-preserving: the seq 04 characterization tests (written
  against the current tool in plan Phase 1) must pass before and after each extraction step.
- The staged writes use `stage_write` + `StagedWrite.commit` so an interruption leaves the
  original file untouched; on a failure after any stage, discard the staged temporary files
  before returning the error code.
- In a dry run no `stage_write` call runs at all, so no temporary file is created either.
- The extracted functions read the `REPO` and `DONE_DIR` module attributes at call time; a
  default argument that captures them would break the seq 04 tests'
  `monkeypatch.setattr(..., "DONE_DIR", ...)`, which is how those tests keep the real
  `implementations/done/` out of scope (verified against the seq 04 Design decisions).

### Details
- Line 87 today writes `| <step> | <desc> | Done | <stamp> | <stamp> | <note> |`; only the
  status cell changes, to `Completed`.
- Docstring line 5 states the tool sets rows to `Done`; restate it with `Completed` (REQ-001
  covers the docstring text; AC-1 checks `rg -n "Done" tools/complete_doc_procedure.py`
  reports nothing).
- The usage block (lines 14-17) and the exit-code line (line 19) of the docstring must
  document `--dry-run` and the `argv`-optional entry point.
- In `tools/complete_doc_procedure.py` the memo line is matched by filename substring (line
  127) and the memo default is memo3.md (line 43): both unchanged.

## Compatibility considerations
- CLI contract unchanged: positional procedure path, `--stepN-note`, `--vf`, `--memo`
  (default `memo3.md`), `--no-archive`; one flag added: `--dry-run`. Existing invocations
  behave identically apart from the written status word.
- Downstream consumers of the written status (`tools/sync_plan_workitem_status.py`,
  `tools/close_procedures_batch.py`, `tools/_detect_unexecuted_archive.py`) only accept
  `Completed`, so the change makes the tool's own output reconcilable; no consumer edit is
  needed here.
- No importer of this tool exists (verified in plan Step 3); the tool is run by hand.
- `tools/TOOL_DESCRIPTIONS.md` rows for this tool are updated by the seq 03 document, not here.

## Security considerations
N/A: no new input surface; paths come from the same arguments as today. Staged writes reduce
the existing partial-write corruption risk on the procedure and memo files.

## Rollback considerations
Single-file revert (`git checkout -- tools/complete_doc_procedure.py`) restores the previous
behavior; already-archived procedures and already-written `Completed` rows are data, not code,
and a revert does not rewrite them. Rollback is safe only before the seq 03 document updates
the description rows; after that, revert the rows in the same commit scope.

## Validation plan
1. The seq 04 module `tests/tools/test_complete_doc_procedure.py` (its own document) is the
   characterization and regression harness: run it first against the current tool (status and
   dry-run tests fail first), then keep it green through steps 2-5.
2. Targeted: `uv run pytest tests/tools/test_complete_doc_procedure.py`.
3. Complexity: `radon cc tools/complete_doc_procedure.py -s -n C` reports nothing (AC-3).
4. Vocabulary: `rg -n "Done" tools/complete_doc_procedure.py` reports nothing; the written
   status equals COMPLETED_STATUS and belongs to the vocabulary (AC-1).
5. Smoke run: the tool with `--dry-run` on a copy of a real archived-style procedure under a
   temporary memo file; confirm the diff output and that the procedure, memo, and
   `implementations/done/` are unchanged (AC-2, plan Test Strategy smoke run).
6. Full sequence per `rules/toolchain.md` (ruff, mypy, full test suite) — the importers of
   `tools/_workitem_status_table.py` run here (plan Test Strategy).

## Completion criteria
- AC-1, AC-2, AC-3 of the plan hold for this file; the seq 04 tests pass; `radon cc
  tools/complete_doc_procedure.py -s -n C` reports nothing; the full validation sequence is
  green; this document's Execution Status rows are all `Completed`.

## Out of Scope
- Rewriting historical `Done` rows in archived procedures (follow-up plan
  `plans/20261117-134130_wftoolfu002_doc-procedure-archival.md`).
- Declaring COMPLETED_STATUS in `tools/_workitem_status_table.py` (seq 02 document).
- Updating `tools/TOOL_DESCRIPTIONS.md` (seq 03 document).
- Creating the test module (seq 04 document).
- Changing `tools/set_execution_status.py` (left untouched per plan Design Decision 2).
- No `docs/*.md` change and no deploy step for this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-205439 | 20261117-205811 | main split into parse_args/_apply_option/_complete_status_rows/_insert_findings/_archive_destination/_memo_text/_preview/_commit/run; COMPLETED_STATUS imported; --dry-run added; staged writes for procedure, memo, and archive; validation-first ordering. |
| 2 | Add or update tests per Validation plan | Completed | 20261117-205439 | 20261117-205811 | No new test file for this row: the seq 04 module (24 tests) is the harness and is green twice with randomized order. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261117-210903 | ruff format/check, mypy, radon cc -n C (no C-or-worse block), bandit -ll, rg 'Done' (no match), pytest tests/tools/test_complete_doc_procedure.py 24 passed, importer tests 189 passed, dry-run smoke on a copied procedure under a temp memo: diff printed, procedure/memo unchanged, implementations/done untouched. Full suite deferred to end of batch. Batch-mode validation: ruff format/check, mypy (CI invocation), bandit, lint-imports, ast-grep Not available locally, module-size tools baseline OK, radon, targeted tests, and the full suite twice: run 1 1 failed (tests/rag flaky, unrelated) / 12614 passed, run 2 12615 passed / 7 skipped / 0 failed. coverage xml + diff-cover -> no lines with coverage info (diff is tools/-only, coverage measured on scripts/). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261117-205811 | N/A: no docs/00_index.md task-scope mapping for tools/complete_doc_procedure.py; tools/TOOL_DESCRIPTIONS.md rows are the seq 03 row. |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20261117-123331_wftool002_status-vocabulary-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-124614_wftool002_status-vocabulary-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-180831
- **Related target files**: `tools/complete_doc_procedure.py`