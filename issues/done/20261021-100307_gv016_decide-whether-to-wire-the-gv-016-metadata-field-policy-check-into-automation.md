# Decide whether to wire the GV-016 metadata field policy check into automation

## Priority
Low

## Summary
Decide whether `tools/check_metadata_field_policy.py` (GV-016) should run automatically in CI, pre-commit, or the `routing.md` "When to run which tool" table, and apply the decision.

## Background
`governance_04_documentation-checks.md` lists GV-016 ("No unnecessary Metadata or Status fields added") as an Auto rule with Timing `Periodic`, Gate `Warning`, and Follow-up "Not run by CI or pre-commit". A search of `.github`, `.pre-commit-config.yaml`, and `tox.ini` finds no reference to the tool. The tool is documented in `tools/TOOL_DESCRIPTIONS.md`. Its default run is report-only (exit 0 on warnings); `--strict` exits 1 on any warning.

## Problem
No automated trigger runs the check, and `routing.md` "When to run which tool" has no row for it. The rule is therefore effectively unenforced, and an agent following `routing.md` is never told to run it. Whether this is deliberate is unknown.

## Reason for Change
An Auto rule that nothing triggers drifts silently. Either the gap should be closed or the rule's intended timing (`Periodic`, by hand) should be stated so the matrix is accurate.

## Implementation Intent
Decide first, then apply the smallest matching change:

- Add a `routing.md` row only: documents when an agent runs it.
- Add a pre-commit hook and/or CI step: blocks or warns automatically.
- Keep it manual: record it as intentionally periodic and unwired.

Before choosing automation, measure the current finding count with live data so a new gate does not fail on existing content.

## Target Files or Areas
- `routing.md` ("When to run which tool")
- `.pre-commit-config.yaml`, `.github/workflows/ci.yml` (only if automation is chosen)
- `docs/00_governance/governance_04_documentation-checks.md` (GV-016 row)
- `tools/TOOL_DESCRIPTIONS.md` (only if the documented trigger changes)

## Required Changes
- Run `uv run python tools/check_metadata_field_policy.py` and `--strict` on the live repository and record the finding count.
- Record the owner's decision on the trigger.
- Apply the matching wiring or documentation change.
- Update the GV-016 matrix row (Timing, Gate, Follow-up) to match the result.

## Constraints
- A new blocking gate must not fail on the existing corpus; resolve or baseline findings first, in a separate change if needed.
- Gate and blocking status are governed by `governance_04`; do not change another rule's gate.
- `routing.md` edits require `uv run python tools/check_skills_references.py`.

## Acceptance Criteria
- The GV-016 trigger (automatic or manual) is stated consistently in `governance_04`, `routing.md`, and `tools/TOOL_DESCRIPTIONS.md`.
- If automated, the trigger runs and passes on the current corpus.
- "Not run by CI or pre-commit" no longer appears in the matrix unless it is the intended state, stated as a design choice.

## Testing Expectations
- `uv run python tools/check_metadata_field_policy.py --strict` on the live repository.
- If a hook or CI step is added: `uv run pre-commit run --all-files` and CI workflow validation.
- `uv run python tools/check_tool_descriptions_sync.py`, `check_skills_references.py`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.
- Existing `tests/tools/test_check_metadata_field_policy.py` continues to pass.

## Documentation Impact
Yes. GV-016 row in `governance_04`; `routing.md` "When to run which tool"; possibly `tools/TOOL_DESCRIPTIONS.md`.

## Out of Scope
- Changing the checker's logic or permitted field sets.
- Wiring other tools.
- Remediating findings beyond what is required to keep a new gate green.

## Dependencies
N/A: none (sibling-issue check: no open issue touches these files). Another issue in the same batch edits `governance_04` (follow-up decisions, compression policy); coordinate edit order.

## Unresolved Questions
- Should GV-016 run automatically, or stay manual and periodic by design?
- If automated, at which trigger (pre-commit, CI, or both) and at which gate (warning or blocking)?

## AI Implementation Instruction
Do not choose the trigger without an owner decision; measure findings first and report. Keep changes limited to the listed files. Do not modify the checker.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-100307
- **Related target files**: `routing.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `docs/00_governance/governance_04_documentation-checks.md`, `tools/TOOL_DESCRIPTIONS.md`
