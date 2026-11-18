# Procedure: tests/tools/test_complete_doc_procedure.py - refusal and archival test coverage

## Goal

Lock the unfinished-row refusal, the location refusal, and the sanctioned archival with tests, and restructure the fixtures so the tests exercise the real repository layout (documents under `implementations/`, a real `implementations/done/`, Git staging) instead of the monkeypatched `DONE_DIR` and root-level documents that REQ-001 and REQ-003 remove.

## Scope
**Release unit**: N/A: not part of a release unit

- Add tests for: unfinished rows (`In Progress`, `Blocked`) blocking the archive; a finished procedure moved and staged as a rename; `--no-archive` updating rows without the refusal; dry-run refusal; taken destination; missing memo line; location refusal; memo line removed after the move. (REQ-006)
- Restructure existing fixtures so archival tests use a temporary Git repository and documents inside `implementations/`; the fixture commits the procedure before the run so that the move shows as a rename.
- Replace the characterization that the archived copy holds a `Blocked` row: such a document is now refused, not archived.

## Assumptions

- The test module already exists (16406 B) and is modified, not created.
- `stage_only=True` produces a staged rename (`git mv`), so the tests inspect the Git index rather than assuming a commit; the tool never commits.
- Refusal messages reuse `describe_rows`, so tests assert on step numbers and statuses rather than exact full sentences.
- The repository fixture follows the precedent named in the plan's target-row evidence: `tests/tools/test_manage_workitem_stage.py` builds a temporary repository with `git.Repo.init` and a committed `.gitkeep`; no network remote is involved (`origin` absent degrades the remote check to a no-op).

## Design decisions

- Fixture design is this module's own decision (the reason it gets its own document rather than being a companion row): a repository helper creates a repository containing `implementations/` and `implementations/done/`, monkeypatches `cdp.IMPLEMENTATIONS_DIR` and `cdp.DONE_DIR` to the temporary layout, and writes procedure documents directly under `implementations/` — the placement the new location refusal requires of every run, `--no-archive` included. The current module monkeypatches only `cdp.DONE_DIR` and writes documents at the repository root.
- Document fixtures come in two variants: a finished variant (all rows `Completed`) and unfinished variants carrying `In Progress` and `Blocked` rows. The current `DOC_TEXT` fixture holds a `Blocked` row and becomes the unfinished variant.
- Refusal assertions check three things together: the exit code, a message naming the offending row or path, and byte-identity of the source plus absence of any new file in `done/` (the AC-2 shape).

## Alternatives considered

- Keep the monkeypatched-`DONE_DIR` root-level fixtures and add the new tests on top. Rejected: the location refusal refuses exactly the root-level placement those fixtures use, and REQ-001 removes the archival role the monkeypatch stubs; keeping them would encode the behavior this change removes.
- Call the tool through a subprocess. Rejected: the module already calls `cdp.main(argv)` directly; subprocess assertions would add Git-in-subprocess flakiness for no additional coverage.
- One combined refusal test looping over statuses. Rejected: per-status tests give a failing status a named test, matching the existing one-behavior-per-test style of this module and of `tests/tools/test_workitem_stage_archive.py`.

## Implementation

### Target file

`tests/tools/test_complete_doc_procedure.py` (exists, 16406 B)

### Procedure

