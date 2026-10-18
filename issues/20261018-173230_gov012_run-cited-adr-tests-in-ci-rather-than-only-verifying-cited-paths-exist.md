# Run cited ADR invariant tests in CI, not only verify cited paths exist

## Priority
Low

## Summary
Governance rule GV-012 ("Code is NOT canonical for adopted design decisions") is enforced by `check_compat_shims.py`, `check_adr_invariant_matrix.py`, and `check_adr_reference.py`. The ADR Invariant Verification Matrix cites a test per invariant, and `check_adr_invariant_matrix.py` verifies each cited test path exists. Extend CI to actually run the cited tests, not merely confirm their paths exist. This is the optional scope the matrix lists for GV-012.

## Background
`governance_04_documentation-checks.md` maps GV-012 to the three checkers, gate `Warning`, status `Existing`, with the optional follow-up: "run cited tests in CI, not just verify path existence." Currently the matrix check confirms a cited test path exists but never executes it.

## Problem
A cited test path can exist yet pass trivially or assert nothing about the invariant. "Path exists" verification therefore does not prove the invariant is enforced; only running the cited test in CI catches a passing-but-meaningless citation.

## Reason for Change
Strengthening GV-012 from structural (path exists) to behavioral (test passes) closes the optional gap without changing what is documented as canonical.

## Implementation Intent
Add a CI step (or extend the existing `lint` job) that reads the test node ids/paths cited in the ADR Invariant Verification Matrix and runs them, failing if any cited test is missing, skipped, or failing. Use the matrix as the citation source; do not change the matrix schema or the existing path-existence check.

## Target Files or Areas
CI workflow for the `lint` job; `tools/check_adr_invariant_matrix.py` (read-only citation source); `docs/00_governance/governance_04_documentation-checks.md` (GV-012 follow-up note).

## Required Changes
- Extract cited test node ids/paths from the ADR Invariant Verification Matrix.
- Run them in CI and fail on missing, skipped, or failing citations.
- Clear the GV-012 optional follow-up note.

## Constraints
- Cited tests must be runnable in CI; define a skip-annotation convention for integration-only tests rather than silently ignoring them.
- Preserve the existing path-existence verification.

## Acceptance Criteria
- Cited tests execute in CI.
- A missing, skipped, or failing citation fails the build.
- Existing cited tests pass without false failures.
- Path-existence checking still runs.

## Testing Expectations
Confirm the CI step runs on a sample set of citations and that a deliberately broken citation fails the build.

## Documentation Impact
`governance_04_documentation-checks.md`: clear the GV-012 optional follow-up note (status remains `Existing`).

## Out of Scope
Changing the ADR Invariant Verification Matrix schema. Extending to non-matrix-cited tests.

## Dependencies
None blocking.

## Unresolved Questions
How to cite integration-only tests that cannot run in the base CI environment? Define a skip-annotation convention before implementing.

## AI Implementation Instruction
Treat the ADR Invariant Verification Matrix as the sole citation source. Add a CI runner that executes cited tests and fails on missing/skipped/failing. Preserve the path-existence check and define a skip convention for integration-only tests.

## Traceability
- Workflow phase: issue-creator
- Source issue: N/A: this document is the issue
- Source requirement: N/A: no standalone requirement document is generated
- Source plan: N/A: not filed from a Plan
- Source implementation procedure: N/A: not filed from an implementation procedure
- Generated at: 2026-10-18
- Related target files: CI `lint` workflow, `tools/check_adr_invariant_matrix.py`
