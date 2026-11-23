## Goal

Rewrite Known Issues MCP-003 to its remaining open question and correct the premise of MCP-004, keeping both open.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the MCP-003 and MCP-004 entries only (about lines 154-190). IDs, Status, Owner, Area, Type, Severity, and Related stay; no entry is removed and no ledger entry changes.

## Assumptions

- Verified: MCP-003 says a per-server item-10 assessment was never performed, but ADR-004 Group 7 records the owner instruction that every registry component is `required`, and item 10's criteria decide only a non-mandatory classification (item 12 forbids assuming it).
- Verified: MCP-004 says the matrix owner list for `mcp.component-mandatoriness` awaits approval, but the governance_01 `### Resolution Matrix` is by claim type with no owner column and no per-target rows; the real mismatch is that `config/documentation_canonical_sources.toml` registers the registry under claim type `security-policy` while the matrix row names only Accepted security ADRs. `check_canonical_source_registry.py` passes.
- The registry file's header comment (procedure 01) keeps citing both IDs, so the IDs stay.

## Design decisions

- MCP-003: title and summary become the open question whether `failure_category` should stay uniform `safety-integrity` or follow ADR-004 Group 2 item 7 (whose own classification awaits approval as AAL-019); observed implementation states the owner instruction and the unchanged values; recommended action: the maintainer states the answer, recorded pending, no approval written; Source updated (rationale lines now cite Group 7).
- MCP-004: source and observed implementation corrected to the claim-type mismatch above; recommended action: the maintainer chooses between naming the registry in the governance_01 `security-policy` row or changing the claim type in the canonical-source registry (first option is the earlier recommendation); no approval written.

## Alternatives considered

Rejected: removing both entries (the `failure_category` and authority questions are still open); rejected: leaving them unchanged (their premises are contradicted by the files).

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Edit the fields named above in both entries, keeping the entry template (field count and order) so `check_issue_inventory_conformance.py` passes.
2. Do not edit any other entry, the Approval Ledger, or Part tables.

### Method
Edit prose of the two entries only; keep references to existing IDs (AAL-019, MCP-003, MCP-004) resolvable.

### Details
- Re-run the inventory conformance and known-deviation checkers after the edit.

## Compatibility considerations

N/A: documentation only.

## Security considerations

N/A: no approver, date, or approval sentence is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_issue_inventory_conformance.py`
- `uv run python tools/check_known_deviation_sync.py`
- `uv run python tools/run_validation_gates.py`

## Completion criteria

- MCP-003 states the `failure_category` question and the owner instruction; MCP-004 states the verified claim-type mismatch; both are open; the checkers pass.

## Out of Scope

Other inventory entries, ADR text, governance_01, and the canonical-source registry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-134241 | 20261123-134634 | Changed: governance_03 MCP-003 and MCP-004 entries; 2:conformance, known-deviation sync, canonical-source registry checkers and validation gates pass |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-134634 | 20261123-134634 | — |

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
- **Requirement ID**: `REQ-002` (failure_category unchanged, question recorded), `REQ-003` (MCP-004 states the verified mismatch), `REQ-005` (inventory entries updated)
- **Source issue**: issues/20261123-104602_gov003_mandatoriness-assessment-registry.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-111105_gov003_mandatoriness-assessment-registry.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-133747
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
