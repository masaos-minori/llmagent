## Goal

Remove the absolute database path, database-wide counts and timestamps, and the configuration path from the MDQ health body, and report readiness through the closed non-sensitive state codes (REQ-003 non-sensitive health).

## Scope
**Release unit**: boundary-characterization-tests (Plan step 5 cites this row; the unit covers Phases 1, 3, 4, 5, 6)

## Assumptions
- Companion test rows (SKILL.md conditions 1-4 hold): `tests/mcp_servers/mdq/test_mdq_health.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`.
- Health body consumers read only the shared contract fields (`liveness`, `ready`, `degraded_reasons`, `capabilities`, `reason`); the removed `details` keys have no production consumer, only test assertions.
- The readiness codes come from `CAPABILITY_STATES` and `HEALTH_DEGRADED_REASON_CODES` in `scripts/shared/mcp_health_contract.py`; this document uses them and does not extend them.
- The configuration input is the shared startup result (seq 09), so the config exception message that embeds the configuration path is no longer produced inside this module.
- Cross-plan overlap on `docs/22_mcp/mcp_04_04_mdq.md` is a documentation-sequencing dependency, not a conflict.

## Design decisions
- Health keeps `make_health_response()`'s shape and the `ready` derivation from `scripts/mcp_servers/health_response.py`; only the non-contract `details` keys are removed.
- Readiness is expressed as capability state names (`ok`, `degraded`, `unavailable`) plus `HEALTH_DEGRADED_REASON_CODES`, not as path-bearing dependency text.

## Alternatives considered
- Keep `details` but mask the path — rejected: the requirement removes the field, and a masked absolute path is still a persistent identifier of the deployment layout.

## Implementation
### Target file
`scripts/mcp_servers/mdq/health_check.py`

### Procedure
- Remove `details["database"] = db_path` (line 146) and the `DEFAULT_DB_PATH` implicit path (line 31).
- Replace `deps["db_file"] = f"not found: {db_path}"` (line 153) with a degraded-reason code from the shared vocabulary.
- Remove `details.update(index_stats)` (line 166), which carries the database-wide counts and `last_indexed`.
- Replace `deps["config"] = f"check failed: {e}"` (line 178) with a reason code that names the field path only.
- Keep `details["allowed_dirs_count"]` and `details["deny_all"]`, which are already non-sensitive.

### Method
- The module reads the shared startup result instead of calling `ConfigLoader().load(MDQ_OWN_CONFIG_FILE)` itself, so no config exception is caught here.
- The schema-health probe stays, but its failure is reported as a reason code rather than a message containing the database path.

### Details
- `_collect_dependencies()` currently returns seven values, five of which feed `build_mdq_posture()`; the `deps`/`details` return stays for the health body, so the signature change is limited to the value types, not the shape.
- `test_mdq_health_endpoint.py` line 335 asserts `"database" in details`; that assertion is replaced by the companion test change.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_health.py`
  - Procedure: replace the global-count assertions in `test_deny_all_reports_zero_count_and_true` and `test_non_empty_allowed_dirs_reports_count_and_false` with non-sensitive state-code expectations; keep `test_raw_allowed_dirs_paths_not_exposed` as the leakage test.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_health.py`
- `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`
  - Procedure: update the body assertions that pin `details["database"]` (line 335) and the schema-error text that carries the path; the fixture classes' `deps` messages become reason codes.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_health_endpoint.py`

## Compatibility considerations
- The removed `details` keys are not part of the shared health contract, so no consumer outside the tests breaks.
- The `/health` body shape stays byte-for-byte compatible for the contract fields.

## Security considerations
- The absolute database path and the configuration path in dependency text are the leakage being removed (AC-2, AC-4).
- Reason codes must name field paths only, never values or secrets.

## Rollback considerations
- Revert the commit; the Phase 1 leakage tests in the companion files fail again.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_health.py tests/mcp_servers/mdq/test_mdq_health_endpoint.py tests/mcp_servers/mdq/test_mdq_health_posture.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- The ordinary health body contains no absolute database path, no database-wide count, no database-wide timestamp, and no configuration path.
- Readiness is reported only through the closed state and reason vocabularies.

## Out of Scope
- The shared startup configuration result (seq 09) and the posture view (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Two companion test files are covered by this document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Documentation is a separate row (seq 27) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-003 (non-sensitive health body)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `scripts/mcp_servers/mdq/health_check.py`, `tests/mcp_servers/mdq/test_mdq_health.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`
