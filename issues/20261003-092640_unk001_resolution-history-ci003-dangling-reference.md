# Resolution History: CI-003 Dangling Reference in ADR-003

## Priority
Low

## Summary
Record the discovery, judgment, execution, and verification process for resolving
UNK-01 (`CI-003` dangling reference in `ADR-003`). This issue serves as an audit trail
documenting how the known deviation was identified, evaluated, and closed.

## Background
During the `issue-to-plan` workflow for `plans/20261002-182813_plan.md`, an unresolved
unknown (`UNK-01`) was discovered: `ADR-003` line 472 referenced Known Issue `CI-003`
which had no matching heading in `governance_03_issue-and-uncertainty-management.md`.
The `tools/check_known_deviation_sync.py` tool flagged this as a dangling reference.

## Problem
The status of `CI-003` (resolved vs. still open) could not be confirmed from available
evidence:
- `governance_03` had no `#### CI-003` heading
- `ADR-003` prose suggested it might be open but was unverified
- Git history showed the ID across renames/reorgs without establishing current status
- No confirmation whether Reload execution flow now has automated test coverage

## Reason for Change
To maintain traceability of decisions made during the `kdref001` acceptance criterion
workstream. Without this record, future reviewers cannot understand why `CI-003` was
removed from `ADR-003` rather than restored to `governance_03`.

## Implementation Intent
Document the resolution decision and verification evidence. No code changes are required;
this is a record-keeping issue only.

## Target Files or Areas
- `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md` (already modified)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (not modified)

## Required Changes
- [x] Remove `CI-003 (...)` clause from `ADR-003` line 472 (`REQ-003`)
- [x] Delete pointer bullet that became empty after removal
- [x] Preserve `### Known Issues` header in `ADR-003`
- [x] Verify `check_known_deviation_sync.py` reports no dangling warning for `CI-003`
- [x] Run related validation tools (`check_adr_structure.py`, etc.)

## Constraints
N/A: covered by Summary

## Acceptance Criteria
- [x] `uv run python tools/check_known_deviation_sync.py` reports no dangling warning for `CI-003`
- [x] `uv run pytest tests/tools/test_check_known_deviation_sync.py` passes (7/7)
- [x] `check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_docs_japanese.py` report no issues
- [x] `ADR-003` line 472 no longer contains `CI-003` reference
- [x] `governance_03` does not contain a new `#### CI-003` heading

## Testing Expectations
Not required — this is a documentation-only record; all testing was performed during the
original resolution work and is recorded in the Acceptance Criteria above.

## Documentation Impact
This issue itself is the documentation artifact. No additional documentation updates are
required beyond this record.

## Out of Scope
- Restoring `CI-003` to `governance_03` (explicitly decided against per user direction)
- Modifying other Known Issue references (`CI-015`, `SHARED-003`, `CI-002` were handled separately)

## Dependencies
- **Source plan**: `plans/20261002-182813_plan.md` (contains `UNK-01` definition)
- **Source issue**: `issues/20261001-125540_kdref001_resolve-dangling-known-issue-references-exposed-by-adr-translation.md`

## Unresolved Questions
N/A: none — all questions were resolved during the original investigation

## AI Implementation Instruction
N/A: This issue records completed work. No implementation tasks remain.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: `issues/20261001-125540_kdref001_resolve-dangling-known-issue-references-exposed-by-adr-translation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261002-182813_plan.md`
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-092640
- **Related target files**: `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`

---

## Resolution Details (Audit Trail)

### Decision (2026-10-02)
`UNK-01` closed as "`CI-003` is resolved". Per user direction, the `CI-003` clause was
removed from `ADR-003` rather than restoring a canonical `#### CI-003` entry to
`governance_03`.

### Action Taken (`REQ-003`)
Removed the `CI-003 (...)` clause from `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`
line 472. With `CI-015` (`REQ-001`) already removed on the same bullet, the pointer bullet
became empty and was deleted while keeping the `### Known Issues` header. No `#### CI-003`
heading was added to `governance_03`.

### Verification Evidence
| Check | Result |
|-------|--------|
| `check_known_deviation_sync.py` | No dangling warning for `CI-003` (nor `CI-015`, `SHARED-003`, `CI-002`) |
| `pytest tests/tools/test_check_known_deviation_sync.py` | Passes (7/7) |
| `check_adr_structure.py` | No issues |
| `check_adr_invariant_matrix.py` | No issues |
| `check_adr_reference.py` | No issues |
| `check_docs_japanese.py` | No issues |

### Result
`UNK-01` resolved; `kdref001` acceptance criterion satisfied.
