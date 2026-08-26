## Goal

Split `ConfigReloadService._reload_approval_settings()` in
`scripts/agent/services/config_reload.py` into four single-concern helpers so each
config domain (approval, tool allowlist, memory runtime, security profile) is reloaded
by a function whose name matches its actual responsibility. Pure refactor — no
behavior change (REQ-001, REQ-002, REQ-003: split responsibilities, wire the new
helpers into `apply_config_dict()`, remove the now-redundant wrapper).

## Scope

- In scope: `scripts/agent/services/config_reload.py` — add
  `_reload_tool_allowlist()`, `_reload_memory_runtime()`, `_reload_security_profile()`;
  update `apply_config_dict()`'s call site; delete `_reload_approval_settings()`.
- Out of scope (per Plan): which fields are hot-reloadable, the field-update logic
  itself (diff-apply pattern via `_get_bool`/`_get_list`/`_get_int`/`_get_str`), and
  `gitops_push_blocked` (tracked separately in
  `issues/20260825_cfgreload_gitops_push_blocked_not_reloadable_issue.md`).
- Out of scope (identified during this document's investigation, not part of this
  item — see Plan Gap note below): adding new `apply_config_dict()`-level
  characterization tests for `allowed_tools` / `memory_retention_days` /
  `memory_local_only` / `security_profile` / `security_lockdown_enabled`. The Plan's
  own Tests section, after adversarial-review correction on 2026-08-25, now flags this
  as a Plan Gap requiring a Plan revision decision — not something this document adds
  on its own initiative.

## Assumptions

- The four helpers keep the exact call order the monolithic function had internally
  (approval → allowed_tools → memory → security), and `apply_config_dict()` keeps
  calling them at the same position (previously line 122) relative to
  `_apply_rag_tool_params()` (before) and `_classify_mcp_server_changes()` /
  `_apply_llm_prompt_params()` / `_apply_sse_reload_params()` / `_sync_services()`
  (after). Verified: none of those five neighboring steps read or write
  `ctx.cfg.approval.*`, `ctx.cfg.tool.allowed_tools`, `ctx.cfg.memory.*`, or
  `ctx.cfg.mcp.security_profile` / `ctx.cfg.mcp.security_lockdown_enabled` — except
  `_sync_services()`, which *reads* `ctx.cfg.tool.allowed_tools` (to pass to
  `runtime_tools.apply_policy()`) after the split helpers have already run, so the
  read-after-write ordering is preserved as long as the four calls stay together at
  the original call site.
- `_reload_approval_settings` has exactly one caller repo-wide
  (`apply_config_dict()` at line 122) — confirmed via
  `rg -n "_reload_approval_settings" scripts/ tests/` (2 matches: the definition at
  line 447 and this one call site). No thin wrapper needs to be kept.

## Design decisions

- Each new helper follows the existing `_reload_approval_config()` signature pattern:
  `(self, ctx: AgentContext, new_cfg: dict[str, Any]) -> None`, matching the
  established style in this class (see `_apply_llm_context_params`,
  `_apply_tool_params`, etc. at lines 225-403).
- Field-update logic is moved verbatim (diff-apply via `_get_bool`/`_get_list`/
  `_get_int`/`_get_str`), including the nested `try`/`import` for
  `security_profile` — no logic rewrite, only a body relocation and a name change.
- `_reload_approval_settings()` is deleted outright rather than kept as a thin
  compatibility wrapper, because it has a single caller and no external contract to
  preserve.

## Alternatives considered

- Keep `_reload_approval_settings()` as a thin wrapper calling the four new helpers:
  rejected — adds an indirection layer with no caller other than
  `apply_config_dict()`, which can call the four helpers directly.
- Merge `_reload_tool_allowlist()` into `_reload_approval_config()` (both are
  "policy-adjacent"): rejected — `allowed_tools` belongs to `ctx.cfg.tool`, not
  `ApprovalConfig`; keeping the split by config-domain ownership (tool / memory / mcp)
  is what REQ-001 asks for and matches the Design section's stated intent.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

