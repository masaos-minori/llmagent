## Goal

Remove all `topic_authorization` handling from the admin endpoint and write its audit record through the new `log_authorization_change` function without the `gen:` detail suffix (REQ-002, REQ-004).

## Scope
**Release unit**: single-authorization-format (with rows 01, 02, 05, 06, 07, 14, 17); the audit-call change belongs to the authorization-audit-record release unit (with rows 03, 05, 14)

## Assumptions
- The endpoint keeps requiring `expected_generation` (143-166); the client's missing parameter is UNK-06 and out of scope.
- The `REQ-002`, `REQ-005`, `REQ-007` comment labels in this file (114, 143, 171, 238) are outside this row's scope and stay for the rmcompat007 Plan; AC-6's grep does not cover this file.

## Design decisions
- N/A: the Plan Design fixes the call shape (`log_authorization_change` with both generation kwargs); no further decision in this file.

## Alternatives considered
- Keeping `topic_authorization` on the endpoint and ignoring it: rejected; REQ-002 removes the second format outright.

## Implementation
### Target file
`scripts/eventbus/admin_route.py`
### Procedure
Delete the validator and every `topic_authorization` path, then replace the audit call.
### Method
Text deletion plus one call-site replacement; the route registration and response shape are unchanged.
### Details
- Delete `_validate_topic_authorization` (64-90) and its uses: the body-key read (137-141), the replacement entry (193-194), and the changed-count block (206-212).
- Update the 422 empty-body text (128) to name only `consumer_authorization` (and note `expected_generation` is mandatory); update the docstring summary (107) to name only `consumer_authorization`.
- Keep the `expected_generation` validation and the generation-conflict response (143-166) unchanged.
- In the audit block (263-276): drop the `gen:` detail part (266), call `log_authorization_change` (row 03) with `previous_generation=current_gen.generation` and `new_generation=new_generation_number` as required kwargs, and keep `target="topics_authorization"` (271) and the remaining detail parts (REQ-004).
- Update the import (12) to `log_authorization_change` alongside `log_privileged_action` if any non-generation call remains in this file.

### Companion test files
- `tests/eventbus/test_admin_topics_authorization.py`
  - Procedure: replace the `log_privileged_action` generation-kwarg assertions (397-414) with `log_authorization_change` assertions; drop the `gen:` detail assertion (208); add the every-record test asserting both generation fields on each authorization record; remove the `topic_authorization` request cases and assert the empty-body 422 names only `consumer_authorization` (610).
  - Validation: `uv run pytest tests/eventbus/test_admin_topics_authorization.py`

## Compatibility considerations
- The request body loses `topic_authorization`; unknown body keys are ignored server-side, so an operator script still sending it lands on the existing no-op/422 path (UNK-04).
- Response shape and route registration are unchanged, so the manifest change is summary-only (row 08).

## Security considerations
- Removing the second format eliminates configurations where the two mappings contradict each other (REQ-002).

## Rollback considerations
- Reverting this file restores the validator and the `gen:` suffix; audit records already written are append-only.

## Validation plan
- `uv run pytest tests/eventbus/test_admin_topics_authorization.py`
- AC-2 acceptance search: `rg -n "topic_authorization" scripts/eventbus/admin_route.py` returns nothing (`target="topics_authorization"` is a different string and stays).
- AC-4: no `gen:` in `detail`; both generation fields asserted on every authorization record.

## Completion criteria
- REQ-002 and REQ-004 states hold in this file; companion tests pass.

## Out of Scope
- Adding `expected_generation` to the client (UNK-06).
- `REQ-` label comments in this file (rmcompat007).

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
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-135237
- **Related target files**: `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py`
