# Promote ADR evidence checks to blocking and validate cited pytest nodes

## Priority
Medium

## Summary
Finish the ADR verification enforcement started by `govrev003` to `govrev005`: promote the body-evidence rules of `tools/check_adr_invariant_matrix.py` from warning to error once the corpus is clean, verify that cited pytest nodes exist (not only their files), and restrict ADR references in source files to structured markers.

## Background
Source: `memo-issue.md` Issue 05, re-verified against current source on 2026-10-27. Most of the memo is already done by `issues/done/20261027-101850_govrev003_partial-verification-gate-rules.md`, `issues/done/20261027-101918_govrev004_adr-verification-evidence-sync.md` and `issues/done/20261027-102002_govrev005_adr-matrix-checker-extension.md` (commit `9d3094ee8`). This issue covers only what remains.

- `tools/check_adr_invariant_matrix.py` extracts `` `path.py::node` `` citations and fails only when the file component is missing; the node component is not checked. `Explicit in code` (module docstring and `_TEST_PATH_RE`).
- The two body rules (empty Implementation cell, body/index disagreement) use `_BODY_RULE_SEVERITY = "WARNING"`, with a note to promote them to `ERROR` once the survey is clean. `Explicit in code`.
- A run on 2026-10-27 reported 14 warnings: 6 empty Implementation cells in `adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` (INV-01, 02, 03, 04, 06, 07) and 8 body/index citation differences (for example ADR-002 INV-01 and INV-02, ADR-005 INV-02, ADR-006 INV-09, ADR-007 INV-09). `Operationally observed`.
- `tools/check_adr_reference.py` treats a source file as self-identifying when the ADR ID appears somewhere in its text. `Explicit in code` (module docstring).

## Problem
Blocking-invariant evidence can still pass CI when the cited test function was renamed or removed, when body and index cite different tests, or when a source file mentions the ADR ID incidentally.

## Reason for Change
The checker was deliberately shipped with warnings until the corpus is clean; the corpus now has a known, finite list of findings, so the promotion is unblocked once they are resolved. Until then stale evidence is not blocking.

## Implementation Intent
Resolve the listed findings (cite a test or record `Not verified` per the vocabulary defined in govrev003), then raise the rule severity to `ERROR`. Add node validation through pytest collection (or an equivalent AST check) and a structured-marker rule for source references. Keep the checker read-only and keep its import by `.github/run_cited_adr_tests.py` working.

## Target Files or Areas
- `tools/check_adr_invariant_matrix.py`, `tests/tools/test_check_adr_invariant_matrix.py`
- `tools/check_adr_reference.py` and its tests
- `docs/10_adr/adr_01_index.md` and ADR bodies listed in the current warnings (for example `adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`)
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Resolve the current 14 warnings (cite evidence or record `Not verified` consistently in body and index).
- Promote the body-evidence rules from `WARNING` to `ERROR` after the corpus is clean.
- Validate that each cited `file::node` exists (collection or AST), including parameterized ids as defined by the cited form.
- Replace the ADR-ID substring match in `check_adr_reference.py` with a structured marker (comment form to be defined in the issue's plan).
- Update the checker docstrings and `TOOL_DESCRIPTIONS.md`.

## Constraints
- Do not lower any Blocking Gate or change invariant statements; `tools/check_adr_preservation.py` must report no unintended ERROR.
- The checker stays read-only and its JSON output and module import by `.github/run_cited_adr_tests.py` must keep working.
- `docs/` edits follow `skills/DESIGN.md` "Docs content policy - remove".

## Acceptance Criteria
- `uv run python tools/check_adr_invariant_matrix.py` reports no warning and exits non-zero on a missing cited node, an empty evidence cell without a marker, or a body/index disagreement.
- A source file that mentions an ADR ID without the structured marker no longer counts as self-identifying.
- New tests cover each new failure mode; existing checker tests pass.

## Testing Expectations
- `uv run pytest tests/tools/test_check_adr_invariant_matrix.py tests/tools/ -k adr`, extended with the new cases.
- Smoke runs of both checkers on the live repository, `uv run python tools/check_tool_descriptions_sync.py`, ruff, mypy and bandit on the changed tools.
- `uv run pre-commit run adr-invariant-matrix --all-files`.

## Documentation Impact
Yes, small. Update the checker description in `tools/TOOL_DESCRIPTIONS.md` and, where the severity is described, `docs/00_governance/governance_04_documentation-checks.md`. Record the gate severity as current behavior only.

## Out of Scope
- Defining the Verification Status vocabulary (done by govrev003).
- Running the full cited test set in CI beyond node existence validation.
- Changing Known Issue and ADR reverse-reference severity (`check_known_deviation_sync.py`).

## Dependencies
N/A: none open. Builds on the completed `issues/done/20261027-102002_govrev005_adr-matrix-checker-extension.md`; re-verify the warning list against current source before starting because ADR bodies may change.

## Unresolved Questions
- Which marker form should source files use for ADR references? `Needs confirmation` (design decision).
- Should node validation use pytest collection (slower, needs test imports) or an AST scan? `Needs confirmation`.
- When should reverse Known Issue/ADR mismatches become errors? `Needs confirmation`; excluded from this issue.

## AI Implementation Instruction
Resolve the corpus findings first, then change severities; do not promote the rules while any warning remains. Keep tool changes minimal and follow the tool validation sequence in `routing.md`. Stop and report if a finding cannot be resolved without changing an ADR Decision.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-155848
- **Related target files**: `tools/check_adr_invariant_matrix.py`, `tests/tools/test_check_adr_invariant_matrix.py`, `tools/check_adr_reference.py`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `tools/TOOL_DESCRIPTIONS.md`
