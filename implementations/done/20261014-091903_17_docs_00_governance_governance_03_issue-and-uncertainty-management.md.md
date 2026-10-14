## Goal

Remove Known Issue AGENT-009 from the ledger (REQ-004: update documentation).

## Scope

- Delete one table row and one detail entry. AGENT-009 row (line 98) and `#### AGENT-009` entry (143-160) only.

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Run `git fetch` and rebase first: this file had 89 commits in 30 days (Plan Risks).
- Ledger convention: a resolved item is removed, not kept closed (governance_03 line 59); do not add a replacement note.

## Alternatives considered

N/A: the docs follow the code removal

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

Delete the table row and the whole `#### AGENT-009` section through the blank line before the next heading.

### Method

Edit with the Edit tool; afterward `rg -n 'AGENT-009' docs scripts tests tools` must be empty. Do not hard-code any item count.

### Details

Run `check_known_deviation_sync.py` and `check_issue_inventory_conformance.py`.

## Compatibility considerations

Docs-only change.

## Security considerations

N/A: docs-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run python tools/check_known_deviation_sync.py`, `check_issue_inventory_conformance.py`, `check_docs_quality.py`, `check_docs_structure.py` pass.

## Completion criteria

- AGENT-009 appears nowhere in the ledger or other docs.

## Out of scope

- Other ledger entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fetch and rebase, then delete the row and entry | Completed | 20261014-094631 | 20261014-094631 |  |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261014-094631 | 20261014-094631 |  |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261014-090429_skill001_remove-the-skill-slash-command-and-its-ephemeral-plumbing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-091322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-091903
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md