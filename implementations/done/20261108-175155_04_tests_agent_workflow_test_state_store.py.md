## Goal
Retarget all 12 `store.recover_stale_attempts(store.get_connection())` call sites in `tests/agent/workflow/test_state_store.py` to no-argument calls so the suite matches the new facade signature while every asserted behavior stays identical.

## Scope
**Release unit**: wfaudit015-full (the no-argument signature in document 01 breaks these sites if they are not retargeted in the same unit).

**Plan row implemented**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md` Implementation Target Files row 4 (`tests/agent/workflow/test_state_store.py`, `REQ-002`/`REQ-005`; plan step 2).

**In scope**:
- Mechanical argument removal at every `recover_stale_attempts` call site in this file (12 at HEAD `ad48bfa28`: L122, L136, L150, L167, L181, L182, L192, L201, L208, L217, L227, L250).

**Out of scope**:
- Any assertion, fixture, or test-name change. The lease-based takeover behaviors these tests lock (REQ-006/AC-4 semantics) are regression locks, not targets.

**Dependencies (landing order)**: `implementations/20261108-170505_04_tests_agent_workflow_test_state_store.py.md` (wfaudit009) retargets land first and may add further `recover_stale_attempts` call sites with connection arguments (valid at their landing time). This procedure converts every call site present at execution time, pattern-anchored, including those additions.

## Assumptions
| ID | Assumption | Validation |
|---|---|---|
| A-001 | Every call site in this file passes the store's own connection (`store.get_connection()`), so argument removal preserves behavior exactly. | Verified (12/12 at `ad48bfa28`) |
| A-002 | No test here asserts the signature itself (no `TypeError` expectations on missing argument). | Verified (file read) |

## Design decisions
| ID | Decision | Rationale |
|---|---|---|
| D-001 | Pattern-anchored bulk rewrite of the exact call pattern, not per-line edits. | The pattern is unique and mechanical; line numbers drift after wfaudit009 retargets land. |
| D-002 | Keep the `store` fixture and DB fixtures untouched. | The tests exercise real-DB recovery behavior; only the call shape changes. |

## Alternatives considered
| Alternative | Reason rejected |
|---|---|
| Keep the old signature with an optional argument so tests compile unchanged | Defeats REQ-002 (single auditable entry) and leaves the bypass route open. |
| Rewrite tests to call the module-level recovery helper directly | Tests must keep exercising the facade entry point (REQ-005 intent). |

## Implementation
### Target file
`tests/agent/workflow/test_state_store.py` (plan target row 4).

### Procedure
Step 1: replace all occurrences of the call pattern. Step 2: confirm zero remaining argument-carrying sites.

### Method
Pattern replace-all on the exact call text (HEAD reference: 12 occurrences).

### Details
Step 1 — replace every occurrence of:
```python
store.recover_stale_attempts(store.get_connection())
```
with:
```python
store.recover_stale_attempts()
```
If wfaudit009 retargets landed a variant that passes `store._db` instead, convert that variant to `store.recover_stale_attempts()` as well.

Step 2 — verify: `grep -n "recover_stale_attempts(" tests/agent/workflow/test_state_store.py` shows only no-argument calls (plus the docstring mentions, which stay).

## Compatibility considerations
- Pure test-call shape change; all asserted counts (`result == 1`, idempotent second pass `== 0`, lease-live skips) are unchanged, keeping the semantics regression lock (REQ-004/REQ-005).

## Security considerations
N/A (test-only change).

## Rollback considerations
Revert with the wfaudit015-full unit.

## Validation plan
Run after documents 01-08 have landed (unit gate):
| Gate | Command | Expectation |
|---|---|---|
| Recovery suite | `uv run pytest tests/agent/workflow/test_state_store.py -q` | all green, same test count as before |
| Pattern audit | `grep -c "recover_stale_attempts(store.get_connection())" tests/agent/workflow/test_state_store.py` | 0 |
| Lint | `uv run ruff check tests/agent/workflow/test_state_store.py` | clean |

## Completion criteria
- Zero argument-carrying `recover_stale_attempts` calls remain in this file.
- All pre-existing recovery assertions pass unchanged (REQ-002/REQ-005).

## Out of Scope
- The signature change itself (document 01).
- New delegation tests (document 05).
- Other test files (documents 05-06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace all argument-carrying call sites with no-argument calls | Completed | 20261109 | 20261109 | All 12 sites now no-argument; behavior-preserving |
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
- **Requirement ID**: `REQ-002`, `REQ-005`
- **Source issue**: `issues/20261107-203228_wfaudit015_state-store-facade-bypass.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-175155
- **Related target files**: `tests/agent/workflow/test_state_store.py`

<!-- tools/generate_workitem.py implementation-procedure timestamp: 20261108-175155 -->
