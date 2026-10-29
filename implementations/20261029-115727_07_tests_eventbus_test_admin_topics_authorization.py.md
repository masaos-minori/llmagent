## Goal

Extend the two existing admin audit tests to assert the new record fields (`REQ-001`, `REQ-004`, `REQ-005`; AC-1, AC-3): request id non-empty, actor equals the admin token fingerprint, `detail` carries the mappings/counts summary with `persistent:false`, and the no-op case still emits nothing.

## Scope

Edit only the audit tests in `tests/eventbus/test_admin_topics_authorization.py`: the assertions inside `test_audit_emitted_on_effective_change` (the `:187` test) and, if needed for readability, its docstring. The fixture and all other tests stay unchanged.

## Assumptions

- Source claims re-verified this cycle (2026-10-29): both audit tests patch `eventbus.admin_route.log_privileged_action` and assert on `mock_log.call_args.kwargs` (the call is made with keyword arguments at `admin_route.py:141-147`); the admin fixture token is `admin-tok`; the fixture's initial `consumer_authorization` is `{"c1": ["topicA"]}`; the effective-change body in the test is `{"c1": ["topicA", "topicB"]}`, which changes exactly one mapping entry.
- The no-op test already pins "no record emitted" (`call_count == 0`) and needs no new assertions; extending it would assert on a record that does not exist. Its docstring is kept truthful.
- Sequencing: land after `implementations/20261029-101422_03_tests_eventbus_test_admin_topics_authorization.py.md` (adds a new class; per its own note land after `ebaudit005` -- reconcile by landing this row first for the two audit tests, since 101422_03 only appends a class and does not touch them) and before `implementations/20261029-102038_12_tests_eventbus_test_admin_topics_authorization.py.md` (comment-identifier cleanup, which re-runs its search at implementation time).
- `detail` shape after seq 03 for this fixture/body: `consumer_authorization:1;persistent:false` (UNK-03 format fixed in seq 03).

## Design decisions

- New assertions in `test_audit_emitted_on_effective_change`, keeping the existing call-count and `target` assertions:
  - `call_args.kwargs["request_id"]` is a non-empty string.
  - `call_args.kwargs["actor"] == _derive_token_fingerprint("admin-tok")` (import `from eventbus.auth import _derive_token_fingerprint` in the test module).
  - `call_args.kwargs["detail"] == "consumer_authorization:1;persistent:false"` (replaces the `detail == "updated"` assertion).
- Assert the fingerprint via the same derivation function the auth layer uses, not a hardcoded hash literal, so hash-algorithm changes don't break the test.

## Alternatives considered

- Asserting only non-emptiness of `detail`: rejected; the exact string pins the UNK-03 format decision and catches format drift.

## Implementation
### Target file

`tests/eventbus/test_admin_topics_authorization.py`

### Procedure

1. Add `from eventbus.auth import _derive_token_fingerprint` to the module imports.
2. In `test_audit_emitted_on_effective_change`, replace the `detail == "updated"` assertion with the summary-string assertion and add the `request_id` non-empty and `actor` equality assertions listed above.

### Method

Assertion-level edits inside one existing test function; no fixture or client changes.

### Details

- Keep `test_audit_not_emitted_on_noop` behavior unchanged (it remains the no-op guard for AC-3).
- Line numbers shift after 101422_03 lands; locate the tests by name, not line.

## Compatibility considerations

- Test-only change; the `detail == "updated"` assertion is intentionally replaced in the same batch as the seq 03 production change (they must land together).

## Security considerations

- The test proves the record carries the fingerprint, not the raw `admin-tok` value (the equality against the derived fingerprint implies it).

## Rollback considerations

- Restore the previous assertion set together with the seq 03 revert.

## Validation plan

- `uv run pytest tests/eventbus/test_admin_topics_authorization.py -v`.
- `uv run ruff check tests/eventbus/test_admin_topics_authorization.py` and `uv run mypy tests/eventbus/test_admin_topics_authorization.py`.

## Completion criteria

- Effective-change test asserts non-empty request id, correct fingerprint actor and the exact detail summary; no-op test still asserts zero records.

## Out of Scope

- The publish-order regression class added by 101422_03, identifier-label cleanup (102038_12), production code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Land with seq 03 (detail shape coupling) |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row is the tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-001, REQ-004, REQ-005 (AC-1, AC-3)
- **Source issue**: `issues/20261028-122415_ebaudit005_privileged-audit-actor-context.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-115727
- **Related target files**: tests/eventbus/test_admin_topics_authorization.py