1. Add a repository helper that initializes a temporary Git repository, creates `implementations/` and `implementations/done/`, commits a seed file so the repository has a HEAD, monkeypatches `cdp.IMPLEMENTATIONS_DIR` and `cdp.DONE_DIR`, and commits each procedure document before the tool run so the archival move appears as a rename in the index.
2. Split the document fixtures into the finished and unfinished variants described in Design decisions, keeping the existing `_doc`, `_memo`, `_rows`, and `_digest` helpers and the existing text fixtures (`DOC_TEXT` becomes the unfinished variant, alongside `NO_ANCHOR_TEXT` and `NO_PENDING_TEXT`).
3. Add tests:
   - unfinished-row refusal, one test per `In Progress` and `Blocked`: exit 1, the message names the step and status, the source bytes are unchanged, and `done/` gains nothing.
   - sanctioned archival: a finished document under `implementations/` completes with the default archival; the file lands in `implementations/done/` carrying the stamped rows; the original path is gone; the index shows a rename (R) into `implementations/done/` whose staged blob equals the rewritten text; the tool leaves nothing committed.
   - `--no-archive` on an unfinished document updates the `Pending` rows in place with no refusal (the refusal is archive-scoped).
   - taken destination: a file of the same name already in `implementations/done/` exits 1 naming the destination before any write.
   - location refusal: a document at the repository root or inside `implementations/done/` exits 2 with nothing changed, with and without `--no-archive`.
   - dry run: `--dry-run` on an unfinished archived document exits 1 like the real run and changes nothing; on a finished document it prints the intended diffs and archive move without writing, moving, or editing the memo.
   - memo order: a refused run leaves the memo line intact; a successful archived run removes it (extends the existing memo tests).
4. Update the existing archival and memo tests to the new fixtures: `test_memo_line_is_removed_by_filename` and its neighbors assert completed rows in the archived copy instead of the old `Blocked` row, and every fixture document moves under `implementations/`. Keep `test_taken_archive_destination_is_exit_1` and `test_no_memo_line_match_is_exit_1` as the existing anchors of the refusal family and add the new refusal tests beside them.
5. Keep the Verification Findings insertion tests (`--vf` rows) working against finished fixtures.

### Method

Modify in place with targeted edits; add the repository helper near the existing fixture helpers at the top of the module.

### Details

- Assert the staged rename with Git plumbing: `git diff --cached --name-status` reports `R` into `implementations/done/`, and the staged blob matches the rewritten document text.
- Message assertions stay substring-level (step number plus status word, or the offending path) so wording edits in the tool do not break tests.
- Keep the findings-insertion and stamp-replacement tests (the ones using the `FINDINGS_TEXT` fixture) as-is; they are stamping behavior, not refusal behavior.

## Compatibility considerations

- The old characterization that a `Blocked` document gets stamped and archived is deliberately replaced (Plan Assumption): such a document is now refused. No other test relies on the tool archiving unfinished documents; the tool has no importers.
- Existing `--no-archive` tests stay valid only because their fixture documents move under `implementations/`; the refusal itself stays archive-scoped.

## Security considerations

- Git is driven through the same mechanism the sibling stage tests use; no shell strings. Tests stay free of assertion-bypass patterns so `bandit` treats the module cleanly.

## Rollback considerations

- Reverting this module restores the previous fixtures and characterizations together with the reverted tool; the tool document and this document are one behavioral unit and revert together.

## Validation plan

- `uv run pytest tests/tools/test_complete_doc_procedure.py -v` — the new refusal and archival tests fail against the current tool implementation before `implementations/20261118-070621_01_tools_complete_doc_procedure.py.md` is applied, and pass after it (plan Phase 1 order).
- `uv run ruff format tools tests/tools` and `uv run ruff check tools tests/tools`.
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`.

## Completion criteria

- AC-6: each of REQ-001 to REQ-005 has a named test that fails before the tool change and passes after it, using a temporary Git repository.
- AC-2 and AC-3 are asserted in the refusal shape (exit code, named offender, byte-identity, absent destination).
- The full module passes pytest, ruff, and mypy.

## Out of Scope

- Tests for `move_to_done` itself (owned by `tests/tools/test_workitem_stage_archive.py` and `tests/tools/test_manage_workitem_stage.py`).
- Changing `tools/check_workitem_structure.py --archived-status` or its baseline file.
- End-to-end batch runs over the real `implementations/done/` tree; the smoke run belongs to the plan's Phase 5, not this module.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261117-132202_wftoolfu002_doc-procedure-archival.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-134130_wftoolfu002_doc-procedure-archival.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-070621
- **Related target files**: `tests/tools/test_complete_doc_procedure.py`, `tools/complete_doc_procedure.py`
