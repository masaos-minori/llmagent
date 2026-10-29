# startorch001 dead `_spawned_subprocesses` state in StartupOrchestrator

## Priority
Low

## Summary
`StartupOrchestrator` initializes and mutates an instance attribute
`self._spawned_subprocesses`, but nothing ever reads it. The rollback path in
`run()` calls `lifecycle.shutdown_all()` and never consults this collection, so
the tracked subprocess list is dead state. It documents an assumption about how
rollback works that the code does not actually rely on.

## Background
In `scripts/agent/startup.py`, `StartupOrchestrator.__init__` sets
`self._spawned_subprocesses = []` (line 60). `run()` appends to it after each
component starts (line 73). The `except` handler (lines 94-100) rolls back via
`await lifecycle.shutdown_all()` and does not reference
`self._spawned_subprocesses`.

## Problem
`self._spawned_subprocesses` is written but never read anywhere in the class or
callers. It is therefore:
- dead state that gives the false impression that the orchestrator tracks
  spawned processes for its own rollback;
- a maintenance hazard: if someone later assumes this list drives shutdown, they
  will be wrong — shutdown is driven entirely by `lifecycle.shutdown_all()`.

## Reason for Change
Remove misleading state. Either the field is genuinely needed (in which case it
should be used) or it should be deleted to avoid implying an ownership/rollback
contract that does not exist.

## Implementation Intent
Confirm the field is unused (grep for `_spawned_subprocesses`). If confirmed
unused, delete the attribute declaration in `__init__`, the append in `run()`,
and any comment referencing it. Verify no caller or test depends on it. If there
is a latent reason to track spawned processes (e.g. future targeted shutdown),
file a follow-up rather than reintroducing dead state now.

## Target Files or Areas
- `scripts/agent/startup.py` — `StartupOrchestrator.__init__` (line 60) and `run()` (line 73)

## Required Changes
- Grep the repo for `_spawned_subprocesses` to confirm zero readers.
- If unused: remove the `self._spawned_subprocesses = []` initialization and the
  corresponding append in `run()`. Remove any inline comment that describes the
  tracking.
- If used somewhere not yet found: document why and wire it into rollback
  deterministically (separate issue).

## Constraints
- Do not change the rollback behavior (`lifecycle.shutdown_all()`).
- Do not introduce new state to replace it without a concrete consumer.

## Acceptance Criteria
- `_spawned_subprocesses` no longer appears anywhere in the codebase (if it was
  confirmed unused), OR its usage is wired into rollback if a consumer exists.
- `scripts/agent/startup.py` still imports and runs; startup tests pass.

## Testing Expectations
- `tests/agent/test_startup.py` passes after removal.
- Confirm no test references `_spawned_subprocesses`.

## Documentation Impact
None beyond code comments. No external docs.

## Out of Scope
- Changing how `shutdown_all()` works.
- Adding real process-tracking machinery.

## Dependencies
N/A: none

## Unresolved Questions
- Was `_spawned_subprocesses` intended to drive per-process teardown in a past
  design? A git blame on `startup.py` may clarify intent before deletion.
- Is there any external tooling or test that introspects this attribute by name?

## AI Implementation Instruction
Grep for `_spawned_subprocesses` across the repo. If it has no readers, delete
its declaration in `StartupOrchestrator.__init__` and its append in `run()`, plus
any comment referencing it. Confirm `tests/agent/test_startup.py` still passes.
If a reader exists, do not delete; instead note it as a follow-up.

## Traceability
- **Workflow phase**: `issue-creator` (fed by `python-code-review`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-220719
- **Related target files**: `scripts/agent/startup.py`
