## Goal

Create the `scripts/shared/security/` package that hosts the common Security Validation
platform shared by every MCP server and the Agent (`REQ-001` common result DTO, `REQ-002`
posture contract, `REQ-003` common startup flow).

## Scope

- One new directory `scripts/shared/security/` and one new `__init__.py`.
- No behavior, no re-exports. The DTO, contract, flow, and shadow harness are separate
  `Implementation Target Files` rows (`02`, `03`, `04`, `05`).

## Assumptions

- `scripts/shared/` is the leaf layer importable by both `agent` and `mcp_servers`
  (`.importlinter:19-28` `shared-is-leaf`, `.importlinter:49-55` `mcp_servers-no-agent`).
- Verified against current source: `scripts/shared/security/` does **not** exist; this row
  creates it. The Plan's earlier "empty package already prepared" claim was corrected in the
  Plan's `Assumptions` during Step 3a.

## Design decisions

- `__init__.py` carries a docstring only and imports nothing: re-exporting submodule symbols
  here would make every consumer import the whole platform eagerly and would couple the DTO
  row to the contract row.
- No new `.importlinter` contract is needed: `shared` is already the `source_modules` entry of
  `shared-is-leaf`, so `shared.security` is covered by the existing leaf rule.

## Alternatives considered

- Host the platform in `scripts/agent/shared/` — rejected: `mcp_servers` may not import `agent`
  (`.importlinter:49-55`), so servers could not consume it.
- Host it in `scripts/mcp_servers/` — rejected: the Agent may not import MCP server modules once
  the `agent-mcp-config-models` exception is removed (`REQ-017`).

## Implementation
### Target file

`scripts/shared/security/__init__.py` (new)

### Procedure

1. Create the directory `scripts/shared/security/`.
2. Create `__init__.py` containing only a module docstring that names the platform and its
   three members (`result_dto` (new), `posture_contract` (new), `startup_flow` (new), plus
   `shadow_validation` (new)) — each is created by rows `02`-`05`.

### Method

- Plain package marker; no `__all__`, no `__init__` subclassing, no lazy-import machinery.
- Submodules are imported by their full dotted path by consumers.

### Details

- Docstring first line follows the repository convention used by other shared modules
  (for example `scripts/shared/config_errors.py`): the module path, then one sentence of purpose.
- Keep the file under 15 lines.

## Compatibility considerations

- New package under `scripts/shared/`; `deploy.sh` already rsyncs `scripts/shared/`, so no
  deployment change is required.

## Security considerations

- N/A: no logic in this file. The non-secret constraint is enforced in rows `02` and `03`.

## Rollback considerations

- Revert the commit; the directory is unused by any other module until rows `02`-`05` land.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Package compiles | `uv run python -m compileall -q scripts/` | no errors |
| Importable from both layers | `PYTHONPATH=scripts uv run python -c "import shared.security"` | exit 0 |
| Architecture boundary | `PYTHONPATH=scripts uv run lint-imports` | `shared-is-leaf` still keeps |

## Completion criteria

- `shared.security` imports successfully from an `agent`-side and an `mcp_servers`-side context.
- `lint-imports` reports no new violation.

## Out of scope

- The DTO, contract schema, startup flow, and shadow harness (rows `02`-`05`).
- Any `docs/*.md` update; ADR alignment is rows `36`-`41`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `scripts/shared/security/` and its `__init__.py` | Completed | 20261016-163649 | 20261016-164740 | stale_detector reported new_target_dir_missing (this row creates the package directory); directory created before re-running the check per user approval. submodule names marked (new) in Procedure step 2 |
| 2 | Add the import smoke test named in Validation plan | Completed | 20261016-164740 | 20261016-164740 | executed as the Validation plan import smoke checks (PYTHONPATH=scripts python -c 'import shared.security'); no new test file created: no frozen Plan row names one for this target |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-164740 | 20261016-164740 | ruff/bandit/mypy(417 files, clean)/lint-imports(6 kept)/compileall pass; full suite: 8443 passed, 19 skipped, 9 pre-existing failures in tests/agent/test_startup_rollback.py (workflow schema 1.1.0 vs 1.0.0), confirmed unrelated by re-running with the new package removed N/A: no docs/00_index.md task-scope mapping for scripts/shared/security/__init__.py |

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
- **Requirement ID**: `REQ-001` (common Security Validation result DTO — package home)
- **Source issue**: `issues/done/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/shared/security/__init__.py`