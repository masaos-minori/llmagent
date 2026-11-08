## Goal
Retarget all 8 `store.recover_stale_attempts(store.get_connection())` call sites in `tests/agent/workflow/test_stale_recovery_lease.py` to no-argument calls, keeping every lease-semantics assertion (live-lease skip, compare-and-swap race outcomes) unchanged.

## Scope
**Release unit**: wfaudit015-full (must land with document 01's signature change).

**Plan row implemented**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md` Implementation Target Files row 6 (`tests/agent/workflow/test_stale_recovery_lease.py`, `REQ-002`/`REQ-005`; plan step 2).

**In scope**:
- Mechanical argument removal at every `recover_stale_attempts` call site in this file (8 at HEAD `ad48bfa28`: L143, L168, L169, L196, L233, L260, L279, L299).

**Out of scope**:
- Lease fixture construction, dual-connection race harnesses, and all assertions — this file is the regression lock for REQ-006/AC-4 lease behavior.

**Dependencies (landing order)**: none of the sibling procedures (wfaudit001/007/009) edit this file; it is unique to this plan. Document 01 lands in the same unit.

## Assumptions
| ID | Assumption | Validation |
|---|---|---|
| A-001 | All 8 sites pass `store.get_connection()` (the store's own connection), so removal is behavior-preserving. | Verified (8/8 at `ad48bfa28`) |
| A-002 | The dual-process race tests drive two `StateStore` instances over one DB file and call recovery through each instance; the no-argument form keeps that structure. | Verified (site census: instance-level calls only) |

## Design decisions
| ID | Decision | Rationale |
|---|---|---|
| D-001 | Pattern-anchored replace-all of the single call pattern. | One uniform pattern in this file; line numbers are only reference points. |

## Alternatives considered
| Alternative | Reason rejected |
|---|---|
| Rewrite the race tests to call `_classify_running_attempts` directly | Would bypass the facade entry point the lease guarantees are pinned at (REQ-005). |

## Implementation
### Target file
`tests/agent/workflow/test_stale_recovery_lease.py` (plan target row 6).

### Procedure
Step 1: replace all occurrences of the call pattern. Step 2: confirm zero remaining argument-carrying sites.

### Method
Pattern replace-all on the exact call text (HEAD reference: 8 occurrences, L143/L168/L169/L196/L233/L260/L279/L299).

### Details
Step 1 — replace every occurrence of:
```python
store.recover_stale_attempts(store.get_connection())
```
with:
```python
store.recover_stale_attempts()
```
and the one instance where the receiver is bound to `s` (HEAD L233):
```python
s.recover_stale_attempts(s.get_connection())
```
with:
```python
s.recover_stale_attempts()
```

Step 2 — verify: `grep -n "recover_stale_attempts(" tests/agent/workflow/test_stale_recovery_lease.py` shows only no-argument calls.

## Compatibility considerations
- No assertion or fixture changes; the lease-live skip, stale takeover, and race-loser (`rowcount == 0`) outcomes are asserted exactly as before (REQ-004 regression lock).

## Security considerations
N/A (test-only change).

## Rollback considerations
Revert with the wfaudit015-full unit.

## Validation plan
Run after documents 01-08 have landed (unit gate):
| Gate | Command | Expectation |
|---|---|---|
| Lease suite | `uv run pytest tests/agent/workflow/test_stale_recovery_lease.py -q` | all green, same test count as before |
| Pattern audit | `grep -c "get_connection()" tests/agent/workflow/test_stale_recovery_lease.py` | 0 |
| Lint | `uv run ruff check tests/agent/workflow/test_stale_recovery_lease.py` | clean |

## Completion criteria
- Zero argument-carrying `recover_stale_attempts` calls remain in this file (REQ-002).
- All lease-semantics tests pass unchanged (REQ-005).

## Out of Scope
- The signature change itself (document 01).
- New routing/delegation tests (documents 05, 07-08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace all argument-carrying call sites with no-argument calls | Pending | — | — | |
| 2 | Run the unit validation gates (valid only after documents 01-08 land) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-005`
- **Source issue**: `issues/20261107-203228_wfaudit015_state-store-facade-bypass.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-175155
- **Related target files**: `tests/agent/workflow/test_stale_recovery_lease.py`

<!-- tools/generate_workitem.py implementation-procedure timestamp: 20261108-175155 -->
