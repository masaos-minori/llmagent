## Goal

Make the dedup store openable only through an injected `DedupStoreConfig`, enforce the stored-vs-injected fingerprint on reopen (`identity_mismatch` (new)), and retire the `retry_class()` facade (REQ-001, REQ-007, REQ-008).

## Scope
**Release unit**: dedup-config-isolation-core (shared-store config isolation, store-identity gate, and operational reference removal)

## Assumptions
- `DedupStoreConfig` and `load_dedup_section()` are declared by sibling seq 01 (`resolved from sibling`).
- Facade re-exports of the renamed config type stay consistent with seq 01 in the same delivery.

## Design decisions
- `open_dedup_store()` (line 411) requires the injected config: delete the `path=None → load_dedup_config()` fallback rather than deprecating it (fail-fast is the requirement).
- `_classify_existing()` gains one check before any query: stored `config_fingerprint` (written at `_first_initialization`, lines 205-209, never compared today) vs `_config_fingerprint(effective config)` → raise `DedupStoreError("identity_mismatch", ...)` (new state) on drift.
- Phased facade handling: Phase 1 turns `retry_class()` into a deprecated reference lookup over `RETRYABLE_TOOLS` (no config argument dependency); Phase 3 deletes it once `dispatch.py` (seq 03) switches to registry metadata.
- Adversarial verification (2026-11-22): Phase 1/Phase 3 are delivered in one commit (01/02/03/11 land together), so the deprecated-`retry_class()` intermediate step is skipped — the facade and all callers drop `retry_class` in the same change. `START_STATES` in `scripts/shared/mcp_dedup_schema.py` gains `identity_mismatch` (the drift check enumerates it).
- Implementation correction (2026-11-22): the config-less `DedupStore(db_path)` class seam stays public (fixtures and operator resolution via `resolve_store` construct it directly); the fingerprint comparison runs only when a config is injected through `open_dedup_store()`.

## Alternatives considered
- Auto-recreating the store on fingerprint drift: rejected — REQ-007 fails closed; recovery stays the existing archive-and-recreate path via `resolve_store`.
- Keeping `retry_class(name, config)` with an ignored config argument: rejected — the mirror is deleted outright (REQ-005).

## Implementation
### Target file
`scripts/shared/mcp_dedup.py`
### Procedure
1. Phase 1: change `open_dedup_store()` to a required `DedupStoreConfig` parameter; update the facade re-export list (line ~54-97) to the renamed type; make `retry_class()` a deprecated `RETRYABLE_TOOLS`-based lookup with a `DeprecationWarning`-free docstring note pointing at tool metadata.
2. Phase 3: in `_classify_existing()` (line 231), after the marker/identity checks and before any query, compare the identity row's `config_fingerprint` with the injected effective fingerprint and raise `DedupStoreError("identity_mismatch", ...)` naming the drift (new state alongside the four legacy states: `legacy_or_unverified`, `schema_mismatch`, and the two marker/uuid refusals — enumeration preserved).
3. Phase 3: delete the `retry_class()` facade and any remaining `retry_class` plumbing in this module.
### Method
Insert the fingerprint comparison where the existing identity row read (`SELECT store_uuid, generation, schema_fingerprint FROM store_meta`) already happens, reusing that read; do not add a second query.
### Details
- Module is 20,074 B (gate 24,576 B): headroom is sufficient.
- Keep the exported exception taxonomy (`DedupStoreError`) and `REFUSAL_MESSAGE` wording style in the new state message.

### Companion test files
- `tests/shared/test_mcp_dedup_identity.py`
  - Procedure: add cases — reopen with a drifted validated set raises `DedupStoreError` with state `identity_mismatch` (new) before any query; reopen with an identical injected set preserves continuity (`healthy`, same generation); four legacy-state cases unchanged.
  - Validation: `uv run pytest tests/shared/test_mcp_dedup_identity.py -q` plus the scratch-database recipe in `rules/persisted-schema-change.md`.

## Compatibility considerations
- `deploy/init_db.sh` (seq 25) and `scripts/shared/execution_snapshot.py` (seq 11) are the remaining no-arg/`path=` callers; they are updated in this plan, and the transitional `dispatch.py` bootstrap (seq 03) keeps the suite green between Phase 1 and Phase 2.

## Security considerations
- The fingerprint gate is the fail-closed mechanism against a server whose injected `[dedup]` semantics disagree with the shared store (REQ-007); no silent migration path.

## Rollback considerations
- Revert the commit; the four legacy states keep older readers functional, and the fingerprint row already exists in every installed store.

## Validation plan
- `uv run pytest tests/shared/test_mcp_dedup_identity.py tests/shared/test_mcp_dedup.py tests/shared/test_mcp_dedup_concurrency.py -q`; scratch-database identity recipe; `uv run mypy scripts/shared/mcp_dedup.py`; `uv run python tools/check_module_size.py`.

## Completion criteria
- `open_dedup_store()` has no discovery fallback (grep: no `load_dedup_config` call in this module); a drifted reopen deterministically raises `identity_mismatch` (new) before any query; identical reopen is a no-op; `retry_class` no longer exists after Phase 3.

## Out of Scope
- `dispatch.py` retry-decision switch and `configure_dedup()` (seq 03); per-server `[dedup]` tables (seq 13-22).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: injected-config `open_dedup_store()` + facade rename + deprecated `retry_class()` reference | Completed | 2026-11-22 | 2026-11-22—implemented+validated (phases collapsed, one commit)|
| 2 | Phase 3: `identity_mismatch` (new) fingerprint gate in `_classify_existing()` | Completed | 2026-11-22 | 2026-11-22—implemented+validated (phases collapsed, one commit)|
| 3 | Phase 3: delete the `retry_class()` facade and retry plumbing | Completed | 2026-11-22 | 2026-11-22—implemented+validated (phases collapsed, one commit)|
| 4 | Add or update companion tests per Validation plan | Completed | 2026-11-22 | 2026-11-22—implemented+validated (phases collapsed, one commit)|
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22—implemented+validated (phases collapsed, one commit)|

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
- **Requirement ID**: REQ-001, REQ-007, REQ-008; AC-002, AC-004
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `scripts/shared/mcp_dedup.py`, `tests/shared/test_mcp_dedup_identity.py`
