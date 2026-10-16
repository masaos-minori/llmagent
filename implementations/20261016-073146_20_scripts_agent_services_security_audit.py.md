## Goal

Remove the Agent-side security audit API, because each MCP server now validates its own
configuration and the Agent only consumes the published posture (`REQ-017`, `AC-008`).

## Scope

- Delete `scripts/agent/services/security_audit.py` (226 lines). Its only public symbol is
  `audit_security_defaults()`, and every check it performs is either replaced by a per-server
  validator (rows `7`-`16`) or already performed elsewhere in the Agent.
- Removing the two importers is rows `22` (`startup_validation.py:19`) and `24`
  (`repl_health.py:16-18`); this row does not edit them.

## Assumptions

- Current module verified: `_load_audit_config_or_raise()` at
  `scripts/agent/services/security_audit.py:31-37`, `audit_security_defaults()` at `:40-226`. The
  module has no other public symbol, and `scripts/agent/services/__init__.py` is a docstring-only
  package file with no re-export.
- Importers today: `scripts/agent/startup_validation.py:19` (call at `:59-68`) and
  `scripts/agent/repl_health.py:16-18` (re-export at `:45-46`). No production module imports it
  besides those two.
- Every behavior the audit provides has an owner after this Plan:
  - HTTP `auth_token` presence (`:56-70`) is already enforced more broadly by the `mcp_auth` check at
    `scripts/agent/startup_validation.py:71-81`, which checks every configured MCP server, not only
    HTTP ones with a URL.
  - `ProductionConfigValidator().validate` (`:142-153`) is independently run at config build time by
    `_run_production_validation()` (`scripts/agent/config_builders.py:375-393`), whose canonical suite
    is `tests/agent/test_production_config_validator.py`. Only the audit-side call is removed.
  - shell `sandbox_backend == "none"` hard failure (`:89-91`), non-firejail warning (`:92-99`), and
    missing firejail binary hard failure (`:103-108`) move to shell-mcp's own validator (row `7`).
  - DENY-ALL warnings for `shell.command_allowlist` (`:109-117`), `git.allowed_repo_paths`
    (`:163-171`), `github.allowed_repos` (`:174-182`), `cicd.workflow_allowlist` (`:187-195`) move to
    the corresponding server validators (rows `7`, `8`, `9`, `10`).
  - GitHub `allow_force_push` / `require_pr_review` warnings (`:204-212`) move to row `9` as
    `WARNING`-status checks, which keep them non-fatal.
  - The "Security posture summary" line (`:214-224`) is replaced by the posture itself.
- `security_lockdown_enabled` (`:75-80`) is the suppression flag that turns DENY-ALL warnings off.
  Plan `UNK-02` records that whether the setting stays in `config/agent.toml` is unresolved; **no
  suppression may be re-added** in the new validators.

## Design decisions

- Delete the file rather than leave an empty module: after removing the two functions, nothing remains
  except imports, a `TypeVar`, and a logger, and an empty module would keep a name in the package that
  implies a capability that no longer exists.
- The Plan's frozen table lists this row's action as `Modify`; the correct action is `Delete`. The Plan
  row is amended to `Delete` before this procedure is executed, so the table stays the contract.
- Removal is a pure deletion: no shim, no deprecation wrapper, no re-export. A shim would keep the
  cross-config read `REQ-017` removes, because the audit's mechanism is loading other servers' config
  files through `agent/security_audit_config.py` (row `21`).
- The `ProductionConfigValidator` call is deleted, not relocated: `_run_production_validation()`
  already validates the same four fields (`tool_definitions_strict`, `routing_drift_strict`,
  `tool_safety_tiers`, `allowed_tools`) with the same `known_tools` input, and it fails with
  `ConfigReloadValidationError` at config build time, which is earlier and stricter than the audit's
  `RuntimeError` at `:154-155`.
- The `known_tools` resolution through `shared.tool_registry.get_registry()` (`:127-138`) disappears
  with the module. `config_builders.py` resolves `known_tools` for its own call, so no capability is
  lost.

## Alternatives considered

- Keep the module as a thin wrapper that only calls `ProductionConfigValidator` — rejected: that
  duplicates `_run_production_validation()` and keeps a second, weaker failure path for the same
  settings.
- Keep the audit as an "Agent-side second opinion" during Phase 1/2 — rejected: `REQ-017` removes the
  cross-config read, and the audit's value depends entirely on reading other servers' config files.
  Row `05` (`shared/security/shadow_validation.py`) is the sanctioned temporary comparison tool, and it
  is explicitly time-boxed.
- Convert the audit into a posture consumer instead of deleting it — rejected: that is row `17` plus
  row `18`, and keeping both would create two places that decide whether a server is acceptable.

## Implementation
### Target file

