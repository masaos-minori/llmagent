## Goal

Add the dedup store identity component (store generation + schema fingerprint) to the execution snapshot built by `scripts/shared/execution_snapshot.py` so a dedup-store swap or generation rollover is visible in snapshot comparison (REQ-008, AC-7).

## Scope
**Release unit**: dedup-lease-identity-rollover

## Assumptions
- Row 01 provides the store identity accessors (generation + schema fingerprint) on `DedupStore`; this document only reads them.
- The shared-leaf import contract is respected: `execution_snapshot` imports `shared/mcp_dedup`, not `db` (existing `_DB_PATH_KEYS` comment records this contract).
- `tool_audit` writes the snapshot payload blob without key assumptions (Plan Risks: read-only consumer confirmed), so the added component is additive-safe.

## Design decisions
- Snapshot becomes a 4-component set: `COMPONENT_KEYS` gains `dedup` (D-8); the component value is `absent` when the dedup store is not configured or cannot be opened, mirroring the existing `_ABSENT`/`_UNKNOWN` tolerance.
- `_DB_PATH_KEYS`/`_DB_PATH_DEFAULTS` gain the dedup entry (`db_path` key from `config/mcp_dedup.toml`) only to the extent the module needs the store path; the component itself is identity-based, not path-based.

## Alternatives considered
- Hashing the whole dedup DB file: rejected — identity row + fingerprint is cheaper, deterministic, and already defined by D-4.

## Implementation
### Target file
`scripts/shared/execution_snapshot.py`
### Procedure
Extend the snapshot builder with a `dedup` component and its config-key plumbing.
### Method
1. Add `dedup` to `COMPONENT_KEYS`.
2. Add a `_dedup_component(...)` (new) reader that opens the store path via the shared loader (`shared.mcp_dedup.load_dedup_config` / `open_dedup_store`) and returns `generation:fingerprint`, degrading to `_UNKNOWN`/`_ABSENT` on any open failure (never raises).
3. Add the `mcp_dedup` config-key entry alongside `rag`/`session`/`workflow` in `_DB_PATH_KEYS`/`_DB_PATH_DEFAULTS` where the builder needs the path; keep the fallback default `""` matching `config/mcp_dedup.toml` resolution.
### Details
- Current shape (verified 2026-11-21): `COMPONENT_KEYS = (deployed_rev, git_sha, config_hash, schema_versions)`; `_DB_PATH_KEYS` covers only rag/session/workflow.
- AC-7 pin: snapshots built before and after a generation rollover must differ on this component.

### Companion test files
- `tests/shared/test_execution_snapshot.py`
  - Procedure: Update the component-shape pins (`set(snap) == set(COMPONENT_KEYS)`) for `dedup`; add per-component mismatch cases for a store swap/rollover and a store-absent case.
  - Validation: `uv run pytest tests/shared/test_execution_snapshot.py` passes.

## Compatibility considerations
- Additive payload component: downstream consumers (`tool_audit`) pass the blob through unchanged; the shape change is covered by the companion test pins.

## Security considerations
- N/A: no new secrets or paths are exposed beyond the existing identity fingerprints already stored in the DB.

## Rollback considerations
- N/A: revert the commit; the snapshot is recomputed per call and persisted nowhere central.

## Validation plan
- `uv run pytest tests/shared/test_execution_snapshot.py`
- `uv run pytest tests/mcp_servers/` (payload passthrough fixtures).
- Full static gate per `rules/toolchain.md`.

## Completion criteria
- AC-7: pre-rollover and post-rollover snapshots are unequal on the `dedup` component; an absent/unopenable store yields a stable sentinel, not a failure.

## Out of Scope
- Store identity creation (row 01); audit payload changes (none needed).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Update companion test file per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `scripts/shared/execution_snapshot.py`, `tests/shared/test_execution_snapshot.py`
