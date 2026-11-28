## Goal

Set `config_dependent` to `True` for the MDQ tool entries whose availability depends on configuration (REQ-001 per-tool availability metadata).

## Scope
**Release unit**: boundary-characterization-tests (Plan step 3 cites this row; the unit covers Phases 1, 3, 4, 5, 6)

## Assumptions
- Every MDQ tool entry is set to `True`, because the availability function in seq 01 answers for every tool name and returns disabled when no roots are authorized; `grep_docs` additionally depends on `enable_grep`.
- `tests/mcp_servers/test_tool_schema.py` is a related test but not a target row, so it is not a companion; it asserts only that the field is present as a boolean.
- Cross-plan overlap on `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md` with `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md` is compatible: this row corrects the MDQ sentence, that plan does not change the same statement. Verified 20261128: that plan's row for the same document adds the status vocabulary and the `disabled_reason` fallback, not the `config_dependent` value statement.

## Design decisions
- The metadata value is the producer-declared flag and is never derived from `status`; it must match the tool's actual dependency on configuration.

## Alternatives considered
- N/A: the row changes one declared value per entry.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_tools.py`

### Procedure
- Change `"config_dependent": False` to `True` for the seven entries: `search_docs` (line 69), `get_chunk` (line 103), `outline` (line 139), `index_paths` (line 168), `refresh_index` (line 201), `stats` (line 219), `grep_docs` (line 270).

### Method
- No other field is touched; the tool names stay identical to `MDQ_TOOLS` in `scripts/shared/tool_constants.py`.

### Details
- N/A: no behavior change beyond the declared metadata value.
- Step 3b correction (20261128): the seven cited lines are confirmed (`mdq_tools.py` 69, 103, 139, 168, 201, 219, 270) and all seven are the MDQ tool entries, so the change applies to every entry as the Assumptions state.
- Step 3b correction (20261128): no test pins the declared value for MDQ. `tests/mcp_servers/test_tool_schema.py` asserts only that the field is present as a boolean, so the change is not observable through the test suite; the completion criterion is verified by reading the entries. Recorded as a validation gap, not closed here because adding an assertion is outside this row.
- Step 3b correction (20261128): `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md` line 25 states `config_dependent` is `false` for `mdq`. After this change the code and the documentation disagree, so seq 28 has to land in the same release unit as this row.

## Compatibility considerations
- `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` pins `MDQ_TOOLS == TOOL_LIST` names and is unaffected by the value change.
- `docs/22_mcp/mcp_01_tool_ownership_matrix.md` lists the seven MDQ tools and is unaffected.

## Security considerations
- N/A: metadata only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_tool_schema.py tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`
- Documentation sentence in `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md` is corrected by seq 28.

## Completion criteria
- The declared value matches the tool's actual dependency on configuration.
- The tool inventory and the boolean field shape stay unchanged.

## Out of Scope
- The availability function itself (seq 01) and the documentation correction (seq 28).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | Seven entries changed to `True` (`mdq_tools.py` 69, 103, 139, 168, 201, 219, 270); no other field touched |
| 2 | Add or update tests per Validation plan | Completed | 20261128 | 20261128 | No test change; existing assertions stay compatible. Targeted run 20261128: 14 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128-093658 | 20261128-093658 | ruff format/check Pass. Registry and routing tests re-run 20261128: 133 passed. Full sequence runs at the end of the release unit end-of-unit gate 20261128 as recorded in seq 01's gates row |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261128-093658 | 20261128-093658 | Covered by seq 28 Covered by seq 28, which was executed 20261128 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-001 (per-tool availability metadata)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `scripts/mcp_servers/mdq/mdq_tools.py`