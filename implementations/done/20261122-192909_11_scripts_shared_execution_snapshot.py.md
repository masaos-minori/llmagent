## Goal

Make the snapshot's dedup component read only Agent-side config, dropping the direct `mcp_dedup.toml` fallback read (REQ-003, REQ-004).

## Scope
**Release unit**: dedup-config-isolation-core (shared-store config isolation, store-identity gate, and operational reference removal)

## Assumptions
- After seq 23 deletes the shared file, no snapshot path may touch it (AC-003 grep gate).

## Design decisions
- `_dedup_component` (lines 145-156 today call `load_dedup_config(cfg_dir / "mcp_dedup.toml")`) reads the store identity at the dedup database directory contract path (`shared.mcp_dedup_config.dedup_db_dir() / "mcp_dedup.sqlite"`, `LLMAGENT_DB_DIR`-overridable), not from a per-file TOML read. Correction (adversarial verification 2026-11-22): the "Agent config mapping" source named in the first draft does not exist — `agent.toml` carries no dedup db-path key (`_DB_PATH_KEYS` holds only rag/session/workflow), so the contract constant + env override is the only discovery-free source that keeps the emitted shape unchanged.
- No config-loading or discovery import of the dedup config module remains in this shared snapshot builder (the deferred imports are read-only identity + contract path).

## Alternatives considered
- Passing a `DedupStoreConfig` through the snapshot API: rejected — snapshot builders are shared-leaf and must not depend on dispatcher store types for display metadata.

## Implementation
### Target file
`scripts/shared/execution_snapshot.py`
### Procedure
1. Replace the `load_dedup_config(cfg_dir / "mcp_dedup.toml")` call (line ~154) with `read_store_identity(dedup_db_dir() / "mcp_dedup.sqlite")` (deferred imports of `shared.mcp_dedup.read_store_identity` and `shared.mcp_dedup_config.dedup_db_dir`); drop the `cfg_dir` parameter from `_dedup_component` and its now-unused imports.
### Method
Keep the emitted snapshot shape identical — only the value source changes.
### Details
- Module is 8,097 B: no size concern.

### Companion test files
- `tests/shared/test_execution_snapshot.py`
  - Procedure: remove fixtures that write `mcp_dedup.toml` and assert the Agent-side source instead.
  - Validation: `uv run pytest tests/shared/test_execution_snapshot.py -q`.

## Compatibility considerations
- Snapshot payload fields keep identical values for unconfigured deployments (same defaults).

## Security considerations
- N/A: read-path change only; no new key material or paths.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/shared/test_execution_snapshot.py -q`; `uv run mypy scripts/shared/execution_snapshot.py`; `rg 'mcp_dedup' scripts/shared/execution_snapshot.py` empty (AC-003).

## Completion criteria
- The module contains no `mcp_dedup.toml` or dedup-loader reference; snapshot values unchanged by default.

## Out of Scope
- Store schema and dedup runtime behavior (untouched).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the read-source switch | Completed | 2026-11-22 | 2026-11-22—contract-path read; tests retargeted to LLMAGENT_DB_DIR|
| 2 | Add or update companion tests per Validation plan | Completed | 2026-11-22 | 2026-11-22—contract-path read; tests retargeted to LLMAGENT_DB_DIR|
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22—contract-path read; tests retargeted to LLMAGENT_DB_DIR|

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
- **Requirement ID**: REQ-003, REQ-004; AC-003
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `scripts/shared/execution_snapshot.py`, `tests/shared/test_execution_snapshot.py`
