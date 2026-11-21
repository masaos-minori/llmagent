## Goal

Remove `McpServerConfig.tool_names` and its validator from `scripts/shared/mcp_config.py` (`REQ-003`): the field (line 70), the call in `_validate_cross_fields` (line 131), the `_validate_tool_names` method (lines 171-180), and the builder kwarg (line 303). Keep `McpServerConfig.required` unchanged.

## Scope
**Release unit**: tool_names removal and required-capability model

## Assumptions
- The four locations are verified against current source: field (line 70), call (line 131), method body (lines 171-180), builder kwarg (line 303). If `agentcfg001` adds fields to `McpServerConfig` first, these line numbers shift and must be re-verified.
- `required` stays on `McpServerConfig`; the required-server check moves to the required-capability model (`REQ-005`, covered by the `mcp_tool_discovery.py` and `config/tool_catalog.toml` rows).
- Removing the field forces two uncovered production consumers to be updated (fallout): `mcp_status.py:86` (`_tier_for_server(cfg.tool_names, ...)`) and `mode_classification.py:53` (MDQ-availability check). These are added to the Plan as fallout rows and handled by their own procedures.

## Design decisions
- Delete the whole `_validate_tool_names` method together with its call site and the field, so no dangling validator or field reference remains.
- Delete only the `tool_names=` kwarg from the single `McpServerConfig(...)` construction; leave the other kwargs (`auth_token`, `role`, `required`) intact.

## Alternatives considered
- Keep the field as an unused attribute: rejected by `REQ-003`, which requires the field gone so no consumer can read a removed value.

## Implementation
### Target file
`scripts/shared/mcp_config.py`

### Procedure
Remove all four `tool_names` references in `mcp_config.py`: the field, the validator call, the validator method, and the builder kwarg.

### Method
Edit the dataclass body, the `_validate_cross_fields` method, and the `_build_single_server`-style constructor call; confirm the module still imports.

### Details
- Delete the field declaration at line 70 (`tool_names: list[str] = field(default_factory=list)`).
- Delete the call at line 131 (`self._validate_tool_names(key_prefix)`).
- Delete the `_validate_tool_names` method (lines 171-180).
- Delete the `tool_names=list(v.get("tool_names", []))` kwarg at line 303.
- Grep the module for any residual `tool_names` and remove only those that reference the removed field (leave unrelated local variables untouched).

## Compatibility considerations
Backward incompatible by design (`REQ-003`): any code reading `McpServerConfig.tool_names` now fails. The direct consumers are `mcp_tool_discovery.py` (required-check, replaced by `REQ-005`), `tool_routing_validation.py` (drift check, replaced by `REQ-004`), plus the two fallout consumers `mcp_status.py` and `mode_classification.py`.

## Security considerations
Removing the field closes the per-server allowlist that could restrict or redirect which tools discovery surfaces; the required-capability model (`REQ-005`) replaces it fail-closed.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Build `McpServerConfig` without `tool_names` and assert the attribute is absent; run the affected shared-config and discovery tests.

## Completion criteria
`McpServerConfig` exposes no `tool_names` field and no `_validate_tool_names` method, the builder kwarg is gone, and no in-module reference to the removed field remains.

## Out of Scope
The required-capability conversion (`mcp_tool_discovery.py`), the drift-check rewrite (`tool_validation.py`, `tool_routing_validation.py`), the registry manifest (`config/tool_catalog.toml`), the two fallout consumers (`mcp_status.py`, `mode_classification.py`), tests, and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-201200 | 20261120-201200 | Removed all four `tool_names` references from `scripts/shared/mcp_config.py`: the field (line 70), the `_validate_cross_fields` call (line 131), the `_validate_tool_names` method (lines 171-180), and the builder kwarg (line 303). `required` left intact. Module parses; grep for `tool_names` returns 0. Confirmed via import: `McpServerConfig` has no `tool_names` field and no `_validate_tool_names` method. |
| 2 | Add or update tests per Validation plan | Completed | 20261120-201200 | 20261120-201200 | Fixed the two direct `mcp_config` test files whose fixtures asserted the removed field: deleted `test_tool_names_default_empty` and dropped the `assert s.tool_names == []` line from `test_toml_string_values_default_when_absent` in `tests/shared/test_mcp_config.py`; removed the `tool_names` defaults from `_http_cfg`/`_subprocess_cfg` and the three validator tests (`test_empty_tool_name_raises`, `test_duplicate_tool_names_raises`, `test_empty_tool_names_list_is_valid`) in `tests/shared/test_mcp_config_validation.py`. All 67 of those tests pass. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-201200 | 20261120-201200 | **FINDING — wide blast radius, see escalation below.** The field removal breaks ~67 tests across ~15 test files (any test constructing `McpServerConfig(..., tool_names=...)` or reading `.tool_names`). Per the sibling fallout rows, cleanup of the direct consumers' tests is owned by `154254_14_...mcp_status.py` (test_agent_mcp_status.py) and `154254_15_...mode_classification.py` (test_mode_classification.py); tests owned by later procedures (`_11` test_mcp_tool_discovery, `_19` test_startup_mcp_starter, `_20` test_tool_registry, `_24` test_startup_validation) are handled there. However, ~9 broken files are NOT owned by any remaining procedure (test_mcp_health_posture, test_cmd_mcp, test_config_reload tool_names-diff, test_mcp_tool_discovery_posture_gate, test_failure_handling_policy_cross_cutting, and 4 integration tests). `154254_15` states non-Plan-listed file edits require a Plan amendment before they can be validated. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261120-201200 | 20261120-201200 | N/A: documentation is explicitly out of scope for this static-catalog-removal procedure. |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `scripts/shared/mcp_config.py`