`scripts/agent/services/security_audit.py` (delete)

### Procedure

1. Confirm no remaining importer: `grep -rn "services.security_audit\|audit_security_defaults\|_load_audit_config_or_raise" scripts/ tests/`
   returns only rows `22`, `24`, `26`, and `31` targets.
2. Delete the file.
3. Do not delete `scripts/agent/production_config_validator.py`, `scripts/agent/config_builders.py`,
   or `scripts/agent/security_audit_config.py` in this row (row `21` owns the loader module).

### Method

- Delete in the same commit as rows `22` and `24`, or after them, so the tree never contains a dangling
  import. If the rows land separately, land `22` and `24` first.
- No code is moved into this module. Any check that appears to lose coverage is traced to its new row
  in the Assumptions list above before the deletion is accepted.

### Details

- The module's `logger` (`:28`) and `T = TypeVar("T")` (`:26`) exist only to serve the two removed
  functions.
- `TransportType` (`:15`) and the four `load_*_audit_config` imports (`:19-24`) disappear with the
  module; `shared.mcp_config.TransportType` is still used elsewhere and is not affected.
- `scripts/agent/startup.py:107` carries a docstring mention of the audit step; it is a comment-only
  touch point listed in the Plan's follow-up list, not a code dependency.

## Compatibility considerations

- Removing the module breaks `tests/agent/test_audit_security_failures.py` (row `26`),
  `tests/agent/test_security_audit_config_isolation.py` (row `27`),
  `tests/agent/test_config_permission_cross_server.py` (row `28`),
  `tests/agent/test_failure_handling_policy_cross_cutting.py` (row `29`), and the audit cases in
  `tests/agent/test_startup.py` (row `30`). Those rows must land with this one; a module-level import
  of a deleted module fails at collection time, not at test time.
- The `security_audit` pipeline source disappears from `StartupValidationResult`, which is row `22`'s
  job; `startup_reporter.py:75` and `:83` then report a source that no longer exists, which row `23`
  removes.
- No `docs/*.md` change is in scope for this row; `docs/10_adr/adr_02_014_agent-control-plane-responsibility-boundaries.md`
  (row `41`) and `docs/23_agent/*` are follow-ups.

## Security considerations

- `REQ-017` / Plan `INV-06`: the Agent stops reading MCP server config files, which is what makes the
  `agent-mcp-config-models` import-linter exception removable (row `25`).
- Deletion is only safe because every removed check has a named owner. If any check lacks an owner at
  execution time, this row must stop and report rather than delete.
- The audit's fail-closed behaviors (hard `RuntimeError` on `sandbox_backend=none`, missing firejail,
  missing auth token) must not be weakened by the move; rows `7`-`10` and the existing `mcp_auth` check
  carry them.

## Rollback considerations

- Restore the file with `git checkout` and re-apply rows `22`, `24`, `25` reversals. Because row `25`
  removes the import-linter exception that this module's config loading depended on, a rollback of this
  row alone would fail `lint-imports` unless row `25` is also reverted.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No importer remains | `grep -rn "audit_security_defaults" scripts/ tests/` | no matches in `scripts/` |
| Startup pipeline integrity | `uv run pytest tests/agent/test_startup.py tests/agent/shared/test_startup_validation_pipeline.py` | passes with the `security_audit` source absent |
| Production validation unaffected | `uv run pytest tests/agent/test_production_config_validator.py` | passes unchanged |
| Config-build validation unaffected | `uv run pytest tests/agent/test_config_builders.py` | passes unchanged |
| Import contract | `PYTHONPATH=scripts uv run lint-imports` | passes with the module gone |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/` | clean, no unused-import findings |

## Completion criteria

- Plan `AC-008`: `audit_security_defaults` and `_load_audit_config_or_raise` no longer exist, and no
  Agent module reads an MCP server config file.
- Each removed check is traceable to a named replacement row or to an existing check
  (`mcp_auth`, `_run_production_validation`).
- `tests/agent/test_production_config_validator.py` and `tests/agent/test_config_builders.py` are
  untouched and still pass.

## Out of scope

- Editing `startup_validation.py` (row `22`), `repl_health.py` (row `24`), `startup_reporter.py`
  (row `23`), `security_audit_config.py` (row `21`), or any test file (rows `26`-`35`).
- Deciding `security_lockdown_enabled`'s future (Plan `UNK-02`).
- `docs/*.md` updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Amend the Plan row action from `Modify` to `Delete` | Pending | — | — | required before execution |
| 2 | Confirm no remaining importer | Pending | — | — | gate for deletion |
| 3 | Delete `scripts/agent/services/security_audit.py` | Pending | — | — | land with rows `22`, `24` |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-017` (remove Agent-side cross-config audit)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/agent/services/security_audit.py`
