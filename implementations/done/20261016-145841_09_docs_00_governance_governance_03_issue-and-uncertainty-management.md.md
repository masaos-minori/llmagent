## Goal
- Remove the resolved Known Issue `AGENT-013` from the Active Items of the ledger.

## Scope
- The `#### AGENT-013` entry in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (from its heading to the line before the next entry).

## Assumptions
- `AGENT-013` is the only `AGENT-*` entry; the ordering convention text names the group and stays valid with an empty group.
- `check_docs_consistency` rejects a Known Issue ID cited under `docs/` that has no ledger entry, so no other document may still cite it (the `GV-023` row is handled in the next document).
- The entry's Resolution Target is met once the registry, handlers, and chapter agree and the exemption is gone (other rows).

## Design decisions
- Delete the whole entry; do not leave a resolved-item note (the ledger forbids resolved-item bullets elsewhere).

## Alternatives considered
Marking the entry resolved: rejected, because resolved entries are removed from the Active Items (`GV-022` rejects resolved-item bullets).

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
- Remove the `#### AGENT-013` heading and all its field lines, keeping a single blank line between the neighbouring entries.

### Method
- Verify with `rg AGENT-013 docs` that the only remaining mention is the `GV-023` row (removed by the next document).

### Details
- Do this edit last in the Plan, after the exemption removal and the contract check pass, because the ledger entry documents an open problem.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py` (all domains), `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_needs_confirmation_inventory.py`
- `rg AGENT-013 docs scripts tools tests`

## Completion criteria
- No `AGENT-013` entry remains and no document cites it; the checkers report no new finding.

## Out of scope
- Other Known Issue entries and the Needs Confirmation inventory.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the AGENT-013 entry | Completed | — | 20261016-200847 | Removed from ledger; GV-023 exemption cleared by the governance_04 doc first |
| 2 | Run the docs checkers and search for remaining citations | Completed | — | 20261016-200847 | `rg AGENT-013 docs` empty; `check_docs_consistency.py --domain {overview,agent}` report no issues |

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
- **Requirement ID**: REQ-007 (close AGENT-013)
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-143248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-145841
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
