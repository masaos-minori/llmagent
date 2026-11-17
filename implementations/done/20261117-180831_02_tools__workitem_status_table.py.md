## Goal
Define one public completed-status constant inside `tools/_workitem_status_table.py` so
every status writer shares the same name and value, and guarantee by construction that the
vocabulary contains it.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file procedure for row 2 of the plan's frozen `Implementation Target Files` table:
`tools/_workitem_status_table.py` (REQ-001; AC-1).

This document declares the name that the seq 01 document imports; the declaration lives here
because this file owns the status vocabulary. It does not modify any importer, the test
module (seq 04), or `tools/TOOL_DESCRIPTIONS.md` (seq 03).

## Assumptions
- Plan phase order and seq order differ: this document runs in plan Phase 2, after the seq 04
  characterization tests exist and immediately before the status fix in
  implementations/20261117-180831_01_tools_complete_doc_procedure.py.md. Do not execute
  documents in raw seq order.
- The seq 01 document references this constant without backticks because the
  `tools/stale_detector.py` sibling rule resolves (new)-marked names only from lower-seq
  siblings; the (new) declaration in this document is the authoritative one.
- The overlap with plans/20261117-133851_wftoolfu001_workitem-status-vocabulary.md (which
  also names `tools/_workitem_status_table.py`) is a compatible sequencing dependency: that
  plan lists this plan as its prerequisite, so this document lands first.
- No importer changes are needed: adding a name to a module without `__all__` cannot break
  any existing importer statement.

## Design decisions
- Constant identity (plan Design Decision 2): `COMPLETED_STATUS` (new) with value `Completed`,
  the parallel of `DONE_STATUS` in `tools/set_execution_status.py` line 42, whose existence
  shows a status writer needs one module-level name; the shared module is the right home
  because five tool modules already import it.
- Containment by construction: the constant is defined before `_VALID_STATUSES` (line 298)
  and its name replaces the literal `Completed` inside the frozenset, so REQ-001's "the
  vocabulary contains it" holds structurally, not by coincidence of two literals.
- Public by naming: the module has no `__all__` and follows the re-export convention stated
  in its module docstring (line 5); a bare (no leading underscore) module-level name is the
  public form used by this module's consumers today, so no `__all__` is introduced.
- No alias entry: adding `done` or `Done` to `_STATUS_ALIASES` was rejected — it would
  silently accept the non-standard status the plan removes, contrary to REQ-001.
  `_normalize_status` behavior (including its error text at line 30) stays identical because
  the frozenset contents are unchanged.

## Alternatives considered
- `DONE_STATUS` as the shared name: rejected by plan Design Decision 2 (it lives inside a
  sibling CLI, and changing that tool is out of scope).
- A `Completed`-only `__all__` list in the module: rejected (the module exports many public
  names to `tools/manage_workitem_stage.py`; narrowing exports would be a behavior change).
- Alias mapping for historical `Done` values: rejected above; historical rows are a
  follow-plan concern.

## Implementation
### Target file
`tools/_workitem_status_table.py` (Modify). The path already exists; no (new) marker.

### Procedure
1. Define `COMPLETED_STATUS` (new) as `"Completed"` at module level, immediately before
   `_VALID_STATUSES` (line 298).
2. Replace the literal `Completed` inside the `_VALID_STATUSES` frozenset with the constant
   name, leaving the other four members unchanged.
3. Extend the module docstring with one sentence stating that `COMPLETED_STATUS` (new) is the
   completed-status name status writers import, alongside the existing re-export sentence
   (line 5).

### Method
- One added name and one literal swap; no function, signature, or message changes anywhere
  in the module.
- Every existing use of the vocabulary keeps working unchanged: the membership test in
  `_normalize_status` (line 27), the error message built from `sorted(_VALID_STATUSES)`
  (line 30), the rendered-vocabulary message at line 111, and `_UNFINISHED_STATUSES` (line
  310) all resolve against the same frozenset contents.

### Details
- Placement: between the `EXECUTION_STATUS_HEADING` assignment and `_VALID_STATUSES` so the
  constant is defined before its first use.
- The constant's value is the exact existing string `Completed`; no importer or test asserts
  on identity (`is`) today, only on the value.

## Compatibility considerations
- Importers verified in this cycle: `tools/_detect_unexecuted_archive.py`,
  `tools/manage_workitem_stage.py`, `tools/_workitem_stage_parser.py`,
  `tools/check_workitem_structure.py`, `tools/sync_plan_workitem_status.py`. The change is
  additive for all five; their tests run in plan Phase 5 (REQ-001).
- `tools/set_execution_status.py` keeps its own `DONE_STATUS` (plan Design Decision 2); the
  two names hold the same value and no tool enforces a single symbol yet.
- The seq 04 test asserts the tool-written status equals this constant and belongs to the
  vocabulary (AC-1).

## Security considerations
N/A: a module-level constant; no input, I/O, or new attack surface.

## Rollback considerations
Reverting this file with a single-path `git checkout` breaks the seq 01 import and the seq 04
assertion; revert the seq 01 and seq 04 documents' code in the same commit scope, or none.

## Validation plan
1. `uv run pytest tests/tools/` (the importer tests plus the seq 04 module) — the vocabulary
   error-message tests in the existing suite must stay green.
2. AC-1 vocabulary half: the seq 04 test asserts the written status equals
   `COMPLETED_STATUS` (new) and is in the parsed vocabulary.
3. Full sequence per `rules/toolchain.md` (ruff, mypy, full test suite).

## Completion criteria
- The module defines one public `COMPLETED_STATUS` (new), `_VALID_STATUSES` contains the
  value through the constant, all importer tests and the seq 04 tests pass, and the toolchain
  sequence is green.

## Out of Scope
- Changing `tools/complete_doc_procedure.py` (seq 01 document).
- Changing `tools/set_execution_status.py` or any other importer.
- Historical `Done` rows in archived procedures (follow-up plan
  plans/20261117-134130_wftoolfu002_doc-procedure-archival.md).
- `tools/TOOL_DESCRIPTIONS.md` updates (seq 03 document).
- No `docs/*.md` change and no deploy step for this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-204903 | 20261117-205116 | COMPLETED_STATUS defined before _VALID_STATUSES; frozenset literal replaced by the constant; docstring sentence added. |
| 2 | Add or update tests per Validation plan | Completed | 20261117-204903 | 20261117-205116 | No new test needed: the seq 04 vocabulary test covers it (now fails on the tool's 'Done' value, not on the import). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261117-210903 | uv run pytest tests/tools/ -> 4 failed / 2101 passed / 2 skipped; the 4 are the seq 04 Phase 1 gate. ruff/mypy/bandit clean on this file. Full suite deferred to end of batch. Batch-mode validation: ruff format/check, mypy (CI invocation), bandit, lint-imports, ast-grep Not available locally, module-size tools baseline OK, radon, targeted tests, and the full suite twice: run 1 1 failed (tests/rag flaky, unrelated) / 12614 passed, run 2 12615 passed / 7 skipped / 0 failed. coverage xml + diff-cover -> no lines with coverage info (diff is tools/-only, coverage measured on scripts/). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261117-205116 | N/A: no docs/00_index.md task-scope mapping for tools/_workitem_status_table.py. |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261117-123331_wftool002_status-vocabulary-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-124614_wftool002_status-vocabulary-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-180831
- **Related target files**: `tools/_workitem_status_table.py`