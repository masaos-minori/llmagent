## Goal

Retarget the three startup-failure integration-test patches from `type(mgr)._read_stderr_tail` to `mgr._stderr_log_manager.read_tail`, returning `bytes` literals, so they exercise the delegated path after the wrapper is removed. Honors REQ-004.

## Scope

Modify `tests/agent/test_http_lifecycle_integration.py` only. The three patched sites currently stub the removed `_read_stderr_tail` method; they must instead stub `StderrLogManager.read_tail` on the injected dependency. No assertion intent changes. Production code in `scripts/agent/http_lifecycle.py` is out of scope (covered by the first implementation procedure document).

## Assumptions

- `mgr` carries a real `StderrLogManager` instance at `mgr._stderr_log_manager` (injected in `__init__`).
- The inlined production call decodes `read_tail`'s return with `.decode(errors="replace")`, so each mock must return `bytes`, not `str`.
- The three sites are the only patches of `_read_stderr_tail` (confirmed via `rg` across `tests/`).
- Each retargeted test still reaches `_cleanup_server_resources` during its flow, so `read_tail` is actually invoked.

## Design decisions

- Patch the instance attribute `mgr._stderr_log_manager.read_tail` rather than a class-level method, because `read_tail` lives on the dependency object, not on `HttpServerLifecycleManager`.
- Convert each `str` literal to its `bytes` form (`b"<text>"`) so the production `.decode()` call succeeds and the captured text still appears in the raised error.

## Alternatives considered

- Keep patching a class method on `type(mgr)`. Rejected: `_read_stderr_tail` is being deleted; the delegated path goes through `StderrLogManager.read_tail`.
- Return a `str` from the mock and rely on Python duck typing. Rejected: `.decode()` on a `str` raises `AttributeError`, failing the test (this is the exact risk documented in the source plan's Risks section).

## Implementation
### Target file
`tests/agent/test_http_lifecycle_integration.py`

### Procedure
Replace each of the three `patch.object(type(mgr), "_read_stderr_tail", new=MagicMock(return_value="<text>"))` blocks with `patch.object(mgr._stderr_log_manager, "read_tail", new=MagicMock(return_value=b"<text>"))`, converting the `str` literal to `bytes`. Preserve every `assert` unchanged.

### Method
Locate the three sites by their unique return values:
- `"error output here"` — in `test_startup_failure_contains_stderr` (multi-line patch form).
- `"timeout stderr"` — in `test_startup_failure_contains_reason_on_timeout` (multi-line patch form).
- `""` — in `test_health_check_poll_continues_on_error` (single-line patch form).

### Details
Site 1 (`test_startup_failure_contains_stderr`):
```python
            with patch.object(
                type(mgr),
                "_read_stderr_tail",
                new=MagicMock(return_value="error output here"),
            ):
```
->
```python
            with patch.object(
                mgr._stderr_log_manager,
                "read_tail",
                new=MagicMock(return_value=b"error output here"),
            ):
```
Site 2 (`test_startup_failure_contains_reason_on_timeout`): replace `"_read_stderr_tail"` -> `"read_tail"` and `"timeout stderr"` -> `b"timeout stderr"`.
Site 3 (`test_health_check_poll_continues_on_error`, single-line form):
```python
            with patch.object(
                type(mgr), "_read_stderr_tail", new=MagicMock(return_value="")
            ):
```
->
```python
            with patch.object(
                mgr._stderr_log_manager,
                "read_tail",
                new=MagicMock(return_value=b""),
            ):
```
Preserve every `assert` unchanged; the decoded bytes still appear in `failure.stderr_full`. Do not alter any surrounding context manager or fixture.

## Compatibility considerations

- Tests construct a real `HttpServerLifecycleManager` with a real `StderrLogManager`; patching `mgr._stderr_log_manager.read_tail` targets that instance. No signature changes to any method.
- Retargeting is safe once the first implementation procedure document has inlined the delegation into `_cleanup_server_resources`; before that change the old patches would target a method that still exists, but the new target is correct regardless.

## Security considerations

- Test-only change; no secret/injection surface introduced.

## Rollback considerations

- Restore the three original `patch.object(type(mgr), "_read_stderr_tail", ...)` blocks. No data/schema impact.

## Validation plan

- Run the three retargeted tests individually plus the full suite: `uv run pytest tests/agent/test_http_lifecycle_integration.py tests/agent/test_http_lifecycle_stderr_log_manager.py tests/agent/test_lifecycle.py`; expect 127 passed, 3 skipped, 0 failed (T-001 / AC-004).
- Confirm the three sites still assert captured stderr text appears in the raised `HttpStartupError` (T-002 / AC-005).
- Static: `uv run ruff check tests/agent/test_http_lifecycle_integration.py` clean; mypy covers `tests/` (T-003).

## Completion criteria

- All three patches target `StderrLogManager.read_tail` returning `bytes`; assertions unchanged; full suites pass at baseline counts (AC-004, AC-005).

## Out of scope

- Any change to production code in `scripts/agent/http_lifecycle.py` (covered by the first implementation procedure document).
- Adding new tests beyond retargeting the three existing sites.
- Changing any assertion's expected value or intent.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Retargeting replaces existing patches; no new tests added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260930-134555_refactor_001_remove-duplicated-stderr-tail-logic-in-httpserverlifecyclemanager-by-delegating-to-stderrlogmanager.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260930-144038_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260930-154120
- **Related target files**: tests/agent/test_http_lifecycle_integration.py
