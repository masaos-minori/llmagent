## Goal
Fix `REQ-001`: create `tools/check_adr_invariant_matrix.py`, which parses `docs/adr-index.md`'s
ADR Invariant Verification Matrix and fails when a cited test path does not exist.

## Scope
Create exactly `tools/check_adr_invariant_matrix.py` (new file). No other file is modified
by this row.

## Assumptions
- The matrix table format (confirmed by reading `docs/adr-index.md`'s "ADR Invariant
  Verification Matrix" section) is
  `| INV | ADR | Invariant | Type | Timing | Gate | Verification Status |`, with a
  backtick-quoted pytest node id (e.g.
  `` `tests/agent/test_startup.py::test_aborts_on_missing_workflow_definition` ``) sometimes
  embedded in the `Verification Status` cell.
- Not every backtick-quoted string in that column is a test path — e.g. INV-003's cell
  contains `` `config_loader.py` `restrict_to()` ``, a code reference, not a pytest node id.
  The extraction pattern must require both a `.py` file segment and a `::` separator to
  avoid a false positive here.
- Rows whose `Verification Status` says "no test yet" / "Not verified" / "Not implemented"
  (with no backtick-quoted test path) are correctly out of scope — they document a known,
  accepted gap, not a regression to flag.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("validate only at system
boundaries"; avoid speculative abstraction): model this tool's structure (argument parsing,
`main()`/exit-code shape) on `tools/check_known_deviation_sync.py`, the closest existing
precedent for a doc-parsing compliance checker, for consistency with the `tools/check_*.py`
family — not a bespoke structure. Reduce the check to one literal claim: does the
backtick-quoted pytest node id's file component exist on disk. Do not attempt to run the
cited test as part of this check (that is the separate, optional CI-side sub-step the
source Issue names as UNK-02 in the Plan — out of scope for this row unless the Plan is
revised to include it).

## Alternatives considered
- Also running each cited test to confirm it passes (not just that the path exists): out of
  scope for this row per the Plan's own phrasing ("optionally, as a separate CI step") —
  implementing it here would exceed this row's `Implementation Target Files` entry.
- A YAML/JSON-based pattern registry instead of parsing the Markdown table directly:
  rejected — `docs/adr-index.md` is the single source of truth per the Plan's Background; a
  separate registry would drift from it, the exact failure mode GV-014 exists to prevent.

## Implementation
### Target file
`tools/check_adr_invariant_matrix.py`

### Procedure
Parse the Markdown table under `docs/adr-index.md`'s `## ADR Invariant Verification Matrix`
heading; for each row, extract any `` `path/to/file.py::test_name` ``-shaped substring from
the `Verification Status` cell; fail (non-zero exit) if the file component does not exist
relative to the repository root.

### Method
1. Read `tools/check_known_deviation_sync.py` in full to confirm its argument-parsing,
   `--format json`, and `report_and_exit`-style exit-code conventions.
2. Implement a Markdown table parser scoped to the `## ADR Invariant Verification Matrix`
   section (locate the heading, read rows until the next `## ` heading), splitting each row
   on `|`.
3. Implement the test-path extraction regex requiring a `.py` segment followed by `::` (per
   Assumptions, to exclude code-reference cells like INV-003's).
4. For each extracted path, resolve it relative to the repository root and check existence
   with `pathlib.Path.exists()`.
5. Emit one issue per unresolved path, following the existing `Issue`/`report_and_exit`
   pattern from `tools/check_known_deviation_sync.py` (or an equivalent shared helper if one
   already exists — check `tools/_docs_consistency_lib.py`, used by other `tools/check_*.py`
   scripts, before writing a new pattern).

### Details
- `docs/adr-index.md`'s current matrix rows were read directly (INV-001 through at least
  INV-020) and confirmed to contain a mix of resolvable test paths (e.g.
  `tests/agent/test_startup.py::test_aborts_on_missing_workflow_definition`), code-reference
  cells (INV-003), and no-test-yet rows — all three cases the extraction logic must handle
  correctly per Assumptions.
- No Plan-level inconsistency was found for this row beyond the already-corrected `Design`/
  `Risks`/Requirement Traceability sections and the newly-added `tools/check_adr_reference.py`
  row (see the Plan's own history — corrected 2026-09-02 during this cycle's Step 3).

## Compatibility considerations
N/A: new file, no existing interface changes. Does not modify `docs/adr-index.md` or any
existing `tools/*.py` file.

## Security considerations
Read-only file-existence checks against paths extracted from a trusted, repository-internal
document; no external input, no code execution of the cited test.

## Rollback considerations
Trivially revertable: delete the new file. No other file references it until the
`.pre-commit-config.yaml`/`ci.yml` wiring rows (this Plan's other rows) are implemented.

## Validation plan
- `uv run python tools/check_adr_invariant_matrix.py` against the current repository —
  expect zero false positives (every currently-cited test path must exist).
- `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -v` (new test file, per this
  Plan's own Tests section) — covers: a resolvable path, an unresolvable path (should fail),
  a code-reference cell like INV-003's (should not be treated as a test path), and a
  no-test-yet row (should be skipped, not flagged).

## Completion criteria
The tool exits non-zero only when a cited test path does not resolve to an existing file;
it exits zero against the current, correct `docs/adr-index.md` content; it does not flag
INV-003-style code-reference cells or no-test-yet rows as failures.

## Out of scope
Running the cited tests to confirm they pass (optional future CI sub-step, not this row).
`tools/check_compat_shims.py`, `tools/check_adr_reference.py`, `.pre-commit-config.yaml`,
`.github/workflows/ci.yml`, `docs/00_governance_04_documentation-checks.md` — each covered
by its own implementation procedure document for this same Plan.

## Documentation
`tools/check_adr_invariant_matrix.py` has no matching row in `docs/00_index.md`'s "Document
References by Task" table — no `docs/*.md` update applies (Step 5: `N/A: no docs/00_index.md
task-scope mapping for tools/check_adr_invariant_matrix.py`). Step 6 content checks skipped
accordingly.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read `check_known_deviation_sync.py` and `_docs_consistency_lib.py` | Completed | 2026-09-02 | 2026-09-02 | Modeled structure on `check_known_deviation_sync.py`; used `Issue`/`report_and_exit` directly from `_docs_consistency_lib`, no `DocFile`/`discover_md_files` needed since only one file (`docs/adr-index.md`) is read |
| 2 | Implement matrix parser and test-path extraction | Completed | 2026-09-02 | 2026-09-02 | Regex requires a `.py` + `::` pair inside backticks, confirmed to correctly skip INV-003's code-reference cell (no `::`) |
| 3 | Add tests under `tests/tools/` | Completed | 2026-09-02 | 2026-09-02 | 6 tests, all pass: resolvable path, unresolvable path, code-reference cell, no-test-yet row, multiple rows, missing heading |
| 4 | Run against live repository; confirm zero false positives | Completed | 2026-09-02 | 2026-09-02 | `uv run python tools/check_adr_invariant_matrix.py` → "No issues found.", exit 0 |
| 5 | Validation | Completed | 2026-09-02 | 2026-09-02 | `ruff`/`mypy`/`bandit` clean on both new files; `lint-imports` shows one pre-existing, unrelated broken contract (`shared.production_config_validator -> agent.tool_policy`) not touched by this row |

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
- **Requirement ID**: REQ-001 (Invariant Matrix test-path verification)
- **Source issue**: `issues/20260901-183941_gv014ci_adr-compliance-ci-check-for-gv-014.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-220712_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-111416
- **Related target files**: `tools/check_adr_invariant_matrix.py`
