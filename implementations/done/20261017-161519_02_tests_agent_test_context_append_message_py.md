# Implementation Procedure — `tests/agent/test_context_append_message.py`

## Goal

Add regression coverage for the session-history restore ephemeral-key fix (`REQ-002`,
`REQ-003`, `REQ-004`).

## Scope

Modify only `tests/agent/test_context_append_message.py`. Append:
- a tampered-row test (restore a row carrying `source="cmd_handler"` + `_ephemeral`, assert
  the key is absent from history) — REQ-004;
- a backward-compat test (well-formed restored row without ephemeral keys is preserved) —
  REQ-003;
- a live-path regression (an `append_message()` with a trusted source still preserves an
  ephemeral key) — REQ-002.
Depends on the code change in `scripts/agent/context.py` (this plan's row 1).

## Assumptions

- The existing test file covers `replace_history()` / `extend_messages()` / `append_message()`
  (plan says ~4330 bytes); append new async test functions rather than rewriting fixtures.
- Row 1 forces an untrusted sentinel source on restore, so a restored row with an embedded
  trusted `source` + ephemeral key no longer retains the key.

## Design decisions

- Build the tampered row exactly as the issue describes:
  `{"role": "user", "content": "x", "source": "cmd_handler", "_ephemeral": True}`.
- Assert on `conv.history` after `replace_history()` completes, not on intermediate state.
- For the live-path regression, use a trusted source (e.g. `cmd_handler`) via `append_message`
  and assert the ephemeral key IS preserved (proving the live path is unchanged).

## Alternatives considered

- Asserting the key is stripped via the sanitized message vs. absent from history: assert
  absence from `conv.history` (the observable, behaviorally meaningful outcome).

## Implementation

### Target file

`tests/agent/test_context_append_message.py`

### Procedure

1. Add an async test that constructs a `ConversationState` (or reuse the existing fixture),
   calls `replace_history()` with the tampered row, awaits it, and asserts
   `"_ephemeral"` is not present in any `conv.history` entry.
2. Add a backward-compat test restoring a well-formed row (no ephemeral keys) and asserting
   the stored message equals the input (REQ-003).
3. Add/confirm a live-path test that `append_message()` with a trusted source preserves an
   ephemeral key (REQ-002).
4. Ensure the tampered-row test uses the same async setup/teardown as neighboring tests.

### Method

Append test functions; reuse existing fixtures/helpers.

### Details

- If the test helper builds rows differently, mirror the production row shape (dict with
  `role`, `content`, `source`, `_ephemeral`).

## Compatibility considerations

N/A: test-only change.

## Security considerations

The test encodes a security property (fail closed on restore); keep it focused and not
dependent on sensitive data beyond the ephemeral-key marker.

## Rollback considerations

Revert the commit to the test file.

## Validation plan

- Run the context tests; all pass.
- Command: `uv run pytest tests/agent/test_context_append_message.py -q`.

## Completion criteria

Tampered-row test asserts the ephemeral key is absent from history; backward-compat and
live-path regressions pass.

## Out of scope

`scripts/agent/context.py` (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes in test_context_append_message.py | Completed | 20261018-102823 | 20261018-102823 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261018-102823 | 20261018-102823 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261018-102823 | 20261018-102823 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261018-102823 | 20261018-102823 | N/A |

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
- **Requirement ID**: `REQ-002` (live path unchanged), `REQ-003` (backward compat),
  `REQ-004` (tampered-row regression)
- **Source issue**: `issues/20261017-123157_restore01_block-ephemeral-key-injection-through-session-history-restore.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-142742_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-161519
- **Related target files**: `tests/agent/test_context_append_message.py`