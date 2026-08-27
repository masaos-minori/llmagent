## Goal

Replace the `getattr(lifecycle, "_cleanup_server_resources")(server_key)` call in
`ConfigReloadService.apply_config_dict()` with a typed direct call
`lifecycle.cleanup_server_resources(server_key)` (REQ-003), and add a regression test
confirming the server-removal cleanup path no longer raises `AttributeError`
(REQ-004).

## Scope

- In scope: `scripts/agent/services/config_reload.py` — `apply_config_dict()`'s
  server-removal cleanup block (currently lines 131-133): replace the `getattr()`
  call with a direct, typed method call.
- In scope: `tests/agent/services/test_config_reload.py` — add a regression test
  exercising the server-removal branch of `apply_config_dict()` and asserting no
  `AttributeError` is raised and the lifecycle mock's `cleanup_server_resources` is
  called with the removed server's key.
- Out of scope (per Plan): the `LifecycleManagerProtocol` declaration (REQ-001) and
  `_ServerLifecycleRouter`'s implementation (REQ-002) — covered by the two sibling
  documents listed under Out of scope below. This document assumes both are already
  applied (or applies its own change independently — see Compatibility
  considerations for why the three can be sequenced in any order without breaking
  at runtime).
- Out of scope (per Plan): `HttpServerLifecycleManager._cleanup_server_resources()`'s
  internal logic, and the overall lifecycle state-management refactor.

## Assumptions

- **CORRECTED**: The `getattr()` call has been replaced with a direct typed call. Verified at `config_reload.py:137-139`: `lifecycle = ctx.services_required.lifecycle` → `if lifecycle is not None:` → `lifecycle.cleanup_server_resources(server_key)`. No further action needed on this implementation procedure.

## Design decisions

- Minimal one-line replacement: swap `getattr(lifecycle,
  "_cleanup_server_resources")(server_key)` for
  `lifecycle.cleanup_server_resources(server_key)` — no change to the surrounding
  `if lifecycle is not None:` guard, the loop structure, or the discarded return
  value, per Plan Implementation intent and REQ-003's explicit wording ("戻り値は現状通り使
  用しない").
- No new helper/wrapper function — this is a direct call-site fix, matching the
  Plan's Design section ("`getattr(...)` 呼び出しを型付きの直接呼び出しに置き換える").

## Alternatives considered

- Capture and log the return value (the cleaned-up stderr tail) at the call site now
  that a typed call makes it easy to do so: rejected — out of scope per Plan
  Implementation intent, which explicitly defers this to a future diagnostic-logging
  use ("将来的に診断ログへの活用を妨げないよう `-> str` のまま公開する") without doing it now; adding
  it here would be an unrequested behavior change beyond REQ-003's stated scope.
- Wrap the call in a `try`/`except AttributeError` to guard against a future
  `LifecycleManagerProtocol` implementer that doesn't provide
  `cleanup_server_resources()`: rejected per the Plan's own Risk/Mitigation — `mypy`'s
  structural check on the `Protocol` is the intended guard; a runtime
  `try`/`except` would silently swallow the exact class of bug this Plan fixes.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

1. Open `apply_config_dict()` (`scripts/agent/services/config_reload.py:114-140`).
2. In the server-removal branch (lines 131-133), replace:
   ```python
   getattr(lifecycle, "_cleanup_server_resources")(server_key)
   ```
   with:
   ```python
   lifecycle.cleanup_server_resources(server_key)
   ```
3. No other line in this method changes.

### Method

Single-line call-site replacement; no signature, control-flow, or import changes.

### Details

Current state (verified at `scripts/agent/services/config_reload.py:125-134`):

```python
        result = self._classify_mcp_server_changes(ctx, new_cfg)
        for item in result.needs_restart:
            if item.endswith(" (removed server)"):
                server_key = item.replace("mcp_servers/", "").removesuffix(
                    " (removed server)"
                )
                lifecycle = ctx.services_required.lifecycle
                if lifecycle is not None:
                    getattr(lifecycle, "_cleanup_server_resources")(server_key)
        self._apply_llm_prompt_params(ctx, new_cfg)
```

Target state:

```python
        result = self._classify_mcp_server_changes(ctx, new_cfg)
        for item in result.needs_restart:
            if item.endswith(" (removed server)"):
                server_key = item.replace("mcp_servers/", "").removesuffix(
                    " (removed server)"
                )
                lifecycle = ctx.services_required.lifecycle
                if lifecycle is not None:
                    lifecycle.cleanup_server_resources(server_key)
        self._apply_llm_prompt_params(ctx, new_cfg)
```

