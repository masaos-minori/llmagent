## Goal

Correct the now-inaccurate mechanism comment in
`test_startup_rollback.py::test_startup_interrupted_triggers_rollback_like_any_other_exception`
to reflect that `StartupInterrupted` is handled by a dedicated `except StartupInterrupted`
branch (added by the sibling `startup.py` procedure) rather than the generic
`except Exception` block. Assertion is unchanged (`REQ-007`).

## Scope

- **In-Scope**:
  - Update the docstring/comment of
    `test_startup_interrupted_triggers_rollback_like_any_other_exception` in
    `tests/agent/test_startup_rollback.py` (lines 242-254) to describe the dedicated
    branch.
- **Out-of-Scope**:
  - Changing the `shutdown_all.assert_awaited_once()` assertion.
  - Any other test or source change.

## Assumptions

- **ASM-001**: The sibling `startup.py` procedure adds an `except StartupInterrupted`
  branch before `except Exception as setup_err:`; the interrupt now flows through that
  dedicated branch, but `shutdown_all()` is still awaited exactly once.

## Design decisions

- Only the comment/docstring changes; the test's behavior and assertions are locked and
  must not change. This is a documentation-only correction to keep the test's narrative
  accurate.

## Alternatives considered

- Leaving the stale "no dedicated branch" comment: rejected — it contradicts the new code
  and misleads future readers.

## Implementation

### Target file

`tests/agent/test_startup_rollback.py`

### Procedure

1. Edit the docstring of `test_startup_interrupted_triggers_rollback_like_any_other_exception`
   (currently: *"StartupInterrupted must flow through run()'s existing rollback
   `except Exception as setup_err:` block unchanged — no dedicated branch."*) to state that
   it flows through the dedicated `except StartupInterrupted` rollback branch added by the
   `startup.py` procedure, and re-raises.

### Method

Replace the existing docstring text:

```python
        """StartupInterrupted must flow through run()'s existing rollback
        `except Exception as setup_err:` block unchanged — no dedicated branch."""
```

with:

```python
        """StartupInterrupted flows through run()'s dedicated
        `except StartupInterrupted` rollback branch (added by the startup.py
        rebase), which calls lifecycle.shutdown_all() and re-raises; the
        generic `except Exception` no longer matches it."""
```

Leave the body (the `pytest.raises(StartupInterrupted)` and
`shutdown_all.assert_awaited_once()`) untouched.

## Compatibility considerations

None. This is a test-docstring correction only.

## Security considerations

N/A.

## Rollback considerations

Revert the docstring edit — a single logical commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_startup_rollback.py` | Behavior: interrupt still rolls back once | `pytest` | AC-004 |

## Completion criteria

- The docstring references the dedicated `except StartupInterrupted` branch (not the generic
  handler).
- `test_startup_interrupted_triggers_rollback_like_any_other_exception` passes with
  `shutdown_all.assert_awaited_once()`.

## Out of Scope

Any source change; other tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261022-095438 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261022-095438 | N/A: assertion unchanged, no new test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261022-095438 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261022-095438 | N/A: no docs map to this test |

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
- **Requirement ID**: REQ-007
- **Source issue**: `issues/20261021-220332_star002_make-startupinterrupted-distinguishable-from-ordinary-runtimeerror-in-broad-startup-handlers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261021-232426_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-072226
- **Related target files**: `tests/agent/test_startup_rollback.py`