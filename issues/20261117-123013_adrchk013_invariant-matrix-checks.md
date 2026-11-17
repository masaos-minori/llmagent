# Make the Invariant matrix consistent and checked in both directions

## Priority
Medium

## Summary
The Index Invariant matrix and the ADR bodies disagree, and `tools/check_adr_invariant_matrix.py` checks only one direction. Fix the data and the checker together.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-M01`; merged from ADRCHK-M04, M06 (review findings M3, M4, N17, N26)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Claims come from the review (`Documentation only` until re-verified).

## Reason for Change
- Status and Blocking values break the Index rule: the Index says Not verified rows are Non-Blocking, yet some ADR-002 and ADR-003 rows are Not verified and Blocking; ADR-003 INV-03 is Confirmed in the Index but Not verified in the ADR; the Index claims test coverage for an ADR-012 invariant with no row in the ADR body; ADR-014 INV-02 is Confirmed but Non-Blocking; ADR-016 and ADR-017 are missing from the matrix although ADR-017 INV-01 blocks startup.
- The checker misses whole tables: it skips any Automated Tests table without an Implementation column, so ADR-004 escapes its rules.
- The checker works in one direction only: evidence that exists only in the Index is never caught.
- The checker rules differ from governance: its `Exception: <id>` grammar differs from governance_03, the Cadence check is a warning with no end date, and its docstring cites a nonexistent follow-up.

## Implementation Intent
- The ADR body is the source of truth, and the Index mirrors it exactly.
- The checker compares both directions, treats a missing column as an error, and uses the governance grammar.
- Blocking values follow the Index rule, unless an approved exception says otherwise.

## Target Files or Areas
- `tools/check_adr_invariant_matrix.py`
- `docs/10_adr/adr_01_index.md`
- docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md (add the Implementation column)
- ADR-002, ADR-003, ADR-012, ADR-014, ADR-016, and ADR-017 under `docs/10_adr/`
- `tests/tools/`

## Required Changes
- Add fixtures that fail today: Index-only evidence, and a table without an Implementation column.
- Implement the reverse direction, the missing-column error, and the governance exception grammar; make the Cadence check an error or record its end date in governance; fix the docstring.
- Add the Implementation column to ADR-004.
- Correct the Index rows from the ADR bodies, and add the ADR-016 and ADR-017 rows.
- Propose Blocking value changes as pending amendments.

## Constraints
- A Blocking value change is a decision change; do not apply it without an approval record.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- `uv run python tools/check_adr_invariant_matrix.py` passes on the repository and fails on each fixture.
- No row is both Not verified and Blocking without an approved exception.

## Testing Expectations
Fixture tests under `tests/tools/` (failing first); ruff, mypy, bandit on the changed tool; ADR checkers. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. Index matrix and the ADR Automated Tests tables.

## Out of Scope
- Changing invariant substance or decisions.

## Dependencies
- `issues/20261117-123011_adrchk011_adr-approval-governance.md` defines the pending form for Blocking changes (depends on).

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
- A Blocking value change is a decision change. Do not apply it without an approval record.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123013
- **Related target files**: `tools/check_adr_invariant_matrix.py`; `docs/10_adr/adr_01_index.md`; `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md (add the Implementation column)`; ADR-002, ADR-003, ADR-012, ADR-014, ADR-016, and ADR-017 under `docs/10_adr/`; `tests/tools/`
