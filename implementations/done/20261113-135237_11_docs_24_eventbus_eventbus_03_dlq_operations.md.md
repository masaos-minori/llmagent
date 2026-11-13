## Goal

Update the DLQ operations document's authorization allowlist sentence to the single `consumer_authorization` format (REQ-007).

## Scope
**Release unit**: N/A: document row (Plan Phase 7), after the code rows land.

## Assumptions
- The fail-closed statements in the same sentence (empty `consumer_authorization` denies all; shared tokens hold no CONSUMER role) stay true and keep their wording.

## Design decisions
- N/A.

## Alternatives considered
- Deleting the whole sentence: rejected; consumer authorization still gates DLQ-adjacent consumer routes and the fail-closed rule is operator-relevant.

## Implementation
### Target file
`docs/24_eventbus/eventbus_03_dlq_operations.md`
### Procedure
Edit the allowlist sentence.
### Method
One-sentence edit.
### Details
- Line 108: verified 2026-11-13 — the current sentence reads "The allowlist comes from `consumer_authorization` and `topic_authorization` in `config/eventbus.toml`, and applies to the CONSUMER-role token only."; delete the `topic_authorization` name (and its conjunction), keep the fail-closed, deny-all, and 403 statements unchanged. The surrounding 106 sentence names no removed format and stays.

## Compatibility considerations
- None beyond wording; no route or DLQ behavior changes in this Plan.

## Security considerations
- N/A: documentation.

## Rollback considerations
- Git revert.

## Validation plan
- `check_docs_consistency.py --domain eventbus`, `check_docs_structure.py`, `check_docs_content_policy.py`.
- AC-2/AC-7: `rg -n "topic_authorization" docs/24_eventbus/eventbus_03_dlq_operations.md` returns nothing.

## Completion criteria
- The sentence names only `consumer_authorization`; docs checkers report no findings.

## Out of Scope
- Other DLQ operations text (rmcompat005 owns DLQ code leftovers; its document edits are separate sentences).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-13 | 2026-11-13 | — |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-13 | 2026-11-13 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-13 | 2026-11-13 | eventbus-domain docs checkers clean; whole-tree structure findings in unrelated files (adr_012 size, deployment_01/security_01 duplicate links) are pre-existing HEAD drift, out of this Plan's scope |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-13 | 2026-11-13 | — |

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
- **Related target files**: `docs/24_eventbus/eventbus_03_dlq_operations.md`
