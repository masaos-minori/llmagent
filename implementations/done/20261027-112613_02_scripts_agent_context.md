## Goal

Update the field comments for `ConversationState.memory_disabled` and `ConversationState.memory_warning_shown` in `scripts/agent/context.py` so they describe the per-turn degraded-state semantics this Plan introduces instead of the outdated "failed during startup" framing. This is a comment-only change; no field type, default, or code is altered.

## Scope

- **In-Scope** (`scripts/agent/context.py` only):
  - Rewrite the inline comment on `memory_disabled` (line 110) to state that the flag reflects a per-turn injection failure and is cleared on the next successful attempt.
  - Rewrite the inline comment on `memory_warning_shown` (lines 111-113) to state that the warning is reset on recovery so a later degradation period re-warns once.
- **Out-of-Scope**:
  - The flag bookkeeping that sets/resets these fields (`scripts/agent/conversation_state_manager.py`; row 01).
  - The regression module (row 03) and the memory overview doc (row 04).

## Assumptions

- The two fields are dataclass defaults on `ConversationState` (lines 110-113); only their trailing inline comments are edited.
- The comments are read by developers, not by code, so the wording change has no runtime effect.
- `context.py` is broadly referenced (churn 8, dominant author), but a comment edit cannot alter behavior.

## Design decisions

- **Mirror the runtime semantics.** The new wording matches the behavior implemented in row 01: `memory_disabled` is a per-turn latch that clears on success, and `memory_warning_shown` re-arms on recovery.
- **Keep the comments terse.** Preserve the existing single-line-per-field style; extend only where the per-turn semantics require it.
- **No behavioral language.** Avoid implying a functional gate; the flags are visibility/bookkeeping only (none gate execution).

## Alternatives considered

- **Leaving the comments unchanged.** Rejected: they currently say "failed during startup" / "was displayed", which contradicts the per-turn reality this Plan corrects (REQ-004 / AC-004).

## Implementation

### Target file

`scripts/agent/context.py` (existing; comment-only edit)

### Procedure

1. Open `scripts/agent/context.py` and locate the two field declarations at lines 110-113.
2. Replace the inline comment on `memory_disabled` (line 110) from the startup-only wording to per-turn degraded-state wording, e.g. `# True when a memory-injection attempt failed; cleared on the next successful attempt`.
3. Replace the inline comment on `memory_warning_shown` (line 112) to note the reset-on-recovery behavior, e.g. `# Whether the "memory degraded" warning was shown; reset on recovery so a later degradation re-warns once`.
4. Leave the field names, types, and default values (`False`) byte-for-byte unchanged.
5. Run the validation sequence (`routing.md`).

### Method

The current declaration block (lines 110-113):

```
    memory_disabled: bool = False  # True when memory injection failed during startup
    memory_warning_shown: bool = (
        False  # Whether the "memory disabled" warning was displayed
    )
```

becomes:

```
    memory_disabled: bool = False  # True when a memory-injection attempt failed; cleared on the next successful attempt
    memory_warning_shown: bool = (
        False  # Whether the "memory degraded" warning was shown; reset on recovery so a later degradation re-warns once
    )
```

Only the text after each `#` changes.

### Details

- **`REQ-004` / `AC-004`:** both comments now describe per-turn degraded-state semantics; `memory_disabled` is no longer described as a startup-only latch and `memory_warning_shown` notes its reset-on-recovery behavior.

## Compatibility considerations

- Comment-only; no signature, type, default, or behavior change. Safe against the turn001 overlap judgment (disjoint members: this touches field comments, not snapshot/restore or write routing).

## Security considerations

- Documentation/comment change only; no new input surface or secret handling.

## Rollback considerations

- Revert the file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/context.py` | Comment-only; behavior pinned by row 03 tests | `uv run mypy scripts/`, `uv run ruff check scripts/` | Clean |
| Existing behavior | Regression | `uv run pytest tests/agent/test_startup_prompt_setup.py` | Pass unchanged |

## Completion criteria

- `memory_disabled` and `memory_warning_shown` comments describe per-turn degraded-state semantics; field names, types, and defaults are unchanged; `mypy` / `ruff` pass.

## Out of Scope

- Flag bookkeeping (row 01).
- The regression module (row 03).
- The memory overview doc (row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update field comments to per-turn degraded-state semantics | Completed | — | 20261027-185628 | REQ-004 Implemented and validated in the memory001 batch (full suite 10235 passed, diff coverage 98%) |
| 2 | Add regression tests (row 03) | Completed | — | 20261027-185628 | Dependency Implemented and validated in the memory001 batch (full suite 10235 passed, diff coverage 98%) |
| 3 | Run validation sequence | Completed | — | 20261027-185628 | mypy/ruff Implemented and validated in the memory001 batch (full suite 10235 passed, diff coverage 98%) |
| 4 | Update doc (row 04) | Completed | — | 20261027-185628 | REQ-005 Implemented and validated in the memory001 batch (full suite 10235 passed, diff coverage 98%) |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261026-224838_memory001_retry-memory-injection-failure.md`
- **Source plan**: `plans/20261027-072306_memory001_retry-memory-injection-failure.md`
- **Generated at**: 20261027-112613
- **Related target files**: `scripts/agent/context.py`