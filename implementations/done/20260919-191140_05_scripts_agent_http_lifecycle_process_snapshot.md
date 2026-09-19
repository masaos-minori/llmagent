## Goal

Decide fate of `ProcessSnapshotProvider` — delete as dead code since no callers exist anywhere in `scripts/` or `tests/`.

## Scope

- **In-Scope**: Deleting `ProcessSnapshotProvider` as dead code after confirming zero external callers
- **Out-of-Scope**: Wiring up `ProcessSnapshotProvider` to a real caller (separate issue per UNK-01), changes to other lifecycle modules

## Assumptions

- `ProcessSnapshotProvider` is fully wired-in but unused — instantiated in `HttpServerLifecycleManager.__init__`, but `self._snapshot_provider` is never read by any method
- Its public methods (`get_info()`, `get_snapshot()`, `list_processes()`) have no callers in `scripts/` or `tests/`
- The entire 544-line module is dead code

## Design decisions

- Delete `ProcessSnapshotProvider` as dead code — no callers exist, and wiring it up requires a separate product/architecture decision (UNK-01)
- Remove all references to `_snapshot_provider` from `HttpServerLifecycleManager.__init__`

## Alternatives considered

- Wiring up `ProcessSnapshotProvider` to an actual caller (e.g., adding a `get_deep_process_snapshot()` method for diagnostics) — rejected because this requires a product/architecture decision that is out of scope for this plan

## Implementation

### Target file

scripts/agent/http_lifecycle_process_snapshot.py

### Procedure

Delete `ProcessSnapshotProvider` as dead code after confirming zero external callers.

### Method

#### Step 1: Verify no external callers

Search for `_snapshot_provider.` across the entire codebase. Confirm zero matches.

#### Step 2: Delete ProcessSnapshotProvider

Delete the file `scripts/agent/http_lifecycle_process_snapshot.py` entirely. This removes ~544 lines of dead code.

#### Step 3: Remove _snapshot_provider reference

Remove the instantiation of `ProcessSnapshotProvider` from `HttpServerLifecycleManager.__init__`:

```python
# Before:
self._snapshot_provider = ProcessSnapshotProvider(ctx)

# After: remove this line entirely
```

### Details

Deletion command:
```bash
rm scripts/agent/http_lifecycle_process_snapshot.py
```

Removal from HttpServerLifecycleManager.__init__:
```python
# Remove these lines:
# self._snapshot_provider = ProcessSnapshotProvider(ctx)
# from agent.http_lifecycle_process_snapshot import ProcessSnapshotProvider
```

## Compatibility considerations

- Public API unchanged — `ProcessSnapshotProvider` was never part of the public API
- Removing `_snapshot_provider` from `HttpServerLifecycleManager` is internal only
- Any future need for deep `/proc` introspection will require re-introducing the module

## Security considerations

- No security-relevant behavior changes — removing dead code reduces attack surface

## Rollback considerations

- If deletion breaks something we missed, restore the file from git history
- Keep a backup copy before deletion

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| ProcessSnapshotProvider deletion | Verification: confirm no callers exist | `rg -n "_snapshot_provider\." scripts/ tests/` | Zero matches |
| Full test suite | Regression — all http_lifecycle tests | `uv run pytest tests/agent/ -q --ignore=tests/integration/` | All tests pass |
| Type checking | Static analysis | `uv run mypy scripts/agent/http_lifecycle*.py` | Clean |
| Linting | Style check | `uv run ruff check scripts/agent/http_lifecycle*.py` | Clean |

## Completion criteria

- `ProcessSnapshotProvider` deleted from codebase
- All references to `_snapshot_provider` removed from `HttpServerLifecycleManager`
- All existing tests pass without modification
- No behavioral regression — same inputs produce same outputs
- Type checker passes on modified files
- Linter passes on modified files

## Out of scope

- Wiring up `ProcessSnapshotProvider` to a real caller (separate issue per UNK-01)
- Deciding whether `ProcessTerminator.terminate_with_timeout()` should return boolean (UNK-02)
- Changes to other lifecycle modules

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
- **Requirement ID**: REQ-009
- **Source issue**: issues/20260919-115306_refactor_002_consolidate_remaining_http_lifecycle_duplication_and_dead_code.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-120000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-191140
- **Related target files**: scripts/agent/http_lifecycle_process_snapshot.py
