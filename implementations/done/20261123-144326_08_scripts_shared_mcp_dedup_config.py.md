## Goal
- Extend the `[dedup]` validation with the optional threshold keys and the optional legal-hold key, so both are fail-closed and absent keys keep every committed config valid (REQ-003 configuration-based legal-hold boundary, REQ-007 threshold keys and their validation range without numeric values).

## Scope
**Release unit**: health exposure
- Adds the module-level table `DEDUP_OPTIONAL_INT_KEYS` (new) with `max_dedup_rows` (new) 1..10000000, `max_dedup_growth_per_hour` (new) 1..1000000, `max_dedup_wal_mb` (new) 1..4096, and the optional list key `legal_hold_states` (new).
- Adds the validator `_validated_optional_int()` (new) and a hold-state name check, both reusing the existing `ConfigParseError` wording.
- Adds the matching `DedupStoreConfig` fields, all excluded from `_config_fingerprint`.
- Out of scope: threshold values themselves (`U-1`, operator-supplied), the 10 committed `config/*_mcp_server.toml` files (unchanged and still valid), and any store or dispatcher behaviour change.

## Assumptions
- Absent means unset: an unset key produces `None` (or an empty tuple) and no status is computed for that metric, so thresholds and holds are status-report only, per the Plan's `D-6` decision.
- The keys stay out of `_config_fingerprint`: store identity is unchanged (owner decision `D-5`), so no store re-initialization or fingerprint drift happens.
- Legal hold is configuration-based (`U-2`): no new stored column, so there is no persisted-schema change and the schema-fingerprint assertions in `tests/deploy/test_init_db_schema_gate.py` stay as they are.
- Unknown keys already fail closed, so a misspelled threshold key is rejected by the existing check once these names are allowed.

## Design decisions
- A separate optional table instead of joining `_DEDUP_INT_KEYS` (lines 38-44): that table's shape is `(default, low, high)` and inventing numeric defaults would put values in the Plan that the Plan says are operator-supplied.
- Hold names are validated against the stored row states — the four names in the `status` `CHECK` of `_SCHEMA` in `scripts/shared/mcp_dedup_schema.py` — kept as a module-level `LEGAL_HOLD_STATES` (new) frozenset so the shared leaf gains no new import.
- Same fail-closed contract as the existing keys: an out-of-range value or an unknown state name aborts startup rather than being clamped.

## Alternatives considered
- Adding the thresholds to `_DEDUP_INT_KEYS` with sentinel defaults: rejected, it would add numeric values and change what `_config_fingerprint` covers for the 10 committed configs.
- Validating holds in `scripts/shared/config_loader.py`: rejected, the loader does not validate keys; `load_dedup_section()` is the validation row.

## Implementation
### Target file
`scripts/shared/mcp_dedup_config.py`

### Procedure
1. Add `DEDUP_OPTIONAL_INT_KEYS` (new) as `dict[str, tuple[int, int]]` mapping each name to its inclusive `(low, high)` range.
2. Add `LEGAL_HOLD_STATES` (new) as the frozenset of the four stored row states.
3. Add `_validated_optional_int()` (new): when the key is absent return `None`; otherwise apply the same checks as `_validated_int()` (lines 85-101) — reject a bool or non-int, then reject a value outside the inclusive bounds — with the same `dedup.<name>` message shapes.
4. Add the hold check: the value must be a list of strings, every name in `LEGAL_HOLD_STATES` (new), otherwise raise `ConfigParseError` naming `dedup.legal_hold_states` (new); absent or empty means no hold.
5. Extend the `unknown_keys` computation in `load_dedup_section()` (lines 104-158) so the four new names are allowed, and pass the validated values into `DedupStoreConfig` (lines 47-55) as new fields: `max_dedup_rows` (new), `max_dedup_growth_per_hour` (new), `max_dedup_wal_mb` (new) as `int | None = None`, and `legal_hold_states` (new) as `tuple[str, ...] = ()`.
6. Leave `_config_fingerprint` payload keys exactly as they are: `db_path`, `retention_days`, `pending_timeout_minutes`, `lease_seconds`, `max_attempts`.

### Method
- No default values are introduced for any new key: `retention_days`, `pending_timeout_minutes`, `lease_seconds`, `max_attempts` keep their existing defaults and ranges.
- Frozen-dataclass fields are appended after the existing five, so positional construction of `DedupStoreConfig` keeps working for every current caller.

### Details
- `load_dedup_section()` keeps its pure contract (no path resolution, no cache), and `scripts/mcp_servers/server.py` still calls it at startup, so the startup gate every server passes today must keep passing.
- The hold tuple is consumed by the ledger sweep (`_legal_hold_states()` (new) in `scripts/shared/mcp_dedup_ledger.py`) and reported by the metrics read; neither is changed by this document beyond reading the field.
- Evidence that the contract is pinned: `TestDedupSectionValidation` in `tests/shared/test_mcp_dedup.py` asserts the current out-of-range and unknown-key behaviour, and it must stay passing for sections that carry none of the new keys.

### Companion test files
- `tests/mcp_servers/test_config_isolation_fail_closed.py`
  - Procedure: extend the parametrized case list at lines 141-157 with a written own config whose `max_dedup_growth_per_hour` (new) value is outside 1..1000000 and one whose `legal_hold_states` (new) names a state that is not a stored state, each expecting `ConfigParseError` with the `dedup.<key>` message before uvicorn runs; extend `test_valid_own_table_injects_dispatcher_globals` or add a case proving a table carrying valid optional keys loads and injects, while the existing tables without any new key keep passing unchanged.
  - Validation: `uv run pytest tests/mcp_servers/test_config_isolation_fail_closed.py tests/shared/test_mcp_dedup.py`

## Compatibility considerations
- `TestDedupSectionValidation` in `tests/shared/test_mcp_dedup.py` pins the current key validation: sections without the optional keys must produce the same `DedupStoreConfig` values as today.
- `tests/deploy/test_init_db_schema_gate.py` asserts the config-file count and the schema fingerprint; no config file and no DDL is added here, so it must keep passing unchanged.
- `scripts/mcp_servers/server.py`'s startup validation gate and `scripts/shared/config_loader.py`'s `restrict_to()` loading path are unchanged.

## Security considerations
- Fail-closed validation means a malformed threshold or hold list stops the server instead of silently disabling the guard.
- A hold list can only name stored states, so it cannot be used to exclude arbitrary rows or key values from the sweep.

## Rollback considerations
- Revert the commit: the new fields default to unset, so a revert leaves every committed config and every store identity unchanged (`_config_fingerprint` was never touched).

## Validation plan
- `uv run pytest tests/mcp_servers/test_config_isolation_fail_closed.py tests/shared/test_mcp_dedup.py` (unit, expect Pass).
- `uv run python tools/run_validation_gates.py` for the diff, plus the full sequence in `rules/toolchain.md`.

## Completion criteria
- An out-of-range threshold value or an unknown hold-state name aborts startup with `ConfigParseError` naming the file and the key.
- Configs without any new key validate to the same values and the same fingerprint as before, and the 10 committed config files are untouched.

## Out of Scope
- Threshold values (`U-1`), the sweep's use of the hold tuple (row 07), the metrics status blocks (row 05), and the `[dedup]` key inventory document (row 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the optional-key table, validator, hold-name check, and config fields per Procedure/Method/Details | Completed | — | 20261123-221656 | `_config_fingerprint` stays untouched Changed: scripts/shared/mcp_dedup_config.py (DEDUP_OPTIONAL_INT_KEYS as dict[str, tuple[int, int]] with the three documented ranges, LEGAL_HOLD_STATES frozenset of the four stored row states, _validated_optional_int(), _validated_hold_states(), the four DedupStoreConfig fields appended after the existing five, unknown_keys extended, docstring sentence). _config_fingerprint payload keys untouched (D-5). Failure Log: first version used dedup.get("legal_hold_states", ()) and the default tuple failed the list check, so an absent key raised ConfigParseError and the whole file failed; fixed by returning () before the type check. One justified nosec B608 is recorded in the code comment (see row 07 notes). |
| 2 | Extend `tests/mcp_servers/test_config_isolation_fail_closed.py` per the companion Procedure | Completed | — | 20261123-221656 | Extended tests/mcp_servers/test_config_isolation_fail_closed.py: two parametrized cases (max_dedup_growth_per_hour outside 1..1000000, legal_hold_states naming a non-stored state) and test_valid_optional_keys_load_and_keep_store_identity, which asserts a table with valid optional keys loads and injects, that a table without them keeps every field unset, and that the two fingerprints are equal (D-5). Run: 77 passed (this file 9, tests/shared/test_mcp_dedup.py 68 including TestDedupSectionValidation unchanged). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-230806 | 20261123-230806 | This member Step 3e: ruff format/check pass, run_validation_gates.py fast mode all applicable gates Pass, lint-imports 6 contracts kept, bandit clean on this file, mypy clean across scripts/. Full suite runs once at end of the release unit. Note: this row was executed before row 07, a seq-order deviation reported in the final report. End-of-unit run for the release unit: full suite with coverage 13660 passed 4 skipped, diff-scoped coverage 94 percent against the 90 gate, all gates pass. Deviation: the run was executed once for the whole diff. |

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
- **Requirement ID**: REQ-003 (define the legal-hold boundary as a configuration entry), REQ-007 (define the threshold keys and their validation range without numeric values)
- **Source issue**: issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-144326
- **Related target files**: `scripts/shared/mcp_dedup_config.py`, `tests/mcp_servers/test_config_isolation_fail_closed.py`