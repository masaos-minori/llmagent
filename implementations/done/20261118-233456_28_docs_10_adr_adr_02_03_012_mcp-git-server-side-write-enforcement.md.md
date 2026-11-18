## Goal

Keep ADR-012's Decision and INV-04 wording aligned with the verified Agent-approval / server-enforcement
split and with the reworded `RepositoryGateway` docstrings, without shortening the invariant text
(REQ-004, REQ-009).

## Scope
**Release unit**: boundary-and-adr-record

## Assumptions
- `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md:43` already records client-side
  approval with an approval-independent git endpoint; INV-04 at `:133` states the two checks are
  independent. Both are already correct.
- Authority entry: `config/adr_authority.toml:48-52` (`agent.tool-approval`, primary ADR-003,
  supplemental ADR-012).

## Design decisions
- Additive clarification only: name the Agent-side components that enforce approval
  (`scripts/agent/tool_policy.py`, `scripts/agent/tool_approval.py`, `scripts/agent/repository_gateway.py`)
  and state that the git server's checks run regardless of approval state.
- No invariant is added, merged, or shortened: `check_adr_preservation.py` treats a shortened invariant
  as a violation.

## Alternatives considered
N/A: DT-05 Option A confirms the existing split; the document change is wording alignment.

## Implementation
### Target file
`docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`
### Procedure
1. Extend the Decision context near `:43` with the Agent-side module names and the docstring wording used
   in row 07.
2. Confirm INV-04 (`:133`) still reads as two independent checks; adjust only if the row 07 wording
   introduced a term this ADR must reuse.
### Method
Two localized edits; invariant statements are not shortened.
### Details
- The matrix row for ADR-012 (`docs/10_adr/adr_01_index.md:205`) already cites `tests/mcp_servers/git/`
  for INV-01-INV-04; this document does not change verification evidence.

## Compatibility considerations
Row 31 re-renders the graph sections of the index from `config/adr_authority.toml`; no authority entry
change is needed here.

## Security considerations
Preserves the guarantee that server-side git enforcement does not depend on Agent approval state.

## Rollback considerations
Revert the whole unit commit (see row 27).

## Validation plan
- `uv run python tools/check_adr_preservation.py`, `uv run python tools/check_adr_structure.py`,
  `uv run python tools/check_adr_invariant_matrix.py`.

## Completion criteria
ADR-012, the `RepositoryGateway` docstrings, and the approval-flow document describe the same split
(AC-009), with no invariant shortened.

## Out of Scope
`RepositoryGateway` docstrings (row 07), ADR-014 (row 27), the index matrix (row 31).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Align the Decision and INV-04 wording per Procedure | Completed | 20261119-080756 | 20261119-080756 | Additive edit to the Constraints bullet near `:43`: names `agent/repository_gateway.py` alongside `tool_policy.py`/`tool_approval.py` and reuses the row 07 docstring wording ("guards the Agent-side write path only... ADR-014 INV-03"). INV-04 (`:133`) verified unchanged: still states the two checks are independent — no new term to reuse |
| 3 | Run the ADR checkers (`routing.md` Tools) | Completed | 20261119-080756 | 20261119-080756 | check_adr_preservation / check_adr_structure / check_adr_invariant_matrix pass; no invariant shortened |

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
- **Requirement ID**: `REQ-004` (DT-05 decision), `REQ-009` (boundary record)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`
