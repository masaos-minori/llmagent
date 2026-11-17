## Goal
Create `tests/tools/test_complete_doc_procedure.py` as the characterization and regression
harness for `tools/complete_doc_procedure.py`: written status, step notes, Verification
Findings insertion and its anchors, usage errors, memo line removal, archive refusal, and the
dry run (REQ-004; AC-4). Written first in plan Phase 1 so the seq 01 restructure is pinned by
passing tests before it happens.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file procedure for row 4 of the plan's frozen `Implementation Target Files` table:
`tests/tools/test_complete_doc_procedure.py`. It is a standalone procedure document, not a
companion: two frozen-table rows name it in their `Related Tests` cells, so it fails the
`SKILL.md` companion condition "exactly one other row names it" and keeps its own document.

No production file is touched by this document.

## Assumptions
- Plan phase order and seq order differ: this document is executed first (plan Phase 1),
  before the seq 02 constant exists and before the seq 01 tool change. Do not execute
  documents in raw seq order.
- Phase 1 gate (plan step 1): only the written-status test and the dry-run tests fail against
  the current tool; every other test must pass against the current tool.
- The current tool rewrites the procedure file before it checks the archive destination and
  the memo line match, so on those two failure paths the procedure file is already modified.
  The seq 01 document changes that to validation-first, so this module asserts exit codes,
  stderr messages, memo state, and "not archived" on those paths and deliberately does NOT
  assert the procedure file's content there — the one behavior point the two documents let
  differ, and it is declared in the seq 01 document's Design decisions.
- The written-status test imports COMPLETED_STATUS from `tools._workitem_status_table` inside
  the test function, not at module import time, so before plan Phase 2 only that one test
  errors and the rest of the module still collects and passes.

## Design decisions
- Model file: `tests/tools/test_set_execution_status.py` — module docstring header, a
  `DOC_TEXT` constant holding a realistic procedure document, a `_doc(tmp_path)` fixture
  helper, `main([...])` called with absolute paths in list order, class-per-behavior grouping,
  and a `_rows(path)` helper that re-reads the document's status table after a run.
- No `tmp_path` juggling for the tool's path resolution: the tool resolves a relative argument
  against its `REPO` constant but keeps an absolute path as-is, including for `--memo`
  (pathlib drops the left operand), so every test passes absolute `tmp_path` paths.
- Archive tests repoint the tool's `DONE_DIR` module attribute with `monkeypatch.setattr` to
  a `tmp_path` directory; tests never write into the real `implementations/done/`. This holds
  only while the tool's functions read the module attribute at call time, which the seq 01
  document's Method states.
- Stamps are asserted structurally (Started equals Completed, both non-empty) rather than by
  freezing the clock, because the tool writes one `stamp` value to both cells and pinning the
  clock adds no coverage.
- Characterization scope: current stderr messages are asserted by substring (for example
  `anchor not found`, `no Pending rows`, `archive destination exists`, `no memo line matched`,
  `memo not found, skipped`, `unknown option`, `--vf needs`) so the seq 01 split cannot
  silently drop them; exact full-line equality is asserted only for the row format itself.

## Alternatives considered
- Driving the tool via `subprocess` instead of importing it: rejected — the sibling model
  imports the module and calls `main`, and in-process calls keep monkeypatching `DONE_DIR`
  and reading exit codes simple.
- A `conftest.py` shared fixture for status-writer tests: rejected — the sibling test module
  keeps its fixtures private to its own file; a shared fixture would couple two plans' files.
- Freezing `time.strftime` with monkeypatch: rejected as unnecessary per the design decision
  above.

## Implementation
### Target file
`tests/tools/test_complete_doc_procedure.py` (new). The containing directory `tests/tools/`
exists.

### Procedure
1. Create the module header, the `DOC_TEXT` fixture document (three `Pending` rows plus
   `### Blocker Log`, patterned on the sibling model), and the `_doc`, `_rows` helpers.
2. Write the characterization group that passes against the current tool first: step-note
   filling (`--step1-note`, `--step2-note`, unmatched steps get empty Notes), Notes-cell and
   row-shape handling, Verification Findings insertion (absent section created before
   `### Blocker Log`; existing section untouched — no second table; malformed `--vf` is exit
   2; missing `### Blocker Log` anchor is exit 1), missing `### Execution Status` anchor
   (exit 1), no-Pending-rows (exit 1), usage errors (no arguments, unknown option: exit 2),
   memo line removal by filename (with `--memo` and with the tool's default memo path never
   used in tests — always pass `--memo` explicitly), memo file absent (exit 0 with the skip
   message), archive destination exists (exit 1, message asserted per the Assumptions note),
   and `--no-archive` leaving the file in place.
