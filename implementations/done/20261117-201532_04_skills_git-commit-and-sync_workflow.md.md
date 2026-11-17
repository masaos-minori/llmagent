## Goal

Update the Phase 4 note of `skills/git-commit-and-sync/workflow.md` so it states the new
default: runtime-argument rows are hidden with a count line, `--verbose` shows them, and the
other `Not available` rows stay visible.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file procedure for row 4 of the plan's frozen `Implementation Target Files` table:
`skills/git-commit-and-sync/workflow.md` (REQ-006 Phase 4 note update, AC-6).

## Assumptions
- The note today reads "Only `Fail` and `Blocked` rows matter; `Not available` rows (a gate
  whose command needs a runtime argument) are not failures." (verified against source).
- The behavior described comes from the seq 01/02 code; land this note after or with them.

## Design decisions
- Rewrite that one sentence in place; the rest of Phase 4 (unrelated-failure tests, stop
  conditions) is unchanged.

## Alternatives considered
N/A: documentation-only single-sentence update.

## Implementation
### Target file
`skills/git-commit-and-sync/workflow.md`
### Procedure
Replace the "Only `Fail` and `Blocked` rows matter" sentence with: gates whose command needs
a runtime argument are omitted from the default summary and counted in one line (add
`--verbose` to show them); `Not available` rows for a missing local tool stay visible;
neither kind is a failure, only `Fail` and `Blocked` remain stop conditions.
### Method
Keep the sentence's position in Phase 4; no new headings or bullets.
### Details
N/A: no further prose changes in the file.

## Compatibility considerations
N/A: documentation-only; the skill's stop-condition logic is unchanged.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` — no finding.
- `uv run python tools/check_skills_heading_cycles.py` — no finding.

## Completion criteria
The Phase 4 note states the hide-by-default behavior, the count line, and the `--verbose`
flag, and both skills checkers pass (AC-6).

## Out of Scope
Every other phase of the workflow; the tool description rows (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261117-231500 |  |
| 2 | Run the documentation checkers named in Validation plan | Completed | — | 20261117-231500 | `check_skills_references.py`, `check_skills_heading_cycles.py` check_skills_references.py and check_skills_heading_cycles.py: no findings |

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
- **Requirement ID**: `REQ-006` (commit-workflow note update)
- **Source issue**: issues/20261117-123335_wftool006_gate-output-noise.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125737_wftool006_gate-output-noise.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-201532
- **Related target files**: `skills/git-commit-and-sync/workflow.md`