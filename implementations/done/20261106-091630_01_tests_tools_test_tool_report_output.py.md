## Goal
Record golden outputs of the four tools to be migrated, as tests that pass against the unmigrated tools first, so every later migration is checked byte for byte (`REQ-006`: golden-output and determinism tests recorded before migration).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one new test file covering default text, `--format json`, and (traceability only) `--format csv` for the four tools, plus determinism of repeated runs.
- Out of scope: unit tests of the shared module (the companion of the `tools/_report.py` procedure), any tool change.

## Assumptions
- Verified on 2026-11-06 (Step 3a): `tests/tools/test_report.py` and `tests/tools/test_tool_report_output.py` do not exist. The four tools expose `main(argv) -> int` and print to stdout; `check_adr_authority.py` prints its text findings to stdout and the `Found N finding(s).` summary to stderr, and the two ADR checkers print text through `report_and_exit` in `tools/_docs_consistency_lib.py` (stdout lines, stderr summary, `No issues found.` on stdout when clean); `check_workitem_traceability.py` prints grouped text, JSON with sorted keys, or CSV with `\r\n` line endings.
- Existing fixtures to reuse in style: `tests/tools/test_check_adr_invariant_matrix.py` `TestCollectIssues._repo` (patches `checker.REPO_ROOT` and `checker.ADR_INDEX`), `tests/tools/test_adr_authority.py` CLI tests (`--model`, `--adr-dir`, `--config` options), and `tests/tools/test_check_workitem_traceability.py` (patches `cwt.ROOT_DIR`).
- This file is NOT a companion: no other row of the Plan names it in `Related Tests`, and its expected values need a record-first step, so it keeps its own procedure document. It is `seq` 01 because the Plan's phase 2 records the goldens before the shared module exists.
- Sequencing: the `toolcommon001` procedures (archived Plan) are expected to execute first; if `check_workitem_traceability.py` has already moved to `ROOT_DIR = REPO_ROOT`, the fixture keeps patching `cwt.ROOT_DIR`, which still works.
- Overlap judgment: no other open Plan targets this new file.

## Design decisions
- Expected strings are constants inside the test file, recorded from the unmigrated tools. They are never regenerated from migrated code; a later diff against them is the regression signal.
- Each case asserts exit code, stdout, and stderr separately, because the text tools split output across streams.

## Alternatives considered
- Snapshot files under `tests/`: rejected, inline constants keep one reviewable file and need no fixture-loading code.

## Implementation
### Target file
`tests/tools/test_tool_report_output.py` (new)

### Procedure
1. For each tool build a fixture that yields at least one finding of every kind its output path prints, using the existing fixture styles above (a minimal repository or model under `tmp_path`, module constants patched with `monkeypatch`).
2. Write the test with an empty expected value, run it against the unmigrated tools, and paste the exact captured output into the expected constants; commit nothing until every case passes against the unmigrated code.
3. Cases: `check_adr_authority.py` text and JSON (one `MODEL_INVALID` finding from an invalid model and one validation finding), `check_adr_reference.py` text and JSON (index missing and a marker mismatch), `check_adr_invariant_matrix.py` text and JSON (reuse the body-rule fixture), `check_workitem_traceability.py` text, JSON, and CSV (a missing source file and a target-file mismatch), and an empty-findings case per tool (`No findings.`, `No issues found.`, `Authority model OK: no findings.`, JSON `[]`).
4. Add a determinism test: run each JSON mode twice and assert identical strings.

### Method
- Call `main([...])` in-process and read `capsys.readouterr()`; assert `out` and `err` separately.
- Parametrize by tool with one fixture function per tool returning the argument list.

### Details
- Keep paths in expected output relative or fixed by the fixture (`tmp_path` values vary): replace the temporary root in captured text before comparing, in a small `_normalize` helper (new) local to the test file.
- Do not import `render_json`, `render_text`, `render_csv`, or `make_finding`: the file MUST survive their removal.

## Compatibility considerations
- N/A: new test file only; it must pass both before and after every migration without edits.

## Security considerations
- N/A: temporary files only; no network and no production path (tests run under the isolated root of `tests/conftest.py`).

## Rollback considerations
- N/A: delete the file.

## Validation plan
- `uv run pytest tests/tools/test_tool_report_output.py -q` passes against the unmigrated tools, then again after each migration procedure of this Plan.
- Mutation check: change one character in a tool's text output locally and confirm a case fails, then revert.
- `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy --no-namespace-packages tests/tools/test_tool_report_output.py`; `uv run python tools/check_mock_patch_targets.py`.

## Completion criteria
- Text and JSON cases exist for the three ADR-related tools, text, JSON, and CSV cases for the traceability tool, an empty-findings case per tool, and a determinism test; all pass on the unmigrated code and fail on a deliberate one-character output change.

## Out of Scope
- Changing any tool, the shared module's own unit tests, documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Build the fixtures and record the expected outputs from the unmigrated tools | Completed | 20261106-113556 | 20261106-113725 | Changed: tests/tools/test_tool_report_output.py (new; goldens recorded from the unmigrated tools, 26 tests) |
| 2 | Add the empty-findings and determinism cases | Completed | 20261106-113725 | 20261106-113725 | 26 tests pass on the unmigrated tools; mutation check (one output character) fails as expected |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the mutation check | Completed | 20261106-113725 | 20261106-113725 | ruff, mypy, mock-patch checker clean |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-113725 | 20261106-113725 | N/A: documentation is another procedure of this Plan |

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
- **Requirement ID**: `REQ-006` (golden-output and determinism tests)
- **Source issue**: issues/20261104-152906_toolreport001_share-report-model-and-renderers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110046_toolreport001_share-report-model-and-renderers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-091630
- **Related target files**: `tests/tools/test_tool_report_output.py`