1. Add three new private methods immediately after `_reload_approval_config()`
   (currently ending at line 429) and before `_detect_startup_only()`, or immediately
   after the current `_reload_approval_settings()` location (lines 447-469) — either
   placement is acceptable since method order within the class has no behavioral
   effect; keep them adjacent to `_reload_approval_config()` for readability.
2. Move the field-update logic out of `_reload_approval_settings()`'s body into the
   three new methods, unchanged.
3. Delete `_reload_approval_settings()` (lines 447-469) in its entirety.
4. In `apply_config_dict()` (line 114), replace the single line
   `self._reload_approval_settings(ctx, new_cfg)` (line 122) with four lines calling
   `self._reload_approval_config(ctx, new_cfg)`,
   `self._reload_tool_allowlist(ctx, new_cfg)`,
   `self._reload_memory_runtime(ctx, new_cfg)`,
   `self._reload_security_profile(ctx, new_cfg)`, in that order, at the same position
   in the method body.

### Method

Extract by config-domain ownership; no change to any individual field's read/write
logic, only which method contains it.

### Details

Current body of `_reload_approval_settings()` (to be split, verified at
`scripts/agent/services/config_reload.py:447-469`):

```python
def _reload_approval_settings(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> None:
    """Update approval, tool, and memory config fields when present in new_cfg."""
    self._reload_approval_config(ctx, new_cfg)
    if (lst := _get_list(new_cfg, "allowed_tools")) is not None:
        ctx.cfg.tool.allowed_tools = list(lst)
    if (v := _get_int(new_cfg, "memory_retention_days")) is not None:
        ctx.cfg.memory.memory_retention_days = v
    if (vb := _get_bool(new_cfg, "memory_local_only")) is not None:
        ctx.cfg.memory.memory_local_only = vb
    # security.toml fields — hot-reloadable
    if (vs := _get_str(new_cfg, "security_profile")) is not None:
        try:
            from shared.mcp_config import SecurityProfile

            ctx.cfg.mcp.security_profile = SecurityProfile(vs)
        except ValueError:
            pass  # invalid enum value — leave current
    if (vb := _get_bool(new_cfg, "security_lockdown_enabled")) is not None:
        ctx.cfg.mcp.security_lockdown_enabled = vb
```

Target split (all four `_get_*` helpers are already imported at module top,
`config_reload.py:29-44` — no new imports needed except the existing local
`from shared.mcp_config import SecurityProfile` which moves with the security block):

```python
def _reload_tool_allowlist(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> None:
    """Update ctx.cfg.tool.allowed_tools when present in new_cfg."""
    if (lst := _get_list(new_cfg, "allowed_tools")) is not None:
        ctx.cfg.tool.allowed_tools = list(lst)

def _reload_memory_runtime(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> None:
    """Update ctx.cfg.memory fields when present in new_cfg."""
    if (v := _get_int(new_cfg, "memory_retention_days")) is not None:
        ctx.cfg.memory.memory_retention_days = v
    if (vb := _get_bool(new_cfg, "memory_local_only")) is not None:
        ctx.cfg.memory.memory_local_only = vb

def _reload_security_profile(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> None:
    """Update ctx.cfg.mcp security fields when present in new_cfg."""
    # security.toml fields — hot-reloadable
    if (vs := _get_str(new_cfg, "security_profile")) is not None:
        try:
            from shared.mcp_config import SecurityProfile

            ctx.cfg.mcp.security_profile = SecurityProfile(vs)
        except ValueError:
            pass  # invalid enum value — leave current
    if (vb := _get_bool(new_cfg, "security_lockdown_enabled")) is not None:
        ctx.cfg.mcp.security_lockdown_enabled = vb
```

`apply_config_dict()` call-site change (`config_reload.py:114-140`, replacing line
122 only):

```python
# before:
self._reload_approval_settings(ctx, new_cfg)

# after:
self._reload_approval_config(ctx, new_cfg)
self._reload_tool_allowlist(ctx, new_cfg)
self._reload_memory_runtime(ctx, new_cfg)
self._reload_security_profile(ctx, new_cfg)
```

## Compatibility considerations

- `_reload_approval_settings` and the four new/kept methods are all module-private
  (leading underscore); no public API surface changes. Confirmed the only caller is
  `apply_config_dict()` — no other module or test imports
  `_reload_approval_settings` directly (`rg -n "_reload_approval_settings" scripts/
  tests/` → 2 matches total, both inside `config_reload.py` itself).
- No config file format, TOML key, or CLI-visible behavior changes.

## Security considerations

- N/A: no security-relevant logic changes. The `security_profile` /
  `security_lockdown_enabled` field-update logic (including the invalid-enum
  swallow-and-keep-current behavior) is relocated verbatim, not modified.

## Rollback considerations

- Single-file, single-commit change with no data migration or config schema change.
  Revert via `git revert` of the implementing commit; no follow-up cleanup needed
  since no new persistent state, config keys, or external contracts are introduced.

## Validation plan

- `uv run pytest tests/agent/services/test_config_reload*.py tests/agent/commands/test_agent_cmd_config.py -v`
  — must stay green (no new failures). Note: per the Plan's Tests section (as
  corrected 2026-08-25), these two files together cover the approval-field path
  through `apply_config_dict()`, but do **not** exercise `allowed_tools` /
  `memory_retention_days` / `memory_local_only` / `security_profile` /
  `security_lockdown_enabled` through that same path — confirmed via
  `rg` across `tests/` finding zero `apply_config_dict()`/`apply_config()` call sites
  using those four field names. This is a pre-existing coverage gap, not something
  introduced by this refactor; flagged as a Plan Gap for the Plan's Tests section, not
  fixed by this document.
- `uv run pytest` (full suite) — no new failures.
- `uv run mypy scripts/` — no new errors.
- `rg -n "_reload_approval_settings" scripts/ tests/` — zero matches after the change
  (AC-03).
- `rg -n "def _reload_tool_allowlist|def _reload_memory_runtime|def _reload_security_profile" scripts/agent/services/config_reload.py` — three matches (AC-01).

## Completion criteria

- `_reload_tool_allowlist()`, `_reload_memory_runtime()`, `_reload_security_profile()`
  exist in `scripts/agent/services/config_reload.py`, each handling exactly the field
  group described in Details above.
- `apply_config_dict()` calls `_reload_approval_config()` +
  the three new helpers (4 calls total) in place of the old single call, in the same
  relative position and in approval → allowed_tools → memory → security order.
- `_reload_approval_settings` no longer exists anywhere in the repository.
- `uv run pytest tests/agent/services/test_config_reload*.py tests/agent/commands/test_agent_cmd_config.py -v` and the full `uv run pytest` suite are green.
- `uv run mypy scripts/` shows no new errors vs. pre-existing baseline.

## Out of scope

- Changing which fields are hot-reloadable (per Plan Scope).
- Changing the field-update logic itself (diff-apply pattern), beyond relocating it
  verbatim (per Plan Scope).
- Adding `gitops_push_blocked` reload support (tracked in a separate issue per Plan
  Scope).
- Adding new characterization tests for the currently-untested field groups
  (`allowed_tools`, `memory_retention_days`, `memory_local_only`, `security_profile`,
  `security_lockdown_enabled`) through `apply_config_dict()` — reported as a Plan Gap,
  requires a Plan revision decision before it can become an implementation step.
- `deploy/deploy.sh` changes — none needed (no file added/removed/moved).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify the current `_reload_approval_settings()` body and confirm the four field-group boundaries (Plan Phase 1) | Pending | — | — | |
| 2 | Add `_reload_tool_allowlist()`, `_reload_memory_runtime()`, `_reload_security_profile()` (REQ-001) | Pending | — | — | |
| 3 | Replace the `apply_config_dict()` call site with the 4-call sequence (REQ-002) | Pending | — | — | |
| 4 | Delete `_reload_approval_settings()` (REQ-003) | Pending | — | — | |
| 5 | Run validation sequence (`rules/toolchain.md`) — targeted tests, full suite, mypy | Pending | — | — | |
| 6 | Confirm zero `_reload_approval_settings` matches repo-wide (AC-03) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (add 3 new helpers), REQ-002 (rewire `apply_config_dict()`), REQ-003 (delete `_reload_approval_settings()`)
- **Source issue**: `issues/20260825_cfgreload_approval_settings_mixed_concerns_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-141157_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-100937
- **Related target files**: `scripts/agent/services/config_reload.py`
