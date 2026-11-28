## Goal

State explicitly in the deployed configuration the keys that `MdqConfig` currently supplies as defaults, so production construction has no implicit default (REQ-007 explicit configuration).

## Scope
**Release unit**: boundary-characterization-tests (Plan step 6 cites this row; the unit covers Phases 1, 3, 4, 5, 6)

## Assumptions
- `tests/mcp_servers/mdq/test_mdq_config.py` is covered by seq 23, which is not a companion of this row.
- The file lists 13 `MdqConfig` keys plus `auth_token` and `db_path` (re-verified 20261127); the five keys named in the plan are absent.
- `deploy/deploy.sh` already copies this file to the deployed config directory with an existing `cp` line, so no deploy change is needed.

## Design decisions
- The added keys carry the same values the pydantic defaults supply today, so production behavior is unchanged while the default path is removed by seq 06.

## Alternatives considered
- N/A: the row adds five keys; no alternative design is implied.

## Implementation
### Target file
`config/mdq_mcp_server.toml`

### Procedure
- Add `context_before = 2`, `context_after = 2`, `max_chars_per_match = 500`, `max_outline_depth = 6`, `sqlite_busy_timeout = 5000` with the current default values.

### Method
- N/A: no code change; the values match `scripts/mcp_servers/mdq/mdq_models.py` lines 115-120.

### Details
- The historical-notes comment in the file points to a config-history document that does not exist under `docs/`; the rename note for `max_file_chars` is written by seq 27 in the doc named by the task map, not here.
- Step 3b correction (20261128): verified against current source. The file carries 13 declared keys plus `auth_token` and `db_path`; the five named keys are absent as stated. They are added in the result-size section, after `max_grep_matches`, with the values the pydantic defaults supplied.
- Step 3b correction (20261128): this row ran before seq 06's validation. `mdq_server.py` constructs the service at import from the production configuration, so once `MdqConfig` has no defaults, a configuration missing any declared key fails at import — every test module that imports the server collects against this file. All 18 keys must be present before the model tests can pass.

## Compatibility considerations
- The deployed configuration gains keys; the values are identical to today's defaults, so no behavior change.

## Security considerations
- N/A: no secret or path is added.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py`
- Deploy verification: confirm the deployed file matches the repository file after the added keys.

## Completion criteria
- Every `MdqConfig` key is present in the deployed configuration.
- The added values equal the values the defaults supplied before the change.

## Out of Scope
- The strict type primitives (seq 06) and the documentation of the compatibility change (seq 27).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128-093658 | 20261128-093658 | the five declared keys added after max_grep_matches with the values the removed defaults supplied; the file now carries all 18 keys and is read through load_startup_config() |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128-093658 | 20261128-093658 | Config-only change; no test change end-of-unit gate 20261128 as recorded in seq 01's gates row |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-007 (explicit production configuration)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `config/mdq_mcp_server.toml`