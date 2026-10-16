## Goal

Remove the audit re-exports from the `repl_health` compatibility shim, so the shim stops exposing the
deleted audit API (`REQ-017`, `AC-008`).

## Scope

- One modified module `scripts/agent/repl_health.py`: delete the `agent.services.security_audit` import
  block and the two `__all__` entries it feeds.
- The other re-exports (`mcp_health`, `routing_drift`, `tool_validation`, `workflow_schema`) stay.

## Assumptions

- Current module verified: `scripts/agent/repl_health.py` (47 lines) — docstring at `:1-3`
  ("Backward-compatibility re-exports for repl_health consumers."), `from agent.services.security_audit
  import (_load_audit_config_or_raise, audit_security_defaults)` at `:16-19`, `__all__` at `:32-46` with
  `"_load_audit_config_or_raise"` at `:45` and `"audit_security_defaults"` at `:46`.
- The module has **no importer anywhere**: `grep -rn "agent\.repl_health" scripts/ tests/ tools/` matches
  only a docstring in `scripts/agent/services/workflow_schema.py:5`. No test imports it and no test
  patches a `agent.repl_health.*` target.
- `scripts/agent/repl_health.py` is coverage-excluded at `pyproject.toml:153` and is listed in
  `tools/check_suppression_justification.py` `DEFAULT_ALLOWLIST` (the file currently contains no
  suppression comment, so the allowlist entry is inert).
- `tools/check_compat_shims.py` `COMPAT_PATTERNS` includes
  `backward[ _]compatibility\s+(?:layer|stub|re-export)`. The current docstring uses a hyphen
  ("Backward-compatibility re-exports") and does not match. Rewriting it as "backward compatibility
  re-export" would match and fail that check.
- `docs/22_mcp/mcp_02_02_startup-modes-and-health.md:147` lists `repl_health` as a keyword. It is a
  keyword list entry, not a code dependency.
- The audit consumers of these names are `tests/agent/test_repl_health.py:16-21` (audit DTOs) and `:27`
  (`audit_security_defaults`), with the audit test class at `:377-500+`; that file is row `31`.

## Design decisions

- Follow the Plan row and keep the module, removing only the two audit names. The Plan's frozen table
  assigns this row a `Modify` action, and the module still re-exports three other service groups.
- Record the verified finding that the module has zero importers today. **Needs confirmation**: whether
  the project wants the whole shim deleted in a follow-up row, which would also require deleting
  `pyproject.toml:153`'s coverage-omit entry, the inert `check_suppression_justification.py` allowlist
  entry, and the stale keyword at `docs/22_mcp/mcp_02_02_startup-modes-and-health.md:147`. Deleting it
  is out of scope for this row because it is unrelated to `REQ-017`.
- Keep the docstring wording unchanged. It already avoids the `check_compat_shims.py` pattern by using a
  hyphen, and rewording it would introduce a CI failure for no benefit.
- No replacement re-export is added for posture functions. Row `17` (`agent/services/posture_validator.py`)
  and row `18` (`agent/services/mcp_health.py`) are imported directly by their consumers; adding posture
  names to a compatibility shim would create a second import path for new code.

## Alternatives considered

- Delete the whole module — rejected for this row: it is a larger change than `REQ-017` requires, and the
  shim's other re-exports are not this Plan's subject. Recorded as a follow-up with its three cleanup
  sites listed above.
- Keep the audit names in `__all__` but drop the import — rejected: `__all__` entries that do not resolve
  raise `AttributeError` on `from agent.repl_health import *` and fail `ruff`'s undefined-name check.
- Re-export `check_readiness` under a new name to signal posture validation — rejected: `check_readiness`
  is already re-exported at `:9` and `:34`, and renaming would break nothing while adding a name nobody
  imports.

## Implementation
### Target file

`scripts/agent/repl_health.py` (modify)

### Procedure

1. Delete the import block at `:16-19`.
2. Delete `"_load_audit_config_or_raise"` (`:45`) and `"audit_security_defaults"` (`:46`) from `__all__`.
3. Keep the remaining imports (`:7-15`, `:20-30`) and the remaining twelve `__all__` entries unchanged.

### Method

- Land this row together with rows `20`-`22`. A leftover import of a deleted module fails at import time.
- Verify after the edit that `__all__` and the imported names still agree:
  `uv run ruff check scripts/agent/repl_health.py` reports no undefined name and no unused import.

### Details

- The module drops from 47 to about 42 lines, and `__all__` from 14 to 12 entries.
- The module is coverage-excluded, so no coverage threshold is affected by the deletion.

## Compatibility considerations

- `tests/agent/test_repl_health.py` imports the audit names from their source modules, not from
  `agent.repl_health`, so this row does not break it; row `31` removes its audit imports and cases.
- No production module imports `agent.repl_health`, so removing two names cannot break a runtime path.
- No `docs/*.md` change is in scope for this row.

## Security considerations

- Removing the re-exports closes the last Agent-side surface that could reach the audit API, which is
  what makes the import-linter exception removable (row `25`).
- This row adds no capability and no new import path.

## Rollback considerations

- Revert this commit together with rows `20`-`22`. Restoring the import alone fails, because the module
  it imports is deleted by row `20`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Shim imports cleanly | `uv run python -c "import sys; sys.path.insert(0,'scripts'); import agent.repl_health"` | succeeds after rows `20`-`22` land |
| Audit names absent | `grep -n "audit" scripts/agent/repl_health.py` | no matches |
| Compat-shim gate | `uv run python -m tools.check_compat_shims` | passes (docstring wording unchanged) |
| Suppression gate | `uv run python -m tools.check_suppression_justification` | passes |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean, no unused import |

## Completion criteria

- Plan `AC-008` for the shim: `agent.repl_health` no longer imports or exports
  `audit_security_defaults` or `_load_audit_config_or_raise`.
- The other twelve re-exports are unchanged and the module still imports cleanly.
- `tools/check_compat_shims.py` still passes.

## Out of scope

- Deleting `security_audit.py` (row `20`) or `security_audit_config.py` (row `21`).
- Deleting the whole `repl_health` shim (Needs-confirmation follow-up).
- Test updates (row `31`).
- `docs/*.md` updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the audit import block and the two `__all__` entries | Completed | 2026-10-17 | 2026-10-17 | land with rows `20`-`22` |
| 2 | Confirm the whole-shim deletion question with the user | Completed | 2026-10-17 | 2026-10-17 | user decision: shim kept, only the two audit names removed, shim deletion recorded as a follow-up |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-17 | 2026-10-17 | ruff clean, mypy 423 files, lint-imports 6 kept 0 broken, tests/agent 3332 passed with only the 9 known test_startup_rollback failures |

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
- **Related target files**: `scripts/agent/repl_health.py`
