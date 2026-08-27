## Goal

Add a regression test for `_clear_previous_turn_ephemeral_messages()` covering
`_skill_ephemeral` (REQ-001), per `plans/20260826-121839_plan.md`.

## Scope

- In scope: one new test (in a dedicated `TestClearPreviousTurnEphemeralMessages`-
  style class, per this Plan's own Tests section) calling
  `Orchestrator._clear_previous_turn_ephemeral_messages()` directly against a
  hand-built `ctx.conv.history`.
- Out of scope: `TestEphemeralMessageLifecycle` (the existing integration-style
  class exercising `_process_turn()` end-to-end — a different, valid test style
  for a different concern; not modified by this item); any other existing test in
  this file.

## Assumptions

- `scripts/agent/orchestrator.py`'s `_EPHEMERAL_KEYS` has been (or is being, in
  this same pass, seq 02) extended to include `"_skill_ephemeral"` — this new
  test's assertion depends on that change landing together.
- This file's existing `_make_ctx()`/`_make_orchestrator()` helpers (verified
  2026-08-27 at lines 34, 111) are reusable for this new test — confirm their
  exact signatures before use, since `_clear_previous_turn_ephemeral_messages()`
  only reads `self._ctx.conv.history` (per its implementation at lines 627-638),
  so a full turn-processing setup is not required, only a `ctx` with a
  hand-built `conv.history`.

## Design decisions

- Add a new `TestClearPreviousTurnEphemeralMessages` class (per this Plan's own
  Tests section naming), calling
  `orch._clear_previous_turn_ephemeral_messages()` directly — a narrower, more
  direct unit-test style than `TestEphemeralMessageLifecycle`'s end-to-end
  `_process_turn()` exercise, appropriate since this item tests one method's
  logic in isolation.
- Cover the `_skill_ephemeral`-only case (no `_ephemeral`/`_memory_injected` key)
  alongside the pre-existing `_ephemeral`/`_memory_injected` cases, per REQ-001's
  Acceptance Criteria — a message tagged only with `_skill_ephemeral` and no
  other ephemeral key must still be removed.

## Alternatives considered

- Adding the `_skill_ephemeral` case to the existing
  `TestEphemeralMessageLifecycle` class (as another end-to-end `_process_turn()`
  test) was considered and rejected — that class's existing tests all involve the
  memory/mode-classification pipeline, which is unrelated to `/skill`; a direct
  unit test of `_clear_previous_turn_ephemeral_messages()` is simpler and more
  targeted, and is what this Plan's own Tests section specifies.

## Implementation
### Target file
`tests/agent/test_orchestrator.py`

### Procedure
1. Add a new `TestClearPreviousTurnEphemeralMessages` class with a test method
   constructing `ctx.conv.history` containing a mix of ephemeral-tagged messages
   (including one tagged only with `_skill_ephemeral`) and non-ephemeral messages,
   calling `_clear_previous_turn_ephemeral_messages()`, and asserting only the
   non-ephemeral messages remain.
2. Run `uv run pytest tests/agent/test_orchestrator.py -v` (will fail on the new
   `_skill_ephemeral` assertion until seq 02, `orchestrator.py`, is also applied —
   or pass if this item lands after that change).

### Method
Direct file addition (Edit tool) — one new test class with one or more test
methods; no changes to existing classes.

### Details
Example shape (verify against `_make_ctx()`/`_make_orchestrator()`'s actual
signatures before finalizing):
```python
class TestClearPreviousTurnEphemeralMessages:
    """Direct unit coverage for Orchestrator._clear_previous_turn_ephemeral_messages()."""

    def test_removes_ephemeral_memory_injected_and_skill_ephemeral_messages(
        self,
    ) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [
            {"role": "system", "content": "kept"},
            {"role": "system", "content": "eph", "_ephemeral": True},
            {"role": "system", "content": "mem", "_memory_injected": True},
            {"role": "system", "content": "skill", "_skill_ephemeral": True},
        ]
        orch = _make_orchestrator(ctx)
        orch._clear_previous_turn_ephemeral_messages()
        assert ctx.conv.history == [{"role": "system", "content": "kept"}]

    def test_skill_ephemeral_only_message_removed_without_other_ephemeral_keys(
        self,
    ) -> None:
        """A message tagged only with _skill_ephemeral (no _ephemeral key) must
        still be cleared -- this is the specific gap REQ-001 fixes."""
        ctx = _make_ctx()
        ctx.conv.history = [
            {"role": "system", "content": "kept"},
            {"role": "system", "content": "skill only", "_skill_ephemeral": True},
        ]
        orch = _make_orchestrator(ctx)
        orch._clear_previous_turn_ephemeral_messages()
        assert ctx.conv.history == [{"role": "system", "content": "kept"}]
```
The second test method is the one that specifically pins down REQ-001's fix (a
`_skill_ephemeral`-only message, matching what `cmd_skill.py` actually produces
after `_ephemeral` is stripped by `validate_message()`'s sanitize fallback) — do
not omit it in favor of only the combined first test, since the combined test
alone would not distinguish "removed because of `_ephemeral`" from "removed
because of `_skill_ephemeral`" if a future regression re-broke only the latter.

## Compatibility considerations

- Test-only change; no production code path is affected.
- Depends on seq 02 (`orchestrator.py`) landing in the same change for the
  `_skill_ephemeral` assertions to pass.

## Security considerations

- N/A: test-only change, no security-relevant code path.

## Rollback considerations

- New-class-only revert via `git diff`/`git checkout -- <path>`; independent of
  other test classes in this file.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_orchestrator.py` | Unit | `uv run pytest tests/agent/test_orchestrator.py -v` | New tests pass once seq 02 has also landed; `TestEphemeralMessageLifecycle` and all other existing tests remain unaffected |

## Completion criteria

- A test confirms a conversation history containing only a `_skill_ephemeral`-
  tagged system message (no `_ephemeral` key) is empty of that message
  immediately after `_clear_previous_turn_ephemeral_messages()` runs.

## Out of scope

- `TestEphemeralMessageLifecycle` and any other existing test class in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestClearPreviousTurnEphemeralMessages` class with 2 test methods | Pending | — | — | |
| 2 | Run `uv run pytest tests/agent/test_orchestrator.py -v` | Pending | — | — | Requires seq 02 applied first |

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
- **Requirement ID**: REQ-001
- **Source issue**: `issues/20260821_08_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-121839_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-112248
- **Related target files**: `tests/agent/test_orchestrator.py`
