## Goal

Turn the dedup config module into a pure, discovery-free validator: a typed `DedupStoreConfig` (new) contract plus `load_dedup_section()` (new), with no per-process file discovery, no cache, and no `[retry_class]` mirror validation (REQ-003, REQ-005, REQ-006).

## Scope
**Release unit**: dedup-config-isolation-core (shared-store config isolation, store-identity gate, and operational reference removal)

## Assumptions
- Consumers (`scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/dispatch.py`, `tests/mcp_servers/conftest.py`) switch to the new contract in sibling procedures (seq 02, 03, 34); this module stops exporting the removed names in the same delivery unit.
- Adversarial verification (2026-11-22): deleting the removed names here breaks `scripts/shared/mcp_dedup.py` (facade imports at lines 45-57) and the deferred `load_dedup_config` import in `scripts/shared/execution_snapshot.py` (lines 154-156) the moment this lands; the suite can only be green after seq 02 and seq 11 are applied. Implement and validate 01/02 (and 11's import fix) within the same delivery-unit commit, not standalone.
- UNK-02: the key name/range decided here concerns only store fields; the Agent-side horizon key belongs to seq 05.

## Design decisions
- `DedupStoreConfig` (new) keeps today's validated store fields (`db_path`, `retention_days`, `pending_timeout_minutes`, `lease_seconds`, `max_attempts`) and drops the `retry_class` field entirely (REQ-005).
- `load_dedup_section()` (new) is a pure function over an already-loaded mapping (the `[dedup]` table), not a path: callers own where the table came from; per-server isolation (`ConfigLoader.restrict_to`) stays outside this module.
- Validation errors keep the current typed surface — `ConfigParseError`/`ConfigMissingError` from `shared.config_errors` with `dedup.<key>`-prefixed messages (verified 2026-11-22: no DedupConfigError type exists in current source).

## Alternatives considered
- Keeping `load_dedup_config(path)` with a `None` default: rejected — path discovery is exactly what REQ-001/REQ-004 removes.
- Replacing the dataclass with a plain validated dict: rejected — the plan requires a typed contract and the fingerprint already serializes the validated effective values.

## Implementation
### Target file
`scripts/shared/mcp_dedup_config.py`
### Procedure
1. Delete `_default_config_path()` (line 69), `_DEDUP_CONFIG_CACHE` (line 42), `clear_dedup_config_cache()`, and `_validated_retry_class()` (line 92) plus the `RETRYABLE_TOOLS`/`get_all_mcp_tool_names` imports used only by the mirror validation.
2. Rename the public `DedupConfig` dataclass to `DedupStoreConfig` (new) and drop its `retry_class` field; keep the fingerprint helper (`_config_fingerprint` input) over the remaining fields.
3. Add `load_dedup_section()` (new): accepts the mapping for a `[dedup]` table, rejects a missing table (`ConfigMissingError`), invalid types, booleans-as-integers (explicit `bool` guard), unknown keys, and a `db_path` that is not the canonical dedup store path (`ConfigParseError`, messages naming `dedup.<key>`); returns a `DedupStoreConfig` (new). Contract definition (owner decision 2026-11-22, corrected at implementation 2026-11-22): `db_path` must equal exactly `dedup_db_dir() / "mcp_dedup.sqlite"` where `dedup_db_dir()` is `Path(os.environ.get("LLMAGENT_DB_DIR", Path(DEFAULT_DB_PATH).parent))` — the env override exists for test and development runs. The contract pins the filename too: the `.mcp_dedup_installed` marker is directory-scoped and `execution_snapshot` reads the canonical path, so a second, differently named store in the same directory would be misclassified (`lost`) and invisible to the snapshot.
4. Update the module docstring (facade note) and keep the `DEFAULT_*` constants; module is 7,589 B, well under the 24,576 B gate.
### Method
Keep the existing per-key validation code paths, re-pointed at the mapping argument instead of a file; the `path`/cache branch of `load_dedup_config` disappears rather than being refactored.
### Details
- `DEFAULT_DB_PATH`/`DEFAULT_RETENTION_DAYS`/`DEFAULT_PENDING_TIMEOUT_MINUTES`/`DEFAULT_LEASE_SECONDS`/`DEFAULT_MAX_ATTEMPTS` all stay (verified 2026-11-22: `DEFAULT_MAX_ATTEMPTS = 3` already exists at line 31 — no new default is needed).
- Implementation correction (2026-11-22): when the table omits `db_path`, the default is derived as `dedup_db_dir() / Path(DEFAULT_DB_PATH).name`, not the literal `DEFAULT_DB_PATH` — a fixed default would contradict the contract whenever `LLMAGENT_DB_DIR` overrides the directory.
- Do not import `scripts/db` or `ConfigLoader` here (shared-leaf contract preserved).

### Companion test files
- `tests/shared/test_mcp_dedup.py`
  - Procedure: retarget loader tests from file discovery/cache to `load_dedup_section()` over dicts; delete the `[retry_class]` validation and cache-clearing cases; keep per-key strictness cases with the new `dedup.<key>` expectations.
  - Validation: `uv run pytest tests/shared/test_mcp_dedup.py -q` green, no discovery/cache imports left in the file.

## Compatibility considerations
- Cross-module renames (`DedupConfig` → `DedupStoreConfig` (new)) land in the same delivery unit as seq 02/03/34; the `shared.mcp_dedup` facade re-exports are updated there, not here.
- Transitional `config/mcp_dedup.toml` bootstrap in `dispatch.py` (seq 03, Phase 1 bullet) keeps the suite green between phases.

## Security considerations
- Unsafe-path rejection (`db_path` inside the dedup database directory contract) and boolean-as-integer rejection are explicit requirements (REQ-006), not best-effort.

## Rollback considerations
- Revert the commit; no persisted state changes. The store fingerprint is computed from the same effective values, so no migration is involved.

## Validation plan
- `uv run pytest tests/shared/test_mcp_dedup.py -q` (companion retarget) and `uv run pytest tests/shared -q`.
- `uv run mypy scripts/shared/mcp_dedup_config.py`, `uv run ruff check scripts/shared/`, `uv run python tools/check_module_size.py`.

## Completion criteria
- No discovery, cache, or retry-mirror code remains in the module; every invalid input listed in REQ-006 raises a `shared.config_errors` type naming file and key; companion tests green.

## Out of Scope
- `scripts/shared/mcp_dedup.py` facade/`open_dedup_store` changes (seq 02); per-server `[dedup]` tables (seq 13-22); deleting `config/mcp_dedup.toml` (seq 23).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-22 | 2026-11-22—implemented+validated|
| 2 | Add or update companion tests per Validation plan | Completed | 2026-11-22 | 2026-11-22—implemented+validated|
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22—implemented+validated|
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-22 | 2026-11-22—no docs in scope; docs owned by seq 47-54|

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
- **Requirement ID**: REQ-003, REQ-005, REQ-006; AC-002
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `scripts/shared/mcp_dedup_config.py`, `tests/shared/test_mcp_dedup.py`
