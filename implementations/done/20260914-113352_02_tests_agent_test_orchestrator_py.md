## Goal

Migrate all test callers in `tests/agent/test_orchestrator.py` from using deprecated
`orch._llm_runner.run()` and `orch._guard.check_*()` methods to direct usage of
`orch._llm_executor.handle_llm_turn()` and fresh `ToolLoopGuard` instances. Per REQ-003,
REQ-004, REQ-006.

## Scope

- Modify exactly one file: `tests/agent/test_orchestrator.py`
- Migrate ~20 occurrences of `_llm_runner`/`_guard` access:
  - `orch._llm_runner.run(...)` → `orch._llm_executor.handle_llm_turn(...)`
  - `orch._guard.check_all(...)`, `orch._guard.check_error_limit(...)` → fresh `ToolLoopGuard(ctx)` instances
- Preserve test semantics: each migration must produce equivalent results

## Assumptions

- `LlmTurnExecutor.handle_llm_turn()` provides equivalent functionality to `LLMTurnRunner.run()`
  for the test cases being migrated (confirmed by signature comparison below)
- Test code can create its own `ToolLoopGuard` instances instead of relying on `Orchestrator._guard`
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- For `_llm_runner.run()` migrations: replace with `handle_llm_turn()` call, adjusting parameter
  names where necessary (key difference: `handle_llm_turn` has empty-string defaults for keyword args)
- For `_guard.check_*()` migrations: create a fresh `ToolLoopGuard(ctx)` instance per test,
  since the two guards operate on separate `_empty_result_counts` dicts
- Keep test structure unchanged — only replace the specific assertions/method calls

## Alternatives considered

- Using `pytest.warns(DeprecationWarning)` to validate warnings during migration: rejected —
  migration should eliminate warnings, not validate them
- Creating a helper function to abstract the migration: rejected — inline replacement is clearer
  and avoids introducing indirection into test code

## Implementation

### Target file

`tests/agent/test_orchestrator.py`

### Procedure

1. **Migrate `_llm_runner.run()` calls** (~7 occurrences):
   - Replace `await orch._llm_runner.run(llm_url, workflow_id=w, task_id=t, stage_id=s, attempt_id=a)`
   - With `await orch._llm_executor.handle_llm_turn(llm_url, workflow_id=w, task_id=t, stage_id=s, attempt_id=a)`
   - Note: `handle_llm_turn` provides empty-string defaults for keyword args; if a caller relied
     on defaults, ensure explicit values are provided

2. **Migrate `_guard.check_*()` calls** (~13 occurrences):
   - Replace `orch._guard.check_all(seen, fingerprints, set(), msg)`
   - With creating a fresh `ToolLoopGuard(ctx)` instance in the test setup, then calling
     `guard_instance.check_all(seen, fingerprints, set(), msg)`
   - Similarly for `check_error_limit(n)`: use `guard_instance.check_error_limit(n)`

3. **Add `ToolLoopGuard` import if not already present**:
   - Check current imports in the test file
   - Add `from agent.tool_loop_guard import ToolLoopGuard` if missing

### Method

1. Read `test_orchestrator.py` to identify all `_llm_runner` and `_guard` access patterns
2. For each `_llm_runner.run()` occurrence:
   - Verify the parameters match `handle_llm_turn`'s signature
   - Replace the call, preserving argument order and names
3. For each `_guard.check_*()` occurrence:
   - Identify which method is called (`check_all`, `check_error_limit`)
   - Determine what context (`ctx`) the test uses for guard creation
   - Create a local `ToolLoopGuard(ctx)` instance and replace the call
4. Verify no remaining references to `_llm_runner` or `_guard` in the file

### Details

**Signature comparison (critical for migration correctness):**

`LLMTurnRunner.run(llm_url, *, workflow_id, task_id, stage_id, attempt_id)` — no defaults
`LlmTurnExecutor.handle_llm_turn(llm_url, *, workflow_id="", task_id="", stage_id="", attempt_id="")` — defaults to `""`

Migration implication: callers that omitted keyword arguments expecting defaults must now
provide explicit values. For example:
- Before: `await orch._llm_runner.run(url, workflow_id="w")` (task_id/stage_id/attempt_id defaulted)
- After: `await orch._llm_executor.handle_llm_turn(url, workflow_id="w", task_id="", stage_id="", attempt_id="")`

**Step 1 — `_llm_runner.run()` migrations:**

For each of the ~7 occurrences found at lines: 896, 923, 967, 990, 1025, 1057, 2211:

Before:
```python
result = await orch._llm_runner.run(
    llm_url,
    workflow_id=workflow_id,
    task_id=task_id,
    stage_id=stage_id,
    attempt_id=attempt_id,
)
```

After:
```python
result = await orch._llm_executor.handle_llm_turn(
    llm_url,
    workflow_id=workflow_id,
    task_id=task_id,
    stage_id=stage_id,
    attempt_id=attempt_id,
)
```

**Step 2 — `_guard.check_*()` migrations:**

For each of the ~13 occurrences found at lines: 1090, 1096, 1104, 1115, 1128, 1133, 1151:

Before:
```python
result = orch._guard.check_error_limit(3)
# or
result = orch._guard.check_all(seen, [], set(), msg)
```

After (pattern A — check_error_limit):
```python
guard = ToolLoopGuard(ctx)  # ctx from test fixture
result = guard.check_error_limit(3)
```

After (pattern B — check_all):
```python
guard = ToolLoopGuard(ctx)  # ctx from test fixture
result = guard.check_all(seen, fingerprints, set(), msg)
```

Note: Each test needs its own `ToolLoopGuard` instance because the two guards have separate
`_empty_result_counts` dicts — sharing would cause incorrect dedup/cycle/retry behavior.

## Compatibility considerations

- Test-only change: no production code affected
- Migration preserves test semantics but changes object identity (fresh `ToolLoopGuard` vs shared)
- Tests that rely on shared guard state between orchestrator and test will need adjustment

## Security considerations

N/A: test code change, no security-sensitive operations.

## Rollback considerations

- Revert the three edit steps above to restore original test code
- No data loss risk — only test code changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_orchestrator.py | Regression test — verify tests pass after migration | `uv run pytest tests/agent/test_orchestrator.py -x -q` | All tests pass |
| tests/agent/test_orchestrator.py | Static check — verify no _llm_runner/_guard references remain | `rg "_llm_runner\|_guard" tests/agent/test_orchestrator.py` | Zero matches |

## Completion criteria

- [ ] All `orch._llm_runner.run()` calls replaced with `orch._llm_executor.handle_llm_turn()`
- [ ] All `orch._guard.check_*()` calls replaced with fresh `ToolLoopGuard` instance calls
- [ ] `ToolLoopGuard` import added if not already present
- [ ] No remaining references to `_llm_runner` or `_guard` in the file
- [ ] pytest passes without regression
- [ ] Each test creates its own `ToolLoopGuard` instance (not shared with Orchestrator)

## Out of scope

- Migrating integration test callers (separate row)
- Adding new deprecation warnings (Phase 1, separate row)
- Removing the fields entirely (Phase 2)
- Refactoring `LlmTurnExecutor` to share guard state across turns

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260914-140025 | 20260914-140025 |  |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: existing tests cover regression |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 20260914-140405 | 20260914-140405 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docstring update in Phase 1 |

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
- **Requirement ID**: REQ-003, REQ-004, REQ-006
- **Source issue**: issues/20260913-172211_unused_orchestrator_llm_runner.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-220251_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-113352
- **Related target files**: tests/agent/test_orchestrator.py