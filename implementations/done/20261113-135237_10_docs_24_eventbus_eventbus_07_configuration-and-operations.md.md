## Goal

Update the EventBus configuration and operations document to describe the single authorization format, the bind rule, and the audit record without the `gen:` suffix (REQ-007).

## Scope
**Release unit**: N/A: document row (Plan Phase 7), after the code rows land.

## Assumptions
- rmcompat005 targets the same document for DLQ sentences; run this Plan first, re-read before editing, and change different sentences than that Plan's completed edits.

## Design decisions
- N/A.

## Alternatives considered
- Leaving the optional-`topic_authorization` sentence as historical note: rejected; the repository documents current policy only (compatrm001, Plan Reason for Change).

## Implementation
### Target file
`docs/24_eventbus/eventbus_07_configuration-and-operations.md`
### Procedure
Replace the two-format allowlist wording with the single format and update the audit-record description.
### Method
Sentence-level edits.
### Details
- Line 60: describe `consumer_authorization` (`consumer_id` -> topics) as the only allowlist applied to the consumer-role token; delete the `topic_authorization` clause.
- Line 79: drop "(and optionally `topic_authorization`)" from the Consumer-process sentence.
- Lines 90-91: the sweep emits one `log_authorization_change` audit record per changed removal cycle, and generation-changing records carry `previous_generation` and `new_generation` in the record itself — delete the sentence's claim that `detail` ends with a `gen:<prev>-><new>` suffix.
- Keep the bind description consistent with the single `__post_init__` rule (loopback-only bind, required `auth_token`) — verified 2026-11-13: the token/bind sentences (57-58) and the Bind Address section (106-107) already state loopback-only with no "set a token" advice; no edit is needed there, confirm only after rows 01-07 land.
- Verified 2026-11-13: the cited lines match the working tree — 60 (two-format allowlist sentence), 79 ("(and optionally `topic_authorization`)"), 90-91 (sweep `log_privileged_action` record and the `gen:` suffix claim). Line 90's function name also changes to `log_authorization_change`; line 97's startup `log_privileged_action` record stays unchanged.

## Compatibility considerations
- Describe intent, boundaries, and failure behavior only (Plan Documentation Impact); no code snippets beyond existing style.

## Security considerations
- N/A: documentation.

## Rollback considerations
- Git revert; docs checkers gate the change.

## Validation plan
- `check_docs_consistency.py --domain eventbus`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.
- AC-7: document matches code after rows 01-07.

## Completion criteria
- No sentence names `topic_authorization` or the `gen:` suffix; docs checkers report no findings.

## Out of Scope
- DLQ sentences owned by rmcompat005.

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
- **Related target files**: `docs/24_eventbus/eventbus_07_configuration-and-operations.md`
