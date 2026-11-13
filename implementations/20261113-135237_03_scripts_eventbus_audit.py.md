## Goal

Define the EventBus `error_type` values as constants, give authorization changes a dedicated audit function that requires both generation fields, and replace the copied mdq/web_search docstring (REQ-004, REQ-005, REQ-006).

## Scope
**Release unit**: authorization-audit-record (shared with rows 04, 05, 14)

## Assumptions
- A new `log_authorization_change` (new) function plus an `AuthzChangeRecord` (new) type keeps `log_privileged_action` unchanged for records that have no generation (DLQ requeue, replay, startup) (Plan Assumptions).
- The `error_type` values already emitted (`authentication_failed`, `authorization_failed`, `consumer_identity_rejected`, `topic_authorization_rejected`) become the constants; the strings do not change.

## Design decisions
- `AuthzChangeRecord` (new) extends the record type with required `previous_generation` and `new_generation`; `log_authorization_change` (new) takes both as required keyword arguments (Plan Design).

## Alternatives considered
- Making the generation fields required on `log_privileged_action`: rejected; it breaks DLQ, replay, and the startup record (Plan Design).

## Implementation
### Target file
`scripts/eventbus/audit.py`
### Procedure
Rewrite the module docstring to describe only the EventBus vocabulary, add the constants, add the record type and function, and trim the general-purpose function.
### Method
Docstring rewrite plus two new public symbols; existing callers of `log_privileged_action` that pass no generation are untouched.
### Details
- Replace the docstring (lines 1-34), which currently copies the mdq/web_search "two vocabularies" text and opens with `Mirrors scripts/mcp_servers/audit.py`, with an EventBus-only vocabulary description containing no `Precedent`, `Mirrors scripts/`, or `REQ-` text (REQ-006).
- Add module constants for the four emitted values (REQ-005): `AUTHENTICATION_FAILED = "authentication_failed"`, `AUTHORIZATION_FAILED = "authorization_failed"`, `CONSUMER_IDENTITY_REJECTED = "consumer_identity_rejected"`, `TOPIC_AUTHORIZATION_REJECTED = "topic_authorization_rejected"` (new); `auth.py` (row 02) imports them.
- Add `AuthzChangeRecord` (new) with required `previous_generation` and `new_generation`, and `log_authorization_change` (new) with both as required keyword arguments (REQ-004).
- Remove the generation parameters from `log_privileged_action` (134-177) and from the record type (the `NotRequired` generation fields at 59-62); startup, DLQ, and replay records are unchanged (REQ-004).

## Compatibility considerations
- Existing JSON-lines log queries keep working: the vocabulary strings are unchanged.
- Rows 04 and 05 switch their call sites in the same unit; row 14 updates the test assertions.

## Security considerations
- Required generation fields make an authorization-change record that omits them a type/call error instead of an ambiguous record (REQ-004).

## Rollback considerations
- Reverting the file restores `log_privileged_action` with optional generation kwargs; already-written records are append-only and unaffected (UNK-01: only new records change).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_auth.py tests/eventbus/test_admin_topics_authorization.py tests/eventbus/test_authz_generation_ttl.py`
- AC-6: `rg -n "Precedent|Mirrors scripts/|REQ-[0-9]+" scripts/eventbus/audit.py` returns nothing.
- AC-4: admin audit tests show both generation fields on every authorization record.

## Completion criteria
- Constants exist and are used by `auth.py`; `log_authorization_change` (new) is the only writer of authorization-change records; `log_privileged_action` has no generation parameters.

## Out of Scope
- `audit.py`'s `REQ-` free text is governed only by AC-6's label patterns; no other audit vocabulary migration is in scope.

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
- **Requirement ID**: REQ-004, REQ-005, REQ-006
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-135237
- **Related target files**: `scripts/eventbus/audit.py`
