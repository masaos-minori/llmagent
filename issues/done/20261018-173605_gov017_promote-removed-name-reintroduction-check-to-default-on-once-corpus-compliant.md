# Promote removed-name reintroduction check to default-on once corpus is compliant

## Priority
Low

## Summary
Governance rule GV-017 ("Removed-name reintroduction in current specifications") is enforced by `check_compat_shims.py --check-removed-names`, currently opt-in. Four slash-command removed-name patterns (`/diff`, `/system`, `/audit`, `/workflow`) are implemented. Promote `--check-removed-names` to default-on (run in CI / by default) once the corpus is confirmed compliant, per the tool's own "report-only until compliant" convention, and mark GV-017 `Existing`.

## Background
`governance_04_documentation-checks.md` maps GV-017 to `check_compat_shims.py --check-removed-names`, gate `Warning`, status `Partial`, follow-up: "Four slash-command removed-name patterns are implemented (`/diff`, `/system`, `/audit`, `/workflow`); promote `--check-removed-names` from opt-in to default-on once the corpus is compliant, per `check_compat_shims.py`'s own 'report-only until compliant' convention." The retired identifier patterns and historical-context markers live in `tools/check_compat_shims.py` (`_REMOVED_NAME_PATTERNS`, `_HISTORICAL_CONTEXT_MARKERS`).

## Problem
While `--check-removed-names` is opt-in, reintroduction of a retired removed-name pattern (e.g. using a retired slash-command name in a current specification) goes undetected unless someone explicitly runs the flag. This lets removed names reappear silently in the corpus.

## Reason for Change
Once the corpus is verified compliant, promoting the check to default-on enforces GV-017 continuously at the PR/CI gate. The tool's "report-only until compliant" design means promoting it does not risk failing CI while any residual non-compliance exists.

## Implementation Intent
First run `check_compat_shims.py --check-removed-names` across the corpus to confirm zero reintroductions. Then wire the check into CI or the pre-commit hook so it runs by default, preserving the report-only-until-compliant guard (it must not hard-fail CI while non-compliance may remain). Use `_REMOVED_NAME_PATTERNS` / `_HISTORICAL_CONTEXT_MARKERS` as the detection basis.

## Target Files or Areas
CI workflow or pre-commit configuration; `tools/check_compat_shims.py` (read-only as the detector); `docs/00_governance/governance_04_documentation-checks.md` (GV-017 row).

## Required Changes
- Run `--check-removed-names` across the corpus and confirm compliance.
- Wire the check into CI / pre-commit default invocation.
- Preserve the report-only-until-compliant behavior (no hard CI failure while non-compliance may exist).
- Update the GV-017 matrix row to `Existing` and clear its Follow-up note.

## Constraints
- Must NOT promote to a failing CI gate while any removed-name reintroduction may remain.
- Keep the check `Warning`-level and non-blocking.

## Acceptance Criteria
- The corpus is confirmed free of removed-name reintroductions.
- The check runs by default in CI / pre-commit.
- Residual non-compliance reports without failing the build.
- GV-017 matrix row is marked `Existing`.

## Testing Expectations
Run `--check-removed-names` across the full corpus to confirm zero findings before promoting; verify the default invocation executes in CI.

## Documentation Impact
`governance_04_documentation-checks.md`: GV-017 row status `Partial` → `Existing`, Follow-up column cleared.

## Out of Scope
Changing the removed-name patterns (`_REMOVED_NAME_PATTERNS`, `_HISTORICAL_CONTEXT_MARKERS`). Handling other `check_compat_shims.py` options.

## Dependencies
`tools/check_compat_shims.py` detection patterns.

## Unresolved Questions
Which CI / pre-commit hook should run the check, and how exactly to preserve the report-only guard in the gate? Define before implementing.

## AI Implementation Instruction
Confirm corpus compliance with `--check-removed-names` before making any change. Wire the check into CI/pre-commit as a non-blocking, report-only step; do not make it a hard failure. Do not modify the detection patterns.

## Traceability
- Workflow phase: issue-creator
- Source issue: N/A: this document is the issue
- Source requirement: N/A: no standalone requirement document is generated
- Source plan: N/A: not filed from a Plan
- Source implementation procedure: N/A: not filed from an implementation procedure
- Generated at: 2026-10-18
- Related target files: CI / pre-commit config, `tools/check_compat_shims.py`
