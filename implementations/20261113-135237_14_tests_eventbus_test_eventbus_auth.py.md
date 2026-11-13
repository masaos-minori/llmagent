## Goal

Update the auth test suite for the removed `topic_authorization` format, the new audit function, and the error-type constants (REQ-002, REQ-004, REQ-005).

## Scope
**Release unit**: single-authorization-format and authorization-audit-record (this row's tests lock both units; Plan Release units list this file in both phases)

## Assumptions
- This row gets its own document (not a companion) because it is named in the `Related Tests` cell of two code rows (02 `auth.py`, 03 `audit.py`), which fails the companion eligibility rule (SKILL.md Core Execution Rules).
- The consumer-pair enforcement path (via `consumer_authorization` expansion in `auth.py`) and its `topic_authorization_rejected` audit error type stay; only the second configuration format disappears.

## Design decisions
- Assertions import the constants from `audit.py` instead of repeating literals (REQ-005), so a vocabulary change surfaces in one place.

## Alternatives considered
- Keeping literal strings in tests: rejected; REQ-005 requires the constants to be used by the consumers of the vocabulary.

## Implementation
### Target file
`tests/eventbus/test_eventbus_auth.py`
### Procedure
Drop the removed-format fixtures, switch audit assertions to the new function, and use the constants.
### Method
Fixture-argument removal and assertion replacement; test structure otherwise unchanged.
### Details
- Delete the `topic_authorization=` config arguments at 875, 931, 975, 1517 and express the same consumer grants through `consumer_authorization` only.
- The rejection test (1135) keeps its shape: grant/deny pairs now come from `consumer_authorization`; assert `error_type` against `audit.TOPIC_AUTHORIZATION_REJECTED` (1166) and the other values against `audit.AUTHENTICATION_FAILED`, `audit.AUTHORIZATION_FAILED`, `audit.CONSUMER_IDENTITY_REJECTED` (REQ-005).
- Replace the `log_privileged_action` generation-kwarg assertions (1252-1253) with `log_authorization_change` assertions on `previous_generation` and `new_generation`, and assert no `gen:` in `detail` (REQ-004).
- Re-read the file before editing: the recent route-registration refactor already trimmed it (current 1747 lines), so verify each cited line again in the working tree.

## Compatibility considerations
- Run in the same unit as rows 01-07 so no intermediate state leaves the suite red.

## Security considerations
- N/A: tests.

## Rollback considerations
- Git revert; no persisted state.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_auth.py`
- AC-4/AC-5: every admin authorization record assertion reads both generation fields; no `error_type` literal remains in this file.

## Completion criteria
- No `topic_authorization=` config arguments and no audit literals remain; the suite passes against the post-change `auth.py`/`audit.py`.

## Out of Scope
- Behavior coverage for `log_privileged_action` non-generation records (unchanged tests stay).

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
- **Requirement ID**: REQ-002, REQ-004, REQ-005
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-135237
- **Related target files**: `tests/eventbus/test_eventbus_auth.py`
