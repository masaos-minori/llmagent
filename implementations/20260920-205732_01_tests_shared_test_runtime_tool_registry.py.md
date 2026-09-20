## Goal
Add two regression tests proving `RuntimeToolRegistry.apply_policy()`'s existing
build-then-swap structure (1) leaves `self._tools` untouched when an exception occurs
mid-build, and (2) never exposes a mixed pre-/post-policy state to a concurrent
reader.

## Scope
In scope: two new test functions in `tests/shared/test_runtime_tool_registry.py`
(REQ-001, REQ-002 of `plans/20260920-203342_plan.md`).
Out of scope: modifying `scripts/shared/runtime_tool_registry.py` itself (no
production code change is required — the atomicity already follows from its existing
structure, confirmed by the source Plan's Problem section); modifying any existing
test in this file.

## Assumptions
- This row is independent of Plan1's Row 2 (`implementations/20260920-205403_02_tests_shared_test_runtime_tool_registry.py.md`,
  from the sibling `plans/20260920-203022_plan.md`) — both add tests to the same file
  but to different, non-overlapping test names/scenarios (REQ-001's Plan covers
  `llm_visibility_base`; this Plan covers rollback/concurrency). Implement in either
  order; if both land in the same session, confirm no name collision between the two
  sets of new test functions before finalizing (both documents' Procedure sections
  list distinct function names, confirmed by cross-reading both this document and
  `implementations/20260920-205403_02_tests_shared_test_runtime_tool_registry.py.md`).
- `dataclasses.replace` is imported at module level in
  `scripts/shared/runtime_tool_registry.py` as `dataclasses.replace(...)` (confirmed:
  `import dataclasses` then `dataclasses.replace(...)`, not `from dataclasses import
  replace`) — the rollback test's `unittest.mock.patch` target must therefore be
  `"shared.runtime_tool_registry.dataclasses.replace"`, not
  `"dataclasses.replace"` directly, to intercept only this module's usage.
- A GIL-dependent threading test is accepted as a CPython-specific regression test per
  the source Plan's Unknowns (UNK-02) — document this assumption in the new test's
  docstring per that Unknown's Resolution Path.

## Design decisions
- For the rollback test: use `unittest.mock.patch` to make `dataclasses.replace` raise
  a `ValueError` when called for a specific tool name (e.g. the second of two
  registered tools), so the loop is guaranteed to fail partway through rather than on
  the first or last iteration — this proves the swap statement never executes even
  when some iterations already succeeded.
- For the concurrency test: use a `threading.Event` to synchronize test start (avoid a
  bare `time.sleep`-based race), a background thread that loops calling
  `reg.all_tools()` and records each observed `(agent_safety_tier, enabled_for_llm)`
  tuple set, and the main thread calling `apply_policy()` in a tight loop alternating
  between two known tier/allowlist configurations — then assert every recorded
  snapshot matches one of exactly two known-good state sets (never a third, mixed
  combination).
- Use a high iteration count (thousands) for the concurrency test per the source
  Plan's Risks mitigation — a statistical-power argument, not a timing-precision one.

## Alternatives considered
- Using `pytest-repeat` or a dedicated concurrency-testing library: rejected — adds a
  new dependency for a test achievable with the standard library's `threading` module,
  consistent with `rules/toolchain.md`'s existing tooling and no other test file in
  this repository importing a concurrency-testing library (confirmed via `rg -l
  "pytest-repeat\|hypothesis" tests/` returning no `threading`-adjacent concurrency
  helper usage beyond stdlib).
- Asserting on `id(reg._tools)` transitions instead of value snapshots for the
  concurrency test: rejected as insufficient alone — `test_atomic_single_swap_identity_change`
  already covers the "id changes once" property; this new test needs to prove content
  consistency (no mixed tier/visibility values), which requires snapshotting actual
  tool attribute values, not just the container's identity.

## Implementation
### Target file
`tests/shared/test_runtime_tool_registry.py`

### Procedure
1. Add `import threading` and `from unittest.mock import patch` to the file's imports
   (confirm neither is already present via Read before adding).
2. Add `test_apply_policy_leaves_tools_unchanged_when_build_raises` to the
   `TestApplyPolicy`-equivalent class (after `test_atomic_single_swap_identity_change`,
   confirmed at lines 257-263, to group with the other atomicity-focused tests):
   register two tools, patch `dataclasses.replace` to raise on the second tool's name,
   call `apply_policy()` inside `pytest.raises(ValueError)`, then assert
   `reg.all_tools()` (or `reg.get(name)` for each original tool) still returns the
   exact pre-call `RuntimeTool` objects (same `agent_safety_tier`, same `id()`).
3. Add `test_apply_policy_swap_never_exposes_mixed_state_to_concurrent_reader`
   immediately after it: register a fixed tool set, spawn a background thread that
   loops calling `all_tools()` and recording snapshots into a shared list (guarded by
   a `threading.Lock` or using a thread-safe container), run `apply_policy()` in the
   main thread thousands of times alternating between two known tier/allowlist values,
   join the background thread, and assert every recorded snapshot matches one of the
   two known-good complete states.

### Method
Direct file edit (`Edit` tool) — append two new test functions to an existing test
class; no change to any existing test or fixture helper.

### Details
Existing reference test (confirmed via Read, lines 257-263):
```python
def test_atomic_single_swap_identity_change(self) -> None:
    tool = build_runtime_tool(name="t", server_key="s", enabled_for_llm=True)
    reg = _registry_with(tool)
    old_id = id(reg._tools)
    reg.apply_policy(tier_map={}, allowed_tools=("t",))
    new_id = id(reg._tools)
    assert old_id != new_id
```

New tests to add (illustrative structure — write exact final code during
implementation):
```python
def test_apply_policy_leaves_tools_unchanged_when_build_raises(self) -> None:
    tool_a = build_runtime_tool(name="tool_a", server_key="s", enabled_for_llm=True)
    tool_b = build_runtime_tool(name="tool_b", server_key="s", enabled_for_llm=True)
    reg = _registry_with(tool_a, tool_b)
    original_a = reg.get("tool_a")
    original_b = reg.get("tool_b")

    real_replace = dataclasses.replace

    def _raising_replace(obj: object, **changes: object) -> object:
        if getattr(obj, "name", None) == "tool_b":
            raise ValueError("simulated mid-build failure")
        return real_replace(obj, **changes)  # type: ignore[arg-type]

    with patch(
        "shared.runtime_tool_registry.dataclasses.replace",
        side_effect=_raising_replace,
    ):
        with pytest.raises(ValueError):
            reg.apply_policy(tier_map={}, allowed_tools=())

    assert reg.get("tool_a") is original_a
    assert reg.get("tool_b") is original_b

def test_apply_policy_swap_never_exposes_mixed_state_to_concurrent_reader(
    self,
) -> None:
    """CPython-GIL-dependent regression test: a single self._tools reference swap
    is atomic with respect to concurrent readers under CPython's GIL."""
    tool = build_runtime_tool(
        name="t", server_key="s", agent_safety_tier="READ_ONLY", enabled_for_llm=True
    )
    reg = _registry_with(tool)
    snapshots: list[tuple[str, bool]] = []
    stop = threading.Event()

    def _reader() -> None:
        while not stop.is_set():
            observed = reg.get("t")
            snapshots.append((observed.agent_safety_tier, observed.enabled_for_llm))

    reader = threading.Thread(target=_reader)
    reader.start()
    for i in range(5000):
        if i % 2 == 0:
            reg.apply_policy(tier_map={"t": "ADMIN"}, allowed_tools=("t",))
        else:
            reg.apply_policy(tier_map={"t": "READ_ONLY"}, allowed_tools=("t",))
    stop.set()
    reader.join()

    valid_states = {("ADMIN", True), ("READ_ONLY", True)}
    assert set(snapshots) <= valid_states
```
`import dataclasses` must also be added if not already present (confirm via Read — the
test file currently imports `RuntimeTool`/`build_runtime_tool`/`RuntimeToolRegistry`/
`ToolSpec` and `pytest` only, per the earlier Read of its import block).

## Compatibility considerations
Additive only — no existing test is modified. The threading test spawns and joins its
own thread within the test function; no shared/global state leaks beyond the test's
own scope (`reg` is a locally-constructed `RuntimeToolRegistry`).

## Security considerations
N/A: test-only change, no production code path affected.

## Rollback considerations
Trivially revertable: removing the two new test functions (and the `threading`/`patch`/
`dataclasses` imports if newly added and otherwise unused) leaves every existing test
unaffected.

## Validation plan
- `uv run pytest tests/shared/test_runtime_tool_registry.py -v` — full file, confirming
  the 2 new tests pass and no existing test regresses (REQ-001, REQ-002, AC-1, AC-2,
  AC-3, AC-5 of `plans/20260920-203342_plan.md`).
- Run the concurrency test individually a few times in a loop
  (`uv run pytest tests/shared/test_runtime_tool_registry.py::TestRuntimeToolRegistry::test_apply_policy_swap_never_exposes_mixed_state_to_concurrent_reader
  --count=10` if `pytest-repeat` is available, otherwise a manual shell loop) during
  implementation to build confidence it is not flaky before considering it complete —
  per the source Plan's Risks mitigation.
- `uv run ruff check tests/shared/test_runtime_tool_registry.py` /
  `uv run mypy tests/shared/test_runtime_tool_registry.py`.

## Completion criteria
- `test_apply_policy_leaves_tools_unchanged_when_build_raises` passes, proving AC-1.
- `test_apply_policy_swap_never_exposes_mixed_state_to_concurrent_reader` passes
  consistently across multiple runs, proving AC-2.
- Every pre-existing test in this file still passes unmodified, proving AC-3.

## Out of scope
- Any change to `scripts/shared/runtime_tool_registry.py` — none required.
- Updating `docs/00_governance_03_issue-and-uncertainty-management.md` — covered by
  this Plan's Row 2, a separate implementation procedure document.
- The `llm_visibility_base`-focused tests from the sibling Plan
  (`plans/20260920-203022_plan.md`, Row 2) — distinct scope, distinct document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_apply_policy_leaves_tools_unchanged_when_build_raises` | Pending | — | — | |
| 2 | Add `test_apply_policy_swap_never_exposes_mixed_state_to_concurrent_reader` | Pending | — | — | |
| 3 | Run full test file multiple times to check for flakiness, plus lint/type checks | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002 (rollback-on-exception and concurrent-read consistency regression tests)
- **Source issue**: issues/20260920-191138_req002_make-registry-swap-during-config-reload-atomic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-203342_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-205732
- **Related target files**: tests/shared/test_runtime_tool_registry.py
