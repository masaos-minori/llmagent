# Block ephemeral-key injection through session history restore

## Priority
High

## Summary
Session restoration via `ConversationState.replace_history()` can carry reserved
ephemeral keys (`_ephemeral`, `_memory_injected`) into history when the source rows
carry a trusted embedded `source` value. Close the gap so tampered/corrupted
session rows cannot inject ephemeral-keyed messages that bypass filtering.

## Background
`message_schema.py` exists to prevent the LLM (or any untrusted source) from
manipulating ephemeral message filtering by injecting/removing keys such as
`_ephemeral` or `_memory_injected`. Ephemeral key injection is restricted to
trusted sources listed in `TRUSTED_SOURCES` (`cmd_handler`, `memory_injection`,
`loop_guard`). `docs/23_agent/agent_04_01_...state-model.md` Known Limitations
notes that session restoration via `replace_history()` allows corrupted/tampered
DB rows to introduce reserved ephemeral keys.

## Problem
`replace_history()` appends each message through `_append_message_locked()`:

```python
result = validate_message(check_view)
if result.success:
    self.history.append(msg)   # appends the ORIGINAL msg, keys intact
    return
```

`validate_message()` decides ephemeral-key legitimacy using the message's OWN
embedded `source` field:

```python
source = msg.get("source", "")
if source not in TRUSTED_SOURCES:
    return ValidationResult(False, ...)
allowed_ephemeral = TRUSTED_SOURCES[source]
unauthorized = ephemeral_keys - allowed_ephemeral
if unauthorized:
    return ValidationResult(False, ...)
```

So a session row that carries `source="cmd_handler"` together with
`"_ephemeral": True` passes validation and is appended with the ephemeral key
intact. An actor who can write to `session.sqlite` (corruption or tampering) can
therefore inject ephemeral-keyed messages that survive inter-turn cleanup,
defeating the protection `message_schema.py` is designed to enforce. The
sanitization path (`_sanitize_message`) only strips keys when validation fails,
and validation passes here because the embedded source looks trusted.

## Reason for Change
This is a security-sensitive control bypass. The ephemeral-key filter is an
explicit integrity boundary (ADR-backed); a local session-DB tamperer gaining the
ability to inject filtered-class messages weakens conversation-history
integrity. It should fail closed.

## Implementation Intent
Make session restore independent of any `source` carried inside restored rows.
During restore, treat every restored message as untrusted: either (a) force
`source` to an untrusted value so ephemeral keys are always rejected/stripped, or
(b) strip reserved ephemeral keys explicitly on restore. Prefer the minimal
change that makes restore fail closed without altering the live-append path used
by trusted in-process sources. Name the boundary (restore vs. live append) as the
design decision.

## Target Files or Areas
- `scripts/agent/context.py` (`replace_history`, `_append_message_locked`, lines ~132-156, 170-177)
- `scripts/agent/message_schema.py` (`validate_message`, `TRUSTED_SOURCES`)
- `scripts/agent/services/session_restore.py` (caller that drives restore)

## Required Changes
- Ensure `replace_history()` does not honor an embedded `source` that would
  authorize ephemeral keys; ephemeral keys on restored rows must be rejected or
  stripped.
- Keep the live-append path (`_append_message_locked` via normal turn flow)
  unchanged so trusted in-process sources still work.
- Add a test that restores a row carrying `source="cmd_handler"` + `_ephemeral`
  and asserts the key is not present in history.

## Constraints
- Do not change validation semantics for live, trusted-source appends.
- Do not weaken `message_schema.py`'s protection for the normal path.
- Preserve backward compatibility for restored rows that carry no ephemeral keys.

## Acceptance Criteria
- A restored row carrying a trusted embedded `source` plus a reserved ephemeral
  key does not retain that key in history.
- Restored rows without ephemeral keys are unaffected.
- A regression test covers the tampered-row case.

## Testing Expectations
- Unit/integration test for `replace_history()` with a tampered row (asserts key
  stripped/rejected).
- Regression tests for restore of well-formed rows.
- Confirm session_restore callers still pass expected `source`.

## Documentation Impact
Update the Known Limitations bullet in
`docs/23_agent/agent_04_01_...state-model.md` to reflect resolution, or move the
item to a resolved note.

## Out of Scope
- Changing how ephemeral keys are injected during normal turns.
- Modifying `TRUSTED_SOURCES` membership.
- Other history-manipulation paths (`extend_messages`, undo) unless shown to share
  the same gap — assess and scope accordingly.

## Dependencies
- N/A: none

## Unresolved Questions
- Whether restore is ever legitimately called with a trusted `source` that
  SHOULD preserve ephemeral keys (e.g. resuming an in-progress injection). If so,
  the fix must distinguish resume-from-trusted-context from raw restore.
- The exact blast radius: which callers invoke `replace_history` and whether any
  depend on preserved ephemeral keys across restart.

## AI Implementation Instruction
Do NOT modify the live-append validation path or `TRUSTED_SOURCES`. Only make
`replace_history()`/`_append_message_locked()` when invoked for restore ignore any
embedded `source` that would authorize ephemeral keys, so tampered rows cannot
inject `_ephemeral`/`_memory_injected`. Add a regression test with a tampered row.
First enumerate all `replace_history` callers to confirm the fix does not break a
legitimate trusted-resume path; if one exists, handle it explicitly rather than
stripping keys globally.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261017-123157
- **Related target files**: `scripts/agent/context.py`, `scripts/agent/message_schema.py`, `scripts/agent/services/session_restore.py`
