## Goal
- Re-export the new metrics module's public names through the dedup facade so `mcp_servers` consumers import them from `shared.mcp_dedup` like every other store name (REQ-004 publish the metrics through the existing store surface).

## Scope
**Release unit**: health exposure
- Adds one submodule import block and two `__all__` entries in `scripts/shared/mcp_dedup.py`.
- No signature, class, or behaviour change: the facade stays a re-export layer.
- Out of scope: the metrics module itself (row 05) and the health `details` wiring (row 09).

## Assumptions
- `scripts/shared/mcp_dedup_metrics.py` (new) is created by row 05 of the same Plan, an earlier sequence number, so its names exist by the time this row is exercised.
- Only the two public names are re-exported; the ledger read helpers stay reachable through the store object and are not facade names.
- The config-side keys (`max_dedup_rows` (new), `legal_hold_states` (new)) reach the store through `DedupStoreConfig` and `open_dedup_store`, which this row does not change.

## Design decisions
- Follow the existing family pattern exactly: submodule imports first, then the public names listed in `__all__`; no aliasing and no wrapper function.
- Keep `shared.mcp_dedup_metrics` a leaf import (`DedupLedger` typing only) so the import-layer contract (`uv run lint-imports --config .importlinter`, 6 contracts) stays kept.

## Alternatives considered
- Importing the metrics module directly from each server handler: rejected, because every other dedup name is facade-mediated and the facade is the contract `mcp_servers` is allowed to import.

## Implementation
### Target file
`scripts/shared/mcp_dedup.py`

### Procedure
1. Add a block importing `METRICS_SCHEMA_VERSION` and `collect_dedup_metrics` from `shared.mcp_dedup_metrics`, placed with the other submodule import blocks (the existing pattern at lines 46-89, which imports `shared.mcp_call_state_contract`, `shared.mcp_dedup_config`, `shared.mcp_dedup_ledger`, `shared.mcp_dedup_rows`, `shared.mcp_dedup_schema`); the new block goes between `mcp_dedup_ledger` and `mcp_dedup_rows` because ruff rule `I` (isort) orders them by module name.
2. Add both names to `__all__` (lines 93-121), keeping the file's existing grouping: constant names with the constants, snake_case names with `classify_interrupted` and `load_dedup_section`.
3. Leave the module docstring's module-family paragraph accurate: add the metrics module to the sentence that lists which submodule owns what.

### Method
- Re-export only: no new class, no new argument, no change to `DedupStore`, `open_dedup_store`, or `read_store_identity`.
- No name collision: `grep` for both names in `scripts/` now returns only their definitions in
  `scripts/shared/mcp_dedup_metrics.py` (row 05, already landed in this batch), so the facade
  re-export is the only consumer.

### Details
- The facade already owns the store lifecycle and the WAL pragma (`scripts/shared/mcp_dedup.py` line 169), and the new names touch neither, so the diff is import-and-list only.
- Module size stays under the 24576 B gate: the file is 20748 B before this change (the 20435 B
  figure recorded at generation time is the measured value corrected in this cycle).
- `tests/shared/test_mcp_dedup.py` imports facade names (`DedupStore`, `DedupStoreConfig`, `open_dedup_store`, `load_dedup_section`) and keeps working unchanged; the new-name assertions live in the row 05 companion test.

## Compatibility considerations
- Purely additive: `BASE_KEYS`-style payload assertions and `tests/deploy/test_init_db_schema_gate.py`'s config-file count are untouched by this row.
- `tests/shared/test_mcp_dedup.py` (`TestTtlPurge`, `TestDedupSectionValidation`) import from the facade; neither import path nor behaviour changes here.
- The same file is a shared target of the mcpdl004 plan; that plan adds result metadata, this row adds two names, so the edits do not collide.

## Security considerations
- No new data path: the facade exposes the same read-only function row 05 defines, which reports counts and the store path only.

## Rollback considerations
- N/A: revert the commit. The two import and list lines have no behaviour to unwind.

## Validation plan
- `uv run pytest tests/mcp_servers/test_health_response.py tests/shared/test_mcp_dedup.py`
- `uv run python tools/run_validation_gates.py` for the diff, plus the full sequence in `rules/toolchain.md`.

## Completion criteria
- `collect_dedup_metrics` and `METRICS_SCHEMA_VERSION` are importable from the facade, and both appear in `__all__`.
- The import-layer contract and the module-size gate pass with the new import block in place.

## Out of Scope
- Implementing the metrics read (row 05), the ledger read helpers (row 07), the config keys (row 08), and the health `details` block (row 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the import block and the two `__all__` entries per Procedure/Method/Details | Completed | — | 20261123-215732 | changed: scripts/shared/mcp_dedup.py (import block between mcp_dedup_ledger and mcp_dedup_rows, two __all__ entries, module-family docstring sentence). 3b corrections: isort placement, __all__ line range 93-121, measured size 20748 B, names now exist from row 05. |
| 2 | Extend facade coverage in the row 05 companion test rather than a new file here | Completed | — | 20261123-220043 | No test file of its own: this row has no companion No test file of its own. Facade coverage is asserted in tests/shared/test_mcp_dedup_metrics.py TestFacadeReExport (row 05 companion), which is red only on symbols a later member creates. Impact-selected run for this file: tests/shared/test_mcp_dedup.py 55 passed, 13 deselected. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-230806 | 20261123-230806 | This member's Step 3e: ruff format/check pass, tools/run_validation_gates.py fast mode all applicable gates Pass, lint-imports 6 contracts kept, bandit reports only the pre-existing B101 at line 385. mypy is red only on symbols created by siblings (view = row 07, config fields = row 08). Full suite runs once at end of the release unit. End-of-unit run for the release unit: full suite with coverage 13660 passed 4 skipped, diff-scoped coverage 94 percent against the 90 gate, all other gates pass. Deviation: the run was executed once for the whole diff, as recorded in row 05. |

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
- **Requirement ID**: REQ-004 (publish the read-only metrics through the existing store and health surface)
- **Source issue**: issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-144326
- **Related target files**: `scripts/shared/mcp_dedup.py`