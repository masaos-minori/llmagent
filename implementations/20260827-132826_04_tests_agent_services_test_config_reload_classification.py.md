## Goal

Add a regression test confirming `_apply_tool_params()` ignores `tool_cache_ttl` in
`new_cfg` (REQ-003), per `plans/20260825-142436_plan.md`.

## Scope

- In scope: one new test function in this file, mirroring the existing
  `test_detect_startup_only_*` pattern.
- Out of scope: any existing test in this file; `test_config_reload.py` (the
  broader integration-style test file — this Plan's regression test belongs at the
  unit level, matching this file's existing per-method test granularity).

## Assumptions

- `scripts/agent/services/config_reload.py`'s `_apply_tool_params()` has been (or
  is being, in this same pass, seq 03) updated to no longer collect `tool_cache_ttl`
  — this test's assertion depends on that change landing together.
- This file's existing `_make_ctx()` fixture (verified 2026-08-27, lines 15-28) sets
  `ctx.cfg.tool.tool_cache_ttl = 60.0` — this remains valid to keep (it exercises
  the ctx object's shape, not the diff-apply behavior under test) since the new
  test calls `_apply_tool_params()` directly with its own `new_cfg`/`changes`
  arguments, not through the full `ctx`-based reload path.

## Design decisions

- Mirror `test_detect_startup_only_empty_dict`/`test_detect_startup_only_non_startup_keys_ignored`'s
  shape (lines 44-50): call the target method directly with a hand-built `new_cfg`
  dict and an empty `changes` dict, assert on the resulting `changes` dict — rather
  than exercising the full `apply_config_dict()` reload path, which is already
  covered by `test_config_reload.py`'s broader integration tests.

## Alternatives considered

- Testing via the full `ConfigReloadService.apply_config_dict()` path (integration
  style) was considered and rejected — this file's own docstring/existing pattern
  favors direct unit tests of individual `_apply_*`/`_detect_*` methods; a direct
  call to `_apply_tool_params()` is simpler and more targeted.

## Implementation
### Target file
`tests/agent/services/test_config_reload_classification.py`

### Procedure
1. Add a new test function `test_apply_tool_params_ignores_tool_cache_ttl`,
   calling `svc._apply_tool_params(ctx.cfg, {"tool_cache_ttl": 999.0}, {})` and
   asserting the returned/mutated `changes` dict does not contain `"tool_cache_ttl"`.
2. Run `uv run pytest tests/agent/services/test_config_reload_classification.py -v`
   (will fail until seq 03, `config_reload.py`, is also applied — or pass if this
   item lands after that change).

### Method
Direct file addition (Edit tool) — one new test function; no changes to existing
tests or the shared `_make_ctx()`/`svc` fixtures.

### Details
`_apply_tool_params()`'s current signature (verified 2026-08-27,
`config_reload.py:398-400`): `_apply_tool_params(self, cfg: AgentConfig, new_cfg:
dict[str, Any], changes: dict[str, Any]) -> None` — it mutates `changes` in place
and returns `None`. Example shape (adjust to match this file's exact fixture
access pattern — verify `svc`/`ctx` fixture names and scope before finalizing):
```python
def test_apply_tool_params_ignores_tool_cache_ttl(
    svc: ConfigReloadService, ctx: MagicMock
) -> None:
    changes: dict[str, object] = {}
    svc._apply_tool_params(ctx.cfg, {"tool_cache_ttl": 999.0}, changes)
    assert "tool_cache_ttl" not in changes
```
Also verify the three still-collected fields remain unaffected with a second
assertion or a follow-up case, e.g. confirming `serial_tool_calls` is still
collected when present in `new_cfg`, to prove the removal was scoped correctly
(not an accidental removal of the whole method's behavior):
```python
def test_apply_tool_params_still_collects_serial_tool_calls(
    svc: ConfigReloadService, ctx: MagicMock
) -> None:
    changes: dict[str, object] = {}
    svc._apply_tool_params(ctx.cfg, {"serial_tool_calls": True}, changes)
    assert changes["serial_tool_calls"] is True
```

## Compatibility considerations

- Test-only change; no production code path is affected.
- Depends on seq 03 (`config_reload.py`) landing in the same change for the first
  assertion to pass.

## Security considerations

- N/A: test-only change, no security-relevant code path.

## Rollback considerations

- New-function-only revert via `git diff`/`git checkout -- <path>`; independent of
  other tests in this file.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/services/test_config_reload_classification.py` | Unit | `uv run pytest tests/agent/services/test_config_reload_classification.py -v` | New test(s) pass once seq 03 has also landed; existing `_detect_startup_only_*` tests remain unaffected |

## Completion criteria

- A test confirms `_apply_tool_params()` does not add `tool_cache_ttl` to `changes`
  even when present in `new_cfg`.
- A test confirms the three other fields (`serial_tool_calls` at minimum) are still
  collected correctly, proving the removal was scoped to only `tool_cache_ttl`.

## Out of scope

- `test_config_reload.py` (broader integration-style tests).
- Any existing test in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_apply_tool_params_ignores_tool_cache_ttl` | Pending | — | — | |
| 2 | Add `test_apply_tool_params_still_collects_serial_tool_calls` (scope-boundary guard) | Pending | — | — | |
| 3 | Run `uv run pytest tests/agent/services/test_config_reload_classification.py -v` | Pending | — | — | Requires seq 03 applied first |

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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/done/20260825_cfgreload_toolexecutor_cache_wiring_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142436_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-132826
- **Related target files**: `tests/agent/services/test_config_reload_classification.py`
