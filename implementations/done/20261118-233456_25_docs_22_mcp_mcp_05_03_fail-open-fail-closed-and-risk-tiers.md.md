## Goal

Extend the tier-to-approval mapping table so it states which tier entries are plan-mode-only and which
tools never reach escalation, publishing the Phase 1 reachability report (REQ-001, REQ-002, REQ-010).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Existing table: `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md:73-74` already says the
  tier supplies the default and rules override it.
- Measured posture: 19 ruled tools all have tier entries; tier-`NONE` rule-less tools (`index_paths`,
  `refresh_index`, `git_add`, `git_commit`, every `READ_ONLY` tool) return `NONE` before escalation.

## Design decisions
- Publish the reachability table here as the tier-side canonical source, with the approval-flow document
  (row 21) as the flow-side canonical source; the two must not restate each other.

## Alternatives considered
N/A: documentation-only; the table's shape is fixed by the existing document.

## Implementation
### Target file
`docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
### Procedure
1. Extend the `:73-74` mapping with a column or following table marking, per tier value, whether it
   affects approval risk, plan-mode blocking, or both.
2. Add a short list of tools that never reach escalation because of the `NONE` short-circuit.
### Method
Table extension plus one list; no restructuring of the document.
### Details
- Numbers must match the shipped config (19 rules / 64 tiers) and the row 11/12/15 characterization tests.

## Compatibility considerations
Consistency is enforced against the row 21 canonical flow document by `check_docs_consistency.py`.

## Security considerations
N/A: documentation of existing behavior.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_consistency.py --domain agent`.

## Completion criteria
A reachability table exists for every tool in `approval_risk_rules` and every tier value, consistent with
the canonical flow document (AC-001, AC-002).

## Out of Scope
The approval-flow narrative (row 21), config comments (row 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the mapping table and add the never-escalates list | Completed | 20261119-080405 | 20261119-080405 | Table gained a "Plan-mode blocking" column (only `READ_ONLY` allowed); reachability paragraph states 19 rules / 64 tiers, 43 tier-`none` unruled tools (39 READ_ONLY + `git_add`/`git_commit`/`index_paths`/`refresh_index`) never reach escalation — all counts measured against the shipped fixture mirrors; links to agent_06_02 as the flow-side canonical source without restating it |
| 3 | Run the documentation checkers (`routing.md` Tools) | Completed | 20261119-080405 | 20261119-080405 | check_docs_quality and check_docs_consistency --domain agent pass |

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
- **Requirement ID**: `REQ-001` (reachability record), `REQ-002` (evaluation order), `REQ-010` (canonical source)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
