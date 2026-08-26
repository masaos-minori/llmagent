## Goal

Add a typed `cleanup_server_resources(server_key: str) -> str` method to
`_ServerLifecycleRouter` (REQ-002: implement the protocol method, delegating to
`self._http_mgr._cleanup_server_resources()`) so `config_reload.py` can call it
directly instead of through `getattr()`.

## Scope

- In scope: `scripts/agent/factory.py` — add `cleanup_server_resources()` to
  `_ServerLifecycleRouter`, a thin delegation to
  `self._http_mgr._cleanup_server_resources(server_key)`.
- In scope (Plan Phase 1 preparation item, folded into this document since it is
  purely investigative and targets this same class): confirm the delegation-method
  pattern already used by `_ServerLifecycleRouter`'s other public methods before
  writing the new method.
- Out of scope (per Plan): any change to
  `HttpServerLifecycleManager._cleanup_server_resources()` itself
  (`scripts/agent/http_lifecycle.py:239-247`) — its internal logic is untouched.
- Out of scope (per Plan): the `LifecycleManagerProtocol` declaration itself (REQ-001,
  covered by the separate `scripts/agent/lifecycle_protocol.py` document) and the
  `config_reload.py` call-site replacement (REQ-003, covered by the separate
  `scripts/agent/services/config_reload.py` document).

## Assumptions

- **CORRECTED**: The `cleanup_server_resources()` method already exists in code. Verified at `factory.py:252-254`: `def cleanup_server_resources(self, server_key: str) -> str:` → `return self._http_mgr._cleanup_server_resources(server_key)`. No further action needed on this implementation procedure.

## Design decisions

- Follow the existing single-line delegation pattern already used by every other
  public method on this class that forwards to `self._http_mgr` — e.g.
  `get_process_snapshot()` (`scripts/agent/factory.py:228-231`):
  ```python
  def get_process_snapshot(self, server_key: str) -> dict | None:
      """Return process snapshot dict for a managed subprocess server, or None."""
      snapshot: dict | None = self._http_mgr.get_process_snapshot(server_key)
      return snapshot
  ```
  `cleanup_server_resources()` follows the same shape: one-line body, delegates to
  `self._http_mgr`, annotated return type matching the delegate's declared type
  (`str`, per `HttpServerLifecycleManager._cleanup_server_resources`).
- No new state, no new imports — the method needs nothing beyond `self._http_mgr`,
  which the class already holds.
- Placed alongside the class's other thin-delegation methods (e.g. immediately after
  `get_process_snapshot()` / `get_process_info()` / `list_processes()`, before
  `get_subprocess_server_configs()`) for readability, matching the class's existing
  grouping of "thin delegation to `_http_mgr`" methods.

## Alternatives considered

- Add a generic `__getattr__` fallback on `_ServerLifecycleRouter` that forwards
  unknown attribute lookups to `self._http_mgr`: rejected — this is exactly the
  dynamic-dispatch pattern the Plan's Reason for change identifies as the root cause
  (bypasses `mypy`/`LifecycleManagerProtocol` structural checking); it would silently
  paper over this bug class instead of fixing it.
- Rename/expose `HttpServerLifecycleManager._cleanup_server_resources()` as a public
  method instead of adding a router-level delegation: rejected — out of scope per
  Plan (this method is a private consolidation artifact from
  `plans/done/20260730-211410_plan.md`, not meant to be a public contract of
  `HttpServerLifecycleManager`).

## Implementation

### Target file

`scripts/agent/factory.py`

### Procedure

1. Confirm (already done during this document's investigation — see Assumptions
   above) that `_ServerLifecycleRouter`'s existing methods which forward to
   `self._http_mgr` all use the same one-line delegation shape; no deviation found
   that would require a different approach for this new method.
2. Add a new method `cleanup_server_resources(self, server_key: str) -> str` to
   `_ServerLifecycleRouter`, placed near the class's other `_http_mgr`-delegating
   methods (after `get_process_snapshot()`/`get_process_info()`/`list_processes()`,
   before `get_subprocess_server_configs()`, i.e. around current line 241-242).
3. Body: `return self._http_mgr._cleanup_server_resources(server_key)` — a single
   statement, no intermediate logic.

### Method

Thin delegation, one new method, zero lines changed in any existing method.

### Details

Current state of the relevant class region (verified at
`scripts/agent/factory.py:228-251`):

```python
    def get_process_snapshot(self, server_key: str) -> dict | None:
        """Return process snapshot dict for a managed subprocess server, or None."""
        snapshot: dict | None = self._http_mgr.get_process_snapshot(server_key)
        return snapshot

    def get_process_info(self, server_key: str) -> ProcessInfoSnapshot | None:
        """Return ProcessInfoSnapshot for a managed subprocess server, or None."""
        info: ProcessInfoSnapshot | None = self._http_mgr.get_process_info(server_key)
        return info

    def list_processes(self) -> list[ProcessInfoSnapshot]:
        """Return list of ProcessInfoSnapshot for all managed subprocess servers."""
        processes: list[ProcessInfoSnapshot] = self._http_mgr.list_processes()
        return processes

    def get_subprocess_server_configs(self) -> list[tuple[str, McpServerConfig]]:
        ...
```

Target state (new method inserted after `list_processes()`, before
`get_subprocess_server_configs()`):

```python
    def list_processes(self) -> list[ProcessInfoSnapshot]:
        """Return list of ProcessInfoSnapshot for all managed subprocess servers."""
        processes: list[ProcessInfoSnapshot] = self._http_mgr.list_processes()
        return processes

    def cleanup_server_resources(self, server_key: str) -> str:
        """Read stderr tail and release tracking resources for a removed server."""
        return self._http_mgr._cleanup_server_resources(server_key)

    def get_subprocess_server_configs(self) -> list[tuple[str, McpServerConfig]]:
        ...
```

Note: this line calls a name-mangled-looking private method
(`_cleanup_server_resources`) on `self._http_mgr` directly by attribute access (not
`getattr()`) — this is intentional and matches the Plan's Implementation intent
(`self._http_mgr._cleanup_server_resources(server_key)`); it is a normal, statically
type-checkable private-method call within the same module's control, not the dynamic
`getattr()` pattern this Plan removes. `HttpServerLifecycleManager` is defined in the
same module (`scripts/agent/factory.py` imports it; the class lives in
`scripts/agent/http_lifecycle.py`) and `_ServerLifecycleRouter` already accesses other
underscore-prefixed attributes of `_http_mgr` nowhere else in this class — this is the
first and only such access, consistent with the Plan's explicit design (Design
section: "薄い委譲メソッドとして実装").

Test addition — `tests/agent/test_agent_factory.py` already has a
`_make_lifecycle_router()` helper (line 515-523) used by
`TestGetSubprocessServerConfigs`; follow the same pattern:

```python
class TestCleanupServerResources:
    """Tests for _ServerLifecycleRouter.cleanup_server_resources()."""

    def test_delegates_to_http_mgr(self) -> None:
        router = _make_lifecycle_router()
        router._http_mgr = MagicMock()
        router._http_mgr._cleanup_server_resources.return_value = "stderr tail"

        result = router.cleanup_server_resources("srv")

        router._http_mgr._cleanup_server_resources.assert_called_once_with("srv")
        assert result == "stderr tail"
```

## Compatibility considerations

- Pure addition — no existing method signature or behavior changes.
- `_ServerLifecycleRouter` is not part of any public/external API (it is an
  internal-module class instantiated only in `scripts/agent/factory.py:307` and
  exposed to the rest of the codebase only through the `LifecycleManagerProtocol`
  type); adding a method cannot break any existing caller.
- Once `scripts/agent/lifecycle_protocol.py`'s `LifecycleManagerProtocol` gains
  `cleanup_server_resources()` (REQ-001, sibling document, seq 02), this class
  satisfies the Protocol's structural check for that method; `mypy` order of
  application across the two files does not matter — the check happens once both
  files are in their final state.

## Security considerations

- N/A: no new security-relevant logic. The returned stderr tail is the same data
  `HttpServerLifecycleManager._cleanup_server_resources()` already produces for its
  existing internal callers (`scripts/agent/http_lifecycle.py:460,489,499`); this
  change only adds a second, external call path to the same existing method, it does
  not change what data is read or how it is exposed.

## Rollback considerations

- Single-file, single-method addition, no state change, no config/schema impact.
  Revert via `git revert` of the implementing commit; no follow-up cleanup needed.
  Reverting this file alone (without also reverting the `lifecycle_protocol.py` and
  `config_reload.py` changes) would leave `config_reload.py`'s new direct call
  (`lifecycle.cleanup_server_resources(...)`) pointing at a method that no longer
  exists — the three documents in this batch (seq 01/02/04) must be applied and, if
  ever reverted, reverted together.

## Validation plan

- `uv run pytest tests/agent/test_agent_factory.py tests/agent/test_lifecycle.py -v` —
  new test(s) green, no regressions in existing `_ServerLifecycleRouter` tests.
- `uv run mypy scripts/agent/` — no new errors (Plan AC-01).
- `uv run pytest` (full suite) — no new failures.

## Completion criteria

- `_ServerLifecycleRouter.cleanup_server_resources(self, server_key: str) -> str`
  exists in `scripts/agent/factory.py`, delegating to
  `self._http_mgr._cleanup_server_resources(server_key)` with no added logic.
- `uv run pytest tests/agent/test_agent_factory.py tests/agent/test_lifecycle.py -v`
  and the full `uv run pytest` suite are green.
- `uv run mypy scripts/agent/` shows no new errors vs. the pre-existing baseline.

## Out of scope

- `HttpServerLifecycleManager._cleanup_server_resources()`'s internal logic (per Plan
  Out-of-Scope).
- `LifecycleManagerProtocol`'s declaration (REQ-001) and `config_reload.py`'s call-site
  change (REQ-003) — covered by the sibling documents
  `implementations/20260826-102143_02_scripts_agent_lifecycle_protocol.py.md` and
  `implementations/20260826-102143_04_scripts_agent_services_config_reload.py.md`.
- Cross-plan awareness (not an action item for this document): two other, already
  processed sibling plans also target `scripts/agent/services/config_reload.py`'s
  `apply_config_dict()` in this same batch —
  `plans/20260825-141157_plan.md` (→
  `implementations/20260826-100937_01_scripts_agent_services_config_reload.py.md`,
  replaces the single `self._reload_approval_settings(ctx, new_cfg)` call at old line
  122 with four calls) and `plans/20260825-141653_plan.md` (→
  `implementations/20260826-101556_01_scripts_agent_services_config_reload.py.md`,
  adds a `gitops_push_blocked` line inside `_reload_approval_config()`, a helper
  defined far below `apply_config_dict()`, around lines 405-429). Neither touches
  `scripts/agent/factory.py`, so this document has no direct overlap with them; the
  file-level cross-reference note belongs on the `config_reload.py` document
  (seq 04) instead, where the same file is genuinely shared by three concurrent
  changes.
- `deploy/deploy.sh` changes — none needed (no file added, removed, or moved;
  `scripts/` is rsynced wholesale per `rules/toolchain.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm `_ServerLifecycleRouter`'s existing `_http_mgr`-delegation pattern (Plan Phase 1) | Completed | 20260826-102143 | 20260826-102143 | Confirmed via `get_process_snapshot()`/`get_process_info()`/`list_processes()` at lines 228-241; no deviation found |
| 2 | Add `cleanup_server_resources()` to `_ServerLifecycleRouter` (REQ-002) | Pending | — | — | |
| 3 | Add unit test in `tests/agent/test_agent_factory.py` (`TestCleanupServerResources`) | Pending | — | — | |
| 4 | Run validation sequence (targeted tests, full suite, mypy) | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (implement `cleanup_server_resources()` on `_ServerLifecycleRouter`)
- **Source issue**: `issues/20260825_cfgreload_lifecycle_cleanup_getattr_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-141919_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-102143
- **Related target files**: `scripts/agent/factory.py`
