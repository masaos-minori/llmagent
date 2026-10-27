# Extend check_adr_invariant_matrix.py to detect empty verification evidence in ADR bodies

## Priority
Medium

## Summary
`tools/check_adr_invariant_matrix.py` verifies only the test paths cited in the ADR index matrix. An invariant whose Implementation cell in an ADR body is empty (`-`) without a not-verified status is not detected. Extend the checker so that this gap, and a disagreement between an ADR body and the index for the same invariant, are reported.

## Background
- The checker's docstring states that it extracts backtick-quoted `path::test_name` references from the Verification Status column of the index matrix and fails when the file component does not exist. It does not read ADR bodies. Evidence: `Explicit in code` (`tools/check_adr_invariant_matrix.py` module docstring).
- Empty Implementation cells (`-`) currently exist in the Automated Tests tables of at least three ADR bodies: ADR-001, ADR-002 and ADR-003 (`adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`). A text search for table rows ending in an empty cell found 5, 2 and 6 rows respectively. Evidence: `Explicit in code` (search result; whether every such row is an Automated Tests row is `Needs confirmation`).
- The checker runs as a pre-commit hook (`.pre-commit-config.yaml`) and is loaded by file path from `.github/run_cited_adr_tests.py`, which reuses its node-id regex. Evidence: `Explicit in code`.
- A test module exists for the checker (`tests/tools/test_check_adr_invariant_matrix.py`). Evidence: `Explicit in code`.
- The ADR-001/ADR-002 evidence cleanup is tracked in `issues/20261027-101918_govrev004_adr-verification-evidence-sync.md`; ADR-003 is not covered by any issue in this batch. No open issue or in-flight plan overlaps the checker (checked `issues/` and `plans/`).

## Problem
The gap that the evidence-cleanup issue removes can reappear unnoticed, because no automated check reads the ADR body evidence. A body and the index can also diverge for the same invariant without any signal.

## Reason for Change
Without a guard, the cleanup of ADR-001 and ADR-002 is a one-time fix. Sequencing matters: enabling a blocking rule before the corpus is clean would fail pre-commit and CI for unrelated changes, so the change must follow the cleanup or start as a warning.

## Implementation Intent
Add two rules to the existing checker, keeping its structure and exit-code contract: (1) an ADR body Automated Tests row whose Implementation cell is empty MUST carry an explicit not-verified marker defined by the Verification Status vocabulary; (2) when an invariant appears in both an ADR body and the index matrix, the cited test paths MUST agree. Choose the severity (warning or error) after a survey of the current corpus, so that the rule does not break unrelated changes. Preserve the public behavior that existing callers rely on: the node-id regex reuse by `.github/run_cited_adr_tests.py`, the `--format json` output and the current exit codes for the existing rule.

## Target Files or Areas
- `tools/check_adr_invariant_matrix.py`
- `tests/tools/test_check_adr_invariant_matrix.py`
- `tools/TOOL_DESCRIPTIONS.md` (entry update)
- Read-only: `.pre-commit-config.yaml`, `.github/run_cited_adr_tests.py`, `docs/10_adr/adr_02_*.md`

## Required Changes
- Survey the current ADR bodies for empty Implementation cells and for body/index disagreement; record the result in the implementation notes.
- Implement rule (1) and rule (2) in the checker with a configurable or documented severity.
- Add tests covering: empty cell without marker, empty cell with marker, matching and disagreeing body/index citations, and the first and last rows of a table.
- Update the checker docstring and the `TOOL_DESCRIPTIONS.md` entry.
- Confirm that `.github/run_cited_adr_tests.py` still loads the module and its regex unchanged.

## Constraints
- Do not break the existing rule, its JSON output, or the import by `.github/run_cited_adr_tests.py`.
- The checker is read-only and MUST NOT modify ADR files.
- Follow `rules/coding.md` (English comments, `orjson` for JSON, line length 88) and the tool validation sequence in `routing.md` "Adding a new tool" (ruff, mypy with an explicit file path, bandit, smoke test on live `docs/10_adr/` data, `check_tool_descriptions_sync.py`).
- The impact radius MUST be measured before changing shared helpers (`rules/toolchain.md` Impact-radius check).

## Acceptance Criteria
- The checker reports an empty ADR body Implementation cell that lacks a not-verified marker, and reports a body/index citation disagreement.
- Running the checker on the repository after the ADR-001/ADR-002 evidence issue is complete produces no new failure from rule (1) for those two ADRs; the handling of ADR-003 follows the decided severity.
- All existing tests of the checker still pass, and new tests cover the cases listed under Required Changes.
- `uv run ruff check tools/check_adr_invariant_matrix.py`, `uv run mypy tools/check_adr_invariant_matrix.py` and `uv run bandit tools/check_adr_invariant_matrix.py` pass.
- `uv run python tools/check_tool_descriptions_sync.py` passes.

## Testing Expectations
- `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -v` (extended).
- `uv run ruff format` and `uv run ruff check` on the changed files; `uv run mypy tools/check_adr_invariant_matrix.py` (path passed explicitly).
- `uv run bandit tools/check_adr_invariant_matrix.py`.
- Smoke test: `uv run python tools/check_adr_invariant_matrix.py` and `--format json` on the live repository.
- `uv run python tools/check_tool_descriptions_sync.py`.
- `uv run pre-commit run adr-invariant-matrix --all-files` (hook id from `.pre-commit-config.yaml`).

## Documentation Impact
`tools/TOOL_DESCRIPTIONS.md` must be updated (what the checker verifies and its new rules). If the severity is a warning, the corpus-wide gap is a candidate Known Issue or Accepted Limit entry decided by the repository owner. No `docs/10_adr/` change is made by this issue.

## Out of Scope
- Fixing the empty cells in ADR-001, ADR-002 or ADR-003 (ADR-001 and ADR-002 are in the dependency issue; ADR-003 is untracked).
- Making the index matrix machine-generated.
- Running the cited tests to confirm they pass (a separate, documented sub-step of GV-012).
- Defining the Verification Status vocabulary.

## Dependencies
- Depends on `issues/20261027-101850_govrev003_partial-verification-gate-rules.md`: the not-verified marker used by rule (1) is defined there.
- Depends on `issues/20261027-101918_govrev004_adr-verification-evidence-sync.md`: complete the ADR-001 and ADR-002 cleanup before enabling a blocking rule, or start with warning severity.

## Unresolved Questions
- Should ADR-003's empty cells be tracked in a separate issue? `不明` (outside the memo that produced this batch).
- Severity of rule (1): warning first, or error after the corpus is clean? `不明`; recommendation is warning until ADR-003 is resolved.
- Is every `-` found by the text search an Automated Tests Implementation cell? `Needs confirmation`.

## AI Implementation Instruction
Change only the checker, its test module and its `TOOL_DESCRIPTIONS.md` entry. Keep the existing rule and its output stable. Do not modify ADR files. Add tests with the change. Write comments in English. Stop and report if the survey shows that enabling the rule as an error would fail on documents outside this batch.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-102002
- **Related target files**: `tools/check_adr_invariant_matrix.py`, `tests/tools/test_check_adr_invariant_matrix.py`, `tools/TOOL_DESCRIPTIONS.md`
