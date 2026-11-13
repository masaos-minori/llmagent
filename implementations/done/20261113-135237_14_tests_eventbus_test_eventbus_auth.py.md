## Goal

Update the auth test suite for the removed `topic_authorization` format, the new audit function, and the error-type constants (REQ-002, REQ-004, REQ-005).

## Scope
**Release unit**: single-authorization-format (fixture deletions, part A) and authorization-audit-record (constant use and audit-record assertions, part B; after row 03 lands). Plan Release units list this file in both phases.

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
- Delete the `topic_authorization=` config arguments at 875, 931, 975, 1517 (verified 2026-11-13) and express the same consumer grants through `consumer_authorization` only.
- The rejection test (1135) keeps its shape and its name `test_topic_authorization_rejection_produces_structured_audit_record` — the name refers to the `topic_authorization_rejected` audit error value, which stays (row 03 makes it a constant); assert `error_type` against `audit.TOPIC_AUTHORIZATION_REJECTED` (1166) and convert the other literals at 1058 (`authentication_failed`), 1094 (`authorization_failed`), 1130 (`consumer_identity_rejected`) — verified 2026-11-13: the original document omitted 1058/1094/1130 (REQ-005; part B, after row 03 lands).
- Verified 2026-11-13: lines 1252-1253 are NOT function patches — the test patches `eventbus.audit.logger.warning`/`info` (1225-1226), captures JSON records, filters `event == "privileged_action"` (1245-1249), and asserts the generation fields on the captured record. Because row 03's `log_authorization_change` keeps `event="privileged_action"`, these assertions pass unchanged; the required change here is to add a `detail` assertion that the record carries no `gen:` suffix (REQ-004).
- Verified 2026-11-13: this file contains no `log_privileged_action` reference and no `_CONSUMER_ID_ALLOWLIST` reference, so row 02's allowlist deletion and row 03's signature trim need no matching edit here; the `REQ-001` docstring labels near 1670 and 1694 describe the unified consumer authorization path (not the REQ-007/REQ-008 labels rmcompat007 sweeps) and stay.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-13 | 2026-11-13 | — |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-13 | 2026-11-13 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-13 | 2026-11-13 | unit-2 targeted+full suites green; diff-cover 100% |
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
- **Requirement ID**: REQ-002, REQ-004, REQ-005
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-135237
- **Related target files**: `tests/eventbus/test_eventbus_auth.py`
