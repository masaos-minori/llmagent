## Goal
Remove the orchestrator's self-feed call: `self._state_store.recover_stale_attempts(self._state_store.get_connection())` becomes the no-argument facade call `self._state_store.recover_stale_attempts()` (HEAD L92). This is the clearest bypass in the issue: the store's own connection fed back into its own method during startup.

## Scope
**Release unit**: wfaudit015-full (the no-argument call only compiles after document 01's re-signature; the suite validates at unit end).

**Plan row implemented**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md` Implementation Target Files row 3 (`scripts/agent/orchestrator.py`, `REQ-003`; plan step 2).

**In scope**:
- The single call-site edit at the startup recovery line (HEAD L92).

**Out of scope**:
- Any `get_connection()` use that `implementations/20261108-134201_03_scripts_agent_orchestrator.py.md` (wfaudit001) adds — its `purge_finished_workflow_events(self._state_store.get_connection())` line lands before this procedure and stays a production `get_connection()` user, deliberately unconverted (`UNK-01`).
- `close()` and component initialization (wfaudit006 `155554_02` region, disjoint).

**Dependencies (landing order)**: document 01 (re-signature) same unit; `134201_03` and `155554_02` land before this edit (plan Notes reconciliation). The edit anchors on the recovery call statement, not a line number.

## Assumptions
| ID | Assumption | Validation |
|---|---|---|
| A-001 | The recovery call is the only `get_connection()` use in `orchestrator.py` at HEAD (verified at `ad48bfa28`: exactly one match, L92). | Verified (grep) |
| A-002 | After `134201_03` lands, a second `get_connection()` match (its purge call) exists in this file; this procedure does not touch it. | Plan Notes / REQ-003 scoping |

## Design decisions
| ID | Decision | Rationale |
|---|---|---|
| D-001 | Convert only the recovery call; leave the wfaudit001 purge call alone. | The purge site is another plan's designed boundary (its procedure passes the connection explicitly); silently converting it would change that plan's contract. Carried in `UNK-01`. |
| D-002 | Anchor the edit on the statement `self._state_store.recover_stale_attempts(self._state_store.get_connection())`. | `134201_03` inserts lines adjacent to it; a line-number edit would drift. |

## Alternatives considered
| Alternative | Reason rejected |
|---|---|
| Convert the purge call too | Out of this plan's frozen scope and contradicts `134201_03`'s design; would exceed REQ-003's audited site list. |
| Move recovery out of `__init__` | Startup-timing change; unrelated to the routing fix and risks init-order regressions. |

## Implementation
### Target file
`scripts/agent/orchestrator.py` (plan target row 3).

### Procedure
Step 1: replace the recovery call statement.

### Method
Symbol-anchored single-statement edit (HEAD `ad48bfa28` L92 is the reference point).

### Details
Step 1 — replace:
```python
        self._state_store.recover_stale_attempts(self._state_store.get_connection())
```
with:
```python
        self._state_store.recover_stale_attempts()
```
Keep its position directly after `self._state_store = StateStore()`. Do not modify any `get_connection()` statement belonging to the wfaudit001 purge call if it is present at execution time.

## Compatibility considerations
- Callers of `Orchestrator.__init__` are unaffected (constructor signature unchanged).
- The startup recovery behavior (counts, `last_recovery_report`) is identical; only argument plumbing disappears.

## Security considerations
Removes the third production `get_connection()` user from this plan's audit scope (REQ-003); the remaining purge site is explicitly tracked in `UNK-01`.

## Rollback considerations
Revert with the wfaudit015-full unit. No data or schema impact.

## Validation plan
Run after the whole unit (documents 01-08) has landed:
| Gate | Command | Expectation |
|---|---|---|
| Orchestrator suite | `uv run pytest tests/agent/test_orchestrator.py -q` | all green incl. document 08 startup routing test |
| Audit | `grep -n "recover_stale_attempts(.*get_connection" scripts/agent/orchestrator.py` | no matches |
| Lint | `uv run ruff check scripts/agent/orchestrator.py` | clean |
| Type check | `uv run pyright scripts/agent/orchestrator.py` | clean |

## Completion criteria
- Startup recovery runs through the no-argument facade call (REQ-002/REQ-003).
- No converted-site `get_connection()` match remains on the recovery line; the wfaudit001 purge match, if present, is untouched (REQ-003 scoping, `UNK-01`).

## Out of Scope
- The facade re-signature itself (document 01).
- Routing test (document 08).
- The wfaudit001 purge call site.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the startup recovery call with the no-argument facade call | Completed | 20261109 | 20261109 | L92 now `recover_stale_attempts()`; covered by orchestrator routing test |
| 2 | Run the unit validation gates (valid only after documents 01-08 land) | Completed | 20261109 | 20261109 | End-of-unit suite: 4220 passed, 3 skipped, 0 failures |

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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: `issues/20261107-203228_wfaudit015_state-store-facade-bypass.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-175155
- **Related target files**: `scripts/agent/orchestrator.py`

<!-- tools/generate_workitem.py implementation-procedure timestamp: 20261108-175155 -->
