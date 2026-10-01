# Fix CANONICAL-006 false positives in check_canonical_source_conflicts.py validation-error wrapping

## Priority
Medium

## Summary
`tools/check_canonical_source_conflicts.py` attributes every registry validation error to every registry entry. As a result it reports CANONICAL-006 ("Multiple source_paths (1) for claim_type 'runtime-behavior' ...") for `eventbus.core-behavior`, an entry that has a single source path and an exempt claim type. Fix the error-to-entry mapping so each finding is reported only for the entry that caused it.

## Background
- The Policy requires the Canonical Source Conflict check to pass as part of documentation verification (`routing.md` "When to run which tool", and the `canon001` work instruction).
- When `validate_registry_schema()` returns errors, the checker converts them with `_wrap_validation_errors(errors, entries)`. `Explicit in code`

## Problem
- `_wrap_validation_errors()` iterates `for entry in entries: for err in errors:` and builds a finding from the current `entry` whenever the error text matches a pattern, without checking that the error refers to that entry. `Explicit in code`
- Observed output (2026-10-01) with the current Registry:
  - `CANONICAL-006 ... Multiple source_paths (1) for claim_type 'runtime-behavior' on entry targeting 'eventbus.core-behavior'` — false positive (1 path, exempt claim type).
  - `CANONICAL-006 ... Multiple source_paths (2) for claim_type 'database-schema' on entry targeting 'eventbus.persistence-schema'` — true positive.
- With N entries and M errors, up to N x M findings can be produced; the same cross-product applies to the CANONICAL-002 to CANONICAL-005 branches. `Strongly implied by code`
- When validation errors exist, the checker returns only the wrapped errors and does not run `_run_detection_functions()`, so other conflict checks may be skipped in that state. `Needs confirmation` (confirm whether this is intended)
- The checker exits 0 even though the registry validator exits 1 for the same Registry. Whether CANONICAL-006 being `NON_BLOCKING` is intended is `Needs confirmation`.

## Reason for Change
- False positives make the conflict checker output untrustworthy as verification evidence and can mislead governance work (`canon001`, `canon002`) into treating a valid entry as a conflict.

## Implementation Intent
- Map each validation error to the entry it refers to (for example by matching the Decision Target carried in the error, or by validating per entry), and emit one finding per actual violation.
- Preserve existing CANONICAL codes, severities, and messages for true positives.
- Clarify, and either fix or document as intended, whether detection functions should also run when validation errors exist.

## Target Files or Areas
- `tools/check_canonical_source_conflicts.py` (`_wrap_validation_errors`, main entry flow)
- `tests/tools/test_check_canonical_source_conflicts.py`
- `tools/TOOL_DESCRIPTIONS.md` (only if the documented behavior changes)

## Required Changes
- Restrict each wrapped finding to the entry the validation error refers to.
- Add regression tests: a Registry with one exempt single-path entry and one violating multi-path entry must yield exactly one CANONICAL-006 finding, for the violating entry only.
- Add a test covering multiple entries x multiple errors to ensure no cross-product duplication.
- Decide and test the behavior of non-validation detection functions when validation errors exist.

## Constraints
- Do not change `tools/check_canonical_source_registry.py` validation rules or `SINGLE_SOURCE_EXEMPTIONS`.
- Do not edit `config/documentation_canonical_sources.toml` in this issue.
- Follow the `routing.md` "Adding a new tool" validation sequence for modified `tools/*.py`.

## Acceptance Criteria
- Running the checker against the current Registry reports CANONICAL-006 only for `eventbus.persistence-schema`, not for `eventbus.core-behavior`.
- New regression tests fail on the current code and pass after the fix.
- Existing tests in `tests/tools/test_check_canonical_source_conflicts.py` and `tests/tools/test_check_canonical_source_conflicts_routing.py` pass.
- The decision on running other detection functions alongside validation errors is reflected in code and tests.

## Testing Expectations
- `uv run pytest tests/tools/test_check_canonical_source_conflicts.py tests/tools/test_check_canonical_source_conflicts_routing.py`
- `uv run ruff format tools/check_canonical_source_conflicts.py`, `uv run ruff check tools/check_canonical_source_conflicts.py`
- `uv run mypy tools/check_canonical_source_conflicts.py`
- `uv run bandit tools/check_canonical_source_conflicts.py`
- Smoke run: `uv run python tools/check_canonical_source_conflicts.py` against the real Registry.
- `uv run python tools/check_tool_descriptions_sync.py`

## Documentation Impact
Update `tools/TOOL_DESCRIPTIONS.md` only if the checker's documented behavior changes. No `docs/` change expected.

## Out of Scope
- Resolving the `eventbus.persistence-schema` violation itself (issue `canon002`).
- Changing severity or blocking classification of CANONICAL codes unless required by the confirmed intent.
- Refactoring unrelated detection functions.

## Dependencies
- Related to `canon002`: after `canon002` is resolved, the true positive disappears; tests must use fixtures, not the live Registry, to keep the regression covered.
- Supports `canon001` verification.

## Unresolved Questions
- Should other detection functions (CANONICAL-001, W-xx) run when registry validation errors exist?
- Is a non-zero exit status expected when CANONICAL-006 is present?

## AI Implementation Instruction
- Write the failing regression test first, then fix `_wrap_validation_errors`.
- Keep the change limited to the error-to-entry mapping and the confirmed behavior; do not restructure the module.
- Stop and report if the intended behavior for the Unresolved Questions cannot be determined from existing tests, docstrings, or `docs/00_governance/governance_04_documentation-checks.md`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261001-103526
- **Related target files**: tools/check_canonical_source_conflicts.py, tests/tools/test_check_canonical_source_conflicts.py, tools/TOOL_DESCRIPTIONS.md