3. Write the status test: run the tool, read the rows, and assert every written Status equals
   the constant imported inside the test from `tools._workitem_status_table` and belongs to
   the parsed vocabulary — this test fails in Phase 1 (the constant does not exist yet, the
   tool writes `Done`).
4. Write the dry-run group (fails in Phase 1 as a usage error, passes after seq 01):
   `--dry-run` prints a unified diff containing the status-row changes and nothing else is
   printed as a write confirmation; the procedure file, the memo file, and the monkeypatched
   archive directory are byte-for-byte unchanged and no temporary staged file is left behind;
   dry run against a broken document returns the same exit code and stderr message the real
   run would (missing anchor: 1; taken archive destination: 1; no memo line: 1; unknown
   option: 2).

### Method
- One class per behavior group (`TestStatusRows` (new), `TestVerificationFindings` (new),
  `TestUsage` (new), `TestMemoAndArchive` (new), `TestDryRun` (new)), each docstring stating
  the invariant it pins.
- Every assertion is against files under `tmp_path`; the only module attributes repointed are
  the tool's `DONE_DIR` via monkeypatch (auto-restored).
- Phase gate inside this file's own creation order: steps 2 tests first, then steps 3-4, so
  `uv run pytest tests/tools/test_complete_doc_procedure.py` initially shows exactly the two
  expected failing groups.

### Details
- The tool under test today: rows are set only when the Status cell is exactly `Pending`; all
  rewritten rows share one stamp value; the findings table is inserted only when `--vf` is
  given and the section is absent; the memo line is matched by filename substring; archive
  refuses when `DONE_DIR / proc.name` exists.
- `DOC_TEXT` must contain a Notes cell with backticked text in it (as the sibling model's
  fixture does) so cell-splitting is exercised on non-empty notes.

## Compatibility considerations
- The tests call `main` with a positional list; that call shape is valid against the current
  `main(argv: list[str])` and the seq 01 target `main(argv: list[str] | None = None) -> int`.
- The written-status test's vocabulary assertion imports the shared parse helper
  `parse_execution_status_rows`, so it also guards the seq 02 vocabulary change indirectly.
- pytest collection requires the file under the existing `tests/tools/` layout; no new
  conftest, marker, or fixture registration is needed.

## Security considerations
N/A: tests run only against `tmp_path` fixtures; the real `implementations/done/` and
`memo3.md` are never written.

## Rollback considerations
Deleting this single file removes the harness; the seq 01 and seq 02 documents depend on it
for validation, so a rollback of this row means halting those rows' validation too. A revert
of this file alone never changes production behavior.

## Validation plan
1. `uv run pytest tests/tools/test_complete_doc_procedure.py -v` at creation time: exactly the
   status group and the dry-run group fail; all other tests pass (plan Phase 1 gate).
2. After the seq 02 document lands: the status test passes.
3. After the seq 01 document lands: the whole module passes, including the dry-run group
   (AC-4, AC-2).
4. Full sequence per `rules/toolchain.md` in plan Phase 5.

## Completion criteria
- AC-4 holds: the module covers every behavior listed in REQ-004 and passes once its two
  dependency documents have landed; the Phase 1 gate (exactly the two groups failing before
  them) was demonstrated.

## Out of Scope
- Any change to `tools/complete_doc_procedure.py` (seq 01) or `tools/_workitem_status_table.py`
  (seq 02).
- Tests for other status writers (the sibling test module already covers its tool).
- Historical `Done` rows in archived procedures (follow-up plan scope).
- No `docs/*.md` change and no deploy step for this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-203657 | 20261117-204850 | Test module created: 24 tests, 5 behavior classes. |
| 2 | Add or update tests per Validation plan | Completed | 20261117-203657 | 20261117-204850 | Characterization group (20 tests) green against the unmodified tool. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261117-210903 | Targeted run: 4 failed / 20 passed twice, deterministic. The 4 are the plan-sanctioned Phase 1 gate (written-status test + 3 dry-run tests). ruff/mypy/bandit run: only mypy error is the missing COMPLETED_STATUS import, same gate. Full suite deferred to end of batch. Batch-mode validation: ruff format/check, mypy (CI invocation), bandit, lint-imports, ast-grep Not available locally, module-size tools baseline OK, radon, targeted tests, and the full suite twice: run 1 1 failed (tests/rag flaky, unrelated) / 12614 passed, run 2 12615 passed / 7 skipped / 0 failed. coverage xml + diff-cover -> no lines with coverage info (diff is tools/-only, coverage measured on scripts/). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261117-204850 | N/A: no docs/00_index.md task-scope mapping for tests/tools/test_complete_doc_procedure.py. |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261117-123331_wftool002_status-vocabulary-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-124614_wftool002_status-vocabulary-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-180831
- **Related target files**: `tests/tools/test_complete_doc_procedure.py`