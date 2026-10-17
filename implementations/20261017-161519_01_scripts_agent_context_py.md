# Implementation Procedure — `scripts/agent/context.py`

## Goal

Close the ephemeral-key control bypass in `ConversationState.replace_history()` so
tampered/corrupted session rows cannot inject reserved ephemeral keys (`_ephemeral`,
`_memory_injected`) into conversation history. Treat every restored message as untrusted so
an embedded trusted `source` can no longer authorize ephemeral keys; the key is rejected and
stripped by the existing sanitization machinery (`REQ-001`, `REQ-002`, `REQ-003`).

## Scope

Modify only `scripts/agent/context.py`. Route `replace_history()` through an untrusted
validation path so ephemeral keys are always stripped on restore, while leaving the
live-append path (`append_message()` / `extend_messages()` / `_append_message_locked()` live
calls) untouched. Add a module constant guaranteed absent from `TRUSTED_SOURCES`.

## Assumptions

- `replace_history(self, msgs, *, source="")` (lines ~170–177) calls
  `await self._append_message_locked(msg, source=source)` with default `source=""`.
- `_append_message_locked(self, msg, *, source="")` builds
  `check_view = dict(msg, source=source) if source else dict(msg)`, so a non-empty source
  overwrites the message's embedded `source` in the validation view; on success the ORIGINAL
  `msg` is appended (embedded source field preserved); on failure `_sanitize_message(msg,
  source=source)` strips disallowed keys.
- `validate_message(check_view)` (message_schema.py lines 68–80) authorizes ephemeral keys
  using `check_view`'s `source`; a source not in `TRUSTED_SOURCES` fails any ephemeral key.
- `TRUSTED_SOURCES` is defined at message_schema.py:18; all three `replace_history()` callers
  (session_restore.py:64,66; startup_prompt_setup.py:114) use default `source=""` — no
  trusted-resume path exists.

## Adversarial verification findings (plan discrepancies)

- **No discrepancy.** Verified against current source: the gap is real and the recommended
  mechanism (force an untrusted sentinel source on restore) closes it without altering the
  live-append path. Non-ephemeral restored messages still pass validation unchanged
  (backward compatible, REQ-003).

## Design decisions

- **Boundary (named decision): restore = untrusted; live append = trusted.** Restore data
  comes from `session.sqlite`, which a local actor may tamper with, so every restored row is
  treated as untrusted.
- Prefer approach (a) — force a non-empty untrusted sentinel source on restore. It is the
  minimal, centralized change: one line in `replace_history()` plus one module constant. The
  sentinel overwrites the embedded `source` in the validation view, so ephemeral keys are
  rejected and stripped by `_sanitize_message()`.
- Approach (b) (explicitly strip `_ALL_EPHEMERAL_KEYS` before appending) is acceptable if
  the maintainer prefers it; reuse `_ALL_EPHEMERAL_KEYS` from message_schema.py rather than
  hardcoding the set. Implement exactly one.

## Alternatives considered

- Modifying `message_schema.py`'s `validate_message`/`TRUSTED_SOURCES`: rejected — out of
  scope and would change the normal-path semantics for all sources.
- Stripping keys in `replace_history()` directly (approach b) vs. routing through the
  untrusted source (approach a): both work; (a) reuses existing validation+sanitization and
  is more centralized.

## Implementation

### Target file

`scripts/agent/context.py`

### Procedure

1. Add a module-level constant near the other module constants:
   ```python
   _UNTRUSTED_RESTORE_SOURCE = "__restore_untrusted__"  # guaranteed absent from TRUSTED_SOURCES
   ```
2. In `replace_history()`, change the per-message call from
   `await self._append_message_locked(msg, source=source)` to
   `await self._append_message_locked(msg, source=_UNTRUSTED_RESTORE_SOURCE)`.
3. Confirm the chosen sentinel value is NOT present in `TRUSTED_SOURCES` (message_schema.py:18)
   — if it were, remove it and pick another unlikely constant.
4. Leave `append_message()`, `extend_messages()`, and the live `_append_message_locked()`
   call sites untouched.

### Method

Edit the constant block and the single line in `replace_history()`. Re-run the context tests.

### Details

- The sentinel must be non-empty (empty string means "use the embedded source").
- The appended message retains its embedded `source` field unchanged; only the validation
  view is overridden, so non-ephemeral messages validate normally.
- The sentinel appears only in the validation reason string on failure (cosmetic); acceptable
  for a security fix.

## Compatibility considerations

- REQ-002: the live-append path (`append_message()` / `extend_messages()`) is unchanged;
  trusted in-process sources still inject ephemeral keys normally.
- REQ-003: restored rows without ephemeral keys validate and append unchanged.

## Security considerations

Fail closed: a restored row carrying a trusted embedded `source` plus a reserved ephemeral
key no longer retains that key. This restores the ADR-backed integrity boundary that a local
session-DB tamperer could otherwise bypass.

## Rollback considerations

Revert the commit to `scripts/agent/context.py`.

## Validation plan

- Unit (`tests/agent/test_context_append_message.py`):
  - Tampered row: restore `[{"role": "user", "content": "x", "source": "cmd_handler",
    "_ephemeral": True}]` and assert `"_ephemeral"` is absent from `conv.history` (REQ-004).
  - Backward compat: restore a well-formed row (no ephemeral keys) and assert content is
    preserved unchanged (REQ-003).
  - Live path: `append_message()` with a trusted source still preserves an ephemeral key
    (REQ-002).
- Command: `uv run pytest tests/agent/test_context_append_message.py -q`.
- Lint/type: `uv run ruff check scripts/agent/context.py` and `uv run mypy
  scripts/agent/context.py` clean.

## Completion criteria

`replace_history()` strips ephemeral keys from restored rows regardless of any embedded
trusted `source`; the live-append path and non-ephemeral restores are unchanged.

## Out of scope

`message_schema.py`'s `validate_message`/`TRUSTED_SOURCES`, the live-append path, the
`undo` path, `extend_messages()` (live in-process path), the test file (separate row), and
the doc update (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route replace_history() through untrusted-source validation | Pending | — | — | approach (a) recommended |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: test file is a separate row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: doc is a separate row |

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
- **Requirement ID**: `REQ-001` (reject/strip ephemeral keys on restore, fail closed),
  `REQ-002` (live-append path unchanged), `REQ-003` (non-ephemeral restores unaffected)
- **Source issue**: `issues/20261017-123157_restore01_block-ephemeral-key-injection-through-session-history-restore.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-142742_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-161519
- **Related target files**: `scripts/agent/context.py`
