## Goal
Register the `github` MCP criticality disagreement as an active Configuration Drift entry in Part 4 and cross-reference it from NC-041, so Part 2 and Part 4 describe the same state (REQ-001: register the entry; REQ-002: cross-reference NC-041 and rely on Part 4's removal rule; REQ-003: back-reference in NC-041).

## Scope
- Replace the line "No active Configuration Drift items remain." under Part 4 "Active Items" with one entry.
- Append a cross-reference to NC-041's Resolution Target; no other NC-041 field changes.

## Assumptions
- NC-041's Evidence records the 2026-10-21 owner decision to restore `required = true`, with the restore deferred until `MCP_GITHUB_AUTH_TOKEN` is provisioned; the approved value is therefore settled and the deployed value differs, which is the Part 4 definition (verified in the file).
- Part 4's removal rule already states how long an entry remains, so the entry does not restate it beyond a pointer.
- The conformance parser attributes any `####` heading to the last Part 1/2 section seen and would demand fifteen fields, so the entry must not use a `####` heading (verified in `check_issue_inventory_conformance.py`); Part 4 status is read from a `- **Status**: <value>` bullet.
- Docs content policy: name configuration keys but not literal values; evidence stays in NC-041.

## Design decisions
- Entry as a bullet block (no heading) with six fields in template order: ID `DRIFT-001`; Decision target (component criticality and startup availability of the `github` MCP server); Deployed value description (the server is configured as not required and with startup disabled in `config/agent.toml`); Approved operational value description (`github` is required per the classification table in `agent_08_04_configuration-mcp-approval-obs.md` and ADR-004 Decision Group 3 item 13; evidence and the pending restore are in NC-041); Severity `Medium`; Status `open`.
- NC-041 Resolution Target gains "; tracked as DRIFT-001 in Part 4".

## Alternatives considered
- NC-041 as the sole record: rejected, the owner decision removed the premise of an undecided disagreement.
- A `#### DRIFT-001` heading: rejected, it would fail the field-count conformance check.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Under Part 4 "Active Items" replace "No active Configuration Drift items remain." with the bullet block described above.
2. In NC-041 append the `DRIFT-001` cross-reference to the end of the Resolution Target value.

### Method
- Minimal in-place edits; re-read the file before editing (the `Blocking`-definition procedure edits Part 2 of the same file; apply sequentially).
- Keep NC-041's other fields byte-identical.

### Details
- Do not print or store any token value; do not restate NC-041's Evidence text.
- The Part 4 template text, status values, and removal rule stay unchanged.

## Compatibility considerations
N/A: documentation only. The inventory checkers must keep passing; no parser change is made here.

## Security considerations
N/A: documentation only; no secrets are written.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_issue_inventory_conformance.py`, `check_needs_confirmation_inventory.py`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain agent`.
- Read back Part 2 and Part 4 once to confirm they describe the same state.

## Completion criteria
- Part 4 contains one active entry with all six template fields and Status `open`, and no longer says no items remain.
- NC-041's Resolution Target names `DRIFT-001`; no other NC-041 field changed.
- All listed checkers pass.

## Out of Scope
- Deciding the `github` outcome, editing `config/agent.toml` or the classification table, and adding an Owner or Blocking field to the Part 4 template.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Register `DRIFT-001` in Part 4 and add the NC-041 cross-reference | Completed | 20261022-115452 | 20261022-115452 | Changed: docs/00_governance/governance_03_issue-and-uncertainty-management.md |
| 2 | Run the inventory and documentation checkers and read back for consistency | Completed | 20261022-115452 | 20261022-115452 | validated; full suite 9689 passed, 14 skipped; ruff, mypy, bandit on edited tools pass; docs checkers pass; check_issue_inventory_conformance and check_needs_confirmation_inventory pass |

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
- **Requirement ID**: `REQ-001` (register the Drift entry), `REQ-002` (cross-reference NC-041), `REQ-003` (NC-041 back-reference)
- **Source issue**: `issues/20261021-104507_gitdrift_register-the-github-mcp-criticality-disagreement-in-the-configuration-drift-inventory.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094640_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101759
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md