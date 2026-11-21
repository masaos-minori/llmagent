## Goal

Derive valid production keys from dataclass fields only, so the RAG section disappears from the derivation and the DB/maintenance keys stop being hand-added (REQ-006, AC-001), and keep the refiner-key rule reachable by calling its check from `validate()` (AC-006).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 4)

## Assumptions
- `tests/agent/test_production_config_validator.py` is this row's companion: it is named by this row only, so it has no document of its own and is carried here. It gains the refiner-key case moved from `tests/agent/test_config_builders.py` (Plan row 22).
- `agent` may import `db` per `.importlinter`, so deriving keys from the dataclasses in `scripts/db/` does not break the import-layer contract.

## Design decisions
- The refiner-key check moves here from `_build_rag_config()` (Plan row 2): the check function itself is not modified, only its call site. Keeping the message as a named rule is preferable to letting the keys fail as unknown keys, because the message states where the refiner is configured (ADR-002) and AC-006 keeps the old location rejected.
- The hand-added blocks are removed only for keys that a dataclass actually defines: the `db` maintenance and path keys come from the typed maintenance configuration and `DbConfig` as defined by Plan rows 8-9, and the `AgentConfig`-level keys come from `AgentConfig` itself added to the derivation loop.
- Justified exceptions stay: `system_prompt_tool` (read directly by `build_agent_config()`) and `diagnostics` (a nested-table section name, not a field). Each kept exception keeps its existing comment explaining why it cannot be derived.

## Alternatives considered
- Keep the DB keys hand-added: rejected by AC-001, which requires derivation for keys that belong to dataclass sections.
- Derive the `diagnostics` name from `DiagnosticsConfig`: rejected — the name is the table section, not a field of any dataclass.

## Implementation
### Target file
`scripts/agent/production_config_validator.py`
### Procedure
- Remove `RAGConfig` from the import list (line 154) and from the derivation list (line 161).
- Replace the hand-added `db` key block (lines 192-213) with derivation from the `db` dataclasses as they exist after Plan rows 8-9 land.
- Add `AgentConfig` to the derivation list and delete the hand-added lines for `agent_memory_max_startup_snippets` and `pending_timeout_minutes` (lines 174, 180).
- Keep `system_prompt_tool` and `diagnostics` as documented exceptions.
- Call `check_agent_refiner_keys()` from `validate()` and add its returned strings to `errors`. This is the call site the Plan does not name; the owner chose this resolver on 2026-11-21, because once `_build_rag_config()` is gone this is the only surviving path that can see the top-level refiner keys, and it is the path that keeps the asserted message instead of a generic unknown-key error.
### Method
- Field introspection through `dataclass_fields()` is reused as-is; only the classes it is called on change.
- `memory_embed_url` (new) needs no special handling: it becomes a `MemoryConfig` field and is derived automatically.
### Details
- Verified 2026-11-21: `_get_valid_production_keys()` is cached in `_VALID_PRODUCTION_KEYS`, so the derivation must stay deterministic at import time and must not execute at module import of `db` classes that could fail; keep the existing lazy-import style inside the function.
- AC-006 depends on this row: the old key location `embed_url` must be rejected as an unknown key rather than read as an alias.

### Companion test files
- `tests/agent/test_production_config_validator.py`
  - Procedure: Add the parametrized refiner-key case moved from `tests/agent/test_config_builders.py`, asserting `validate({key: 1})` returns the `config/rag_pipeline_mcp_server.toml` message for `use_refiner`, `refiner_max_tokens`, `refiner_timeout`, `refiner_max_chars_per_chunk`; the existing `assert "refiner_max_tokens" not in keys` derivation test stays, since the key is no longer accepted by derivation and is rejected by the named rule instead.
  - Validation: `uv run pytest tests/agent/test_production_config_validator.py -v`

## Compatibility considerations
- The validator runs before assembly in `build_agent_config()`; deriving from `db` dataclasses must not introduce a circular import (`db` never imports `agent`).

## Security considerations
- N/A: no trust-boundary change; the check surface is unchanged apart from key ownership.

## Rollback considerations
- N/A: revert the commit (Phase 4 is not part of a release unit).

## Validation plan
- `uv run pytest tests/agent/test_production_config_validator.py -v`
- `uv run ruff check scripts/agent/production_config_validator.py`, `uv run mypy scripts/agent/production_config_validator.py`
- `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria
- Every accepted key is either derived from a dataclass field or carries a written justification for being an exception; `RAGConfig` is not referenced anywhere in this module; a config that carries a refiner key is rejected with the existing `config/rag_pipeline_mcp_server.toml` message through `validate()`.

## Out of Scope
- The dataclass definitions (Plan row 1), the `db` typed configuration definitions (Plan rows 8-9), documentation updates (Plan rows 27-31).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | Add the refiner-key case to the companion test file named in Implementation > Companion test files. Gated: same - the derived-key surface must be re-verified after that Issue lands |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - shared derivation surface must be re-verified after that Issue lands |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: same - documentation rows are separate procedure documents |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006 (valid keys are derived, not hand-added)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/agent/production_config_validator.py`, `tests/agent/test_production_config_validator.py`