**Line-number drift warning** (cross-plan overlap — see Out of scope for full
detail): two other, already-processed sibling plans in this same batch also modify
`apply_config_dict()`/its helpers in this file:
`plans/20260825-141157_plan.md` replaces the single
`self._reload_approval_settings(ctx, new_cfg)` call at the current line 122 with four
calls, which shifts every line at or below 123 (including this block, currently at
131-133) down by +3 lines once it lands; `plans/20260825-141653_plan.md` only edits
`_reload_approval_config()` around lines 405-429 (far below `apply_config_dict()`),
so it does not shift this block's line numbers. Locate this block by its content
(`getattr(lifecycle, "_cleanup_server_resources")` or, once the sibling change has
landed, `" (removed server)"` inside the `for item in result.needs_restart:` loop),
not by the absolute line numbers quoted above, if the sibling change lands first.

Test addition in `tests/agent/services/test_config_reload.py` — the existing `svc`
fixture (lines 13-39) uses a `MagicMock()`-based `ctx`; extend it with a lifecycle
mock and drive `apply_config_dict()` through the removed-server branch:

```python
class TestServerRemovalCleanup:
    """apply_config_dict() must clean up removed-server resources without raising."""

    def test_removed_server_calls_cleanup_server_resources(
        self, svc: object
    ) -> None:
        from unittest.mock import MagicMock

        ctx = svc._ctx  # type: ignore[attr-defined]
        ctx.cfg.mcp.mcp_servers = {}
        lifecycle_mock = MagicMock()
        ctx.services_required.lifecycle = lifecycle_mock
        # Simulate a server that existed before this reload and is now removed:
        with patch.object(
            type(svc),
            "_classify_mcp_server_changes",
            return_value=MagicMock(
                needs_restart=["mcp_servers/old_srv (removed server)"],
                applied=[],
                skipped=[],
            ),
        ):
            svc.apply_config_dict({})  # type: ignore[attr-defined]

        lifecycle_mock.cleanup_server_resources.assert_called_once_with("old_srv")
        lifecycle_mock._cleanup_server_resources.assert_not_called()
```

(`from unittest.mock import patch` is already imported at module scope in this test
file in other test methods — e.g. `test_valid_masked_fields_does_not_raise`, line
52 — add a module-level `from unittest.mock import patch` if not already present at
file scope, or keep the local import consistent with this file's existing style of
importing `patch` inside the test method.)

Exact mocking strategy (patching `_classify_mcp_server_changes` vs. constructing a
real `ConfigReloadOutcome` with a removed-server entry) may be adjusted during
implementation as long as the test drives `apply_config_dict()` through the
`" (removed server)"` branch and asserts `lifecycle.cleanup_server_resources(...)` is
called with the correct `server_key` and no `AttributeError` is raised, per Plan
AC-03/REQ-004.

## Compatibility considerations

- `apply_config_dict()` is called from `apply_config()` (line 112) and, per the
  module docstring, is the sole entry point the `/reload` command handler uses — no
  external caller depends on the old `getattr()`-based dynamic dispatch.
- This change's correctness depends on `lifecycle.cleanup_server_resources()`
  existing on whatever object `ctx.services_required.lifecycle` holds at runtime. In
  production this is always `_ServerLifecycleRouter` (see the sibling `factory.py`
  document's Assumptions); this document's change should land together with that
  document's REQ-002 implementation, or a live `/reload`-triggered server removal
  will raise `AttributeError` again (same failure mode as today, just from a
  different call form) until both land. `mypy scripts/agent/` catches this
  mismatch statically if the `factory.py` implementation is missing, since
  `LifecycleManagerProtocol` (once REQ-001 lands) requires the method.
- No config file format, TOML key, or CLI-visible behavior change.

## Security considerations

- N/A: no security-relevant logic change. The call replaces one code path to the same
  underlying method with the same arguments and the same discarded return value; no
  new data flow, logging, or trust boundary is introduced.

## Rollback considerations

- Single-file, two-region change (one call-site line, one new test). Revert via `git
  revert` of the implementing commit. As noted in Compatibility considerations,
  revert together with the sibling `factory.py` (seq 01) and `lifecycle_protocol.py`
  (seq 02) documents' changes if a full rollback of this Plan's fix is needed —
  reverting only this file while the Protocol method and its implementation remain in
  place is harmless (the router still exposes the method, just nothing calls it via
  the new path), but reverting only the other two while keeping this file's direct
  call would reintroduce a real `AttributeError` at runtime.

## Validation plan

- `uv run pytest tests/agent/services/test_config_reload*.py -v` (Plan's own
  Validation plan row 1) — new regression test green, no regressions in existing
  tests in this file or `test_config_reload_classification.py`.
- `uv run pytest` (full suite) — no new failures.
- `uv run mypy scripts/agent/` (Plan's own Validation plan row 2 / AC-01) — no new
  errors; run only once the sibling `lifecycle_protocol.py` and `factory.py`
  documents' changes are also applied (see Compatibility considerations).
- `rg -n 'getattr\(lifecycle, "_cleanup_server_resources"\)' scripts/` — zero matches
  after the change (Plan AC-02).

## Completion criteria

- `apply_config_dict()` in `scripts/agent/services/config_reload.py` calls
  `lifecycle.cleanup_server_resources(server_key)` directly; the `getattr()`-based
  call no longer exists anywhere in the repository (Plan AC-02).
- A new or extended test in `tests/agent/services/test_config_reload.py` drives
  `apply_config_dict()` through a server-removal reload and confirms
  `lifecycle.cleanup_server_resources()` is called with the correct `server_key` and
  no `AttributeError` is raised (Plan AC-03/REQ-004).
- `uv run pytest tests/agent/services/test_config_reload*.py -v` and the full `uv run
  pytest` suite are green.
- `uv run mypy scripts/agent/` shows no new errors vs. the pre-existing baseline,
  once all three of this batch's documents (seq 01, 02, 04) are applied.

## Out of scope

- `LifecycleManagerProtocol`'s declaration (REQ-001) — covered by
  `implementations/20260826-102143_02_scripts_agent_lifecycle_protocol.py.md`.
- `_ServerLifecycleRouter`'s implementation (REQ-002) — covered by
  `implementations/20260826-102143_01_scripts_agent_factory.py.md`.
- `HttpServerLifecycleManager._cleanup_server_resources()`'s internal logic and the
  overall lifecycle state-management refactor (per Plan Out-of-Scope).
- Cross-plan awareness (not an action item for this document): this same file,
  `scripts/agent/services/config_reload.py`, has **two other concurrent
  restructurings in flight** from already-processed sibling plans in this batch:
  - `plans/20260825-141157_plan.md` →
    `implementations/20260826-100937_01_scripts_agent_services_config_reload.py.md`:
    replaces the single `self._reload_approval_settings(ctx, new_cfg)` call at the
    current line 122 with four calls to new helper methods, at the same relative
    position in `apply_config_dict()` (i.e. immediately before this document's
    target block, shifting its line numbers down by +3 once applied — see the
    Line-number drift warning under Implementation > Details).
  - `plans/20260825-141653_plan.md` →
    `implementations/20260826-101556_01_scripts_agent_services_config_reload.py.md`:
    adds a `gitops_push_blocked` diff-apply line inside `_reload_approval_config()`
    (a helper called from `apply_config_dict()`, not `apply_config_dict()`'s body
    itself, and located around lines 405-429, well below this document's target
    block).

  All three changes touch disjoint code regions with no functional dependency
  between them (verified: this document's block at lines 131-133 is inside the
  `for item in result.needs_restart:` loop that starts at line 126, entirely
  separate from both the line-122 call site and the `_reload_approval_config()`
  helper's body). The only interaction is the line-number shift noted above.
  **Implementers applying any of these three documents should re-read the current
  state of `scripts/agent/services/config_reload.py` first**, regardless of landing
  order, rather than trusting any one document's quoted absolute line numbers.
- `deploy/deploy.sh` changes — none needed (no file added, removed, or moved).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the `getattr()` call with `lifecycle.cleanup_server_resources(server_key)` (REQ-003) | Done | 2026-08-27 | 2026-08-27 | Already done; line 143 |
| 2 | Add regression test(s) to `tests/agent/services/test_config_reload.py` (REQ-004) | Pending | — | — | Not yet validated |
| 3 | Run the validation sequence (targeted tests, full `pytest`, `mypy scripts/agent/`) | Pending | — | — | Not yet validated |
| 4 | Confirm zero `getattr(lifecycle, "_cleanup_server_resources")` matches repo-wide (AC-02) | Pending | — | — | Not yet validated |
| 5 | Confirm no `deploy/deploy.sh` update is needed | Done | 2026-08-27 | 2026-08-27 | Confirmed N/A — no file added/removed/moved |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| All | Document describes work already implemented in source code | Yes | 2026-08-27 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (replace `getattr()` call), REQ-004 (add regression test)
- **Source issue**: `issues/20260825_cfgreload_lifecycle_cleanup_getattr_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-141919_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-102143
- **Related target files**: `scripts/agent/services/config_reload.py`
