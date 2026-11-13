## Goal

Update ADR-013's decision text to describe the single authorization format, the single bind/token rule, and the new audit record shape (REQ-007).

## Scope
**Release unit**: N/A: document row (Plan Phase 7), after the code rows land.

## Assumptions
- The `Approval Record` section (289-297) already records the task-level approval as acceptance evidence and states no individual-name record exists; no new record is added (UNK-05 governs individual statements).
- The adrrev plans are archived with completed procedures: the `Implementation` column in the Automated Tests table (rows 242-262) and Decision Detail 12 (line 103) are already applied; re-read before editing and change different sentences than those documents did.

## Design decisions
- N/A: document describes the code decision made by rows 01-07.

## Alternatives considered
- Adding a new "pending approval" record row: rejected; the Approval Record exists and per UNK-05 individual statements are maintainer-written, not added by this Plan.

## Implementation
### Target file
`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
### Procedure
Edit the sentences that name the removed format or the old audit shape; leave the Approval Record untouched.
### Method
Sentence-level edits inside existing decisions and notes; no new sections.
### Details
- Decision #10 (line 93): name only `consumer_authorization` for the runtime update.
- Operator guidance (193): "explicit `consumer_authorization` mappings" (drop the second mapping).
- Automated Tests table row (247 area): the empty-mappings deny-all row names only `consumer_authorization` after the test is renamed/updated by row 14; keep the Implementation column text in sync with the final test names.
- Implementation Notes (268 area): grants are built from `consumer_authorization` only.
- Any bind/auth_token decision text must match the single `__post_init__` rule (loopback-only bind, required `auth_token`).

## Compatibility considerations
- The ADR is also touched by rmcompat007 (label sweep on other sentences); run this Plan first and re-read before editing.

## Security considerations
- N/A: documentation.

## Rollback considerations
- Git revert; ADR preservation rules apply (`check_adr_preservation.py`).

## Validation plan
- `uv run python tools/check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_reference.py`, `check_known_deviation_sync.py`.
- AC-7: document matches code after rows 01-07.

## Completion criteria
- No decision text describes `topic_authorization` or the `gen:` suffix; ADR checkers report no findings.

## Out of Scope
- Individual approval statements (UNK-05); the Approval Record content itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-135237
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
