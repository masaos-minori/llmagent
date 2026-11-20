## Goal

Remove the now-obsolete `validate_routing_against_config()` references from the module docstring of `scripts/shared/tool_registry.py` (`REQ-004`, scope approved). The config-vs-registry drift path is eliminated: `validate_routing_against_config()` is removed by row 8 (`tool_routing_validation.py`) and its only production caller chain (`routing_drift.py` → `startup_validation.py`) by rows 16-17. Keep `validate_routing_against_live()` as the sole routing-drift validator named here.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- The current module docstring (lines 2-35) names `validate_routing_against_config()` in exactly two places: the parenthetical at lines 8-9 (`validate_routing_against_live()/validate_routing_against_config() in shared/tool_routing_validation.py`) and the bullet at line 33 (`- validate_routing_against_config(): validates config tool_names against registry`). Line 34 (`validate_routing_against_live()`) survives.
- NOTE: the Plan's original Evidence column cited "lines 8-9, 15-16, 33"; current source has NO `validate_routing_against_config()` mention at 15-16 (that area describes `tool_policy.classify_operation_type()` using `RuntimeToolRegistry`). Verified against current source.
- `validate_tool_names_match()` is a pure function taking `config_tool_names: list[str]` as a parameter; it does not read the removed `McpServerConfig.tool_names` field directly. Its only production caller was `validate_routing_against_config()` in `tool_routing_validation.py` (removed by row 8), so it becomes dead code but stays syntactically valid. Not touched by this row.
- No test asserts on this module's docstring text.

## Design decisions
- Delete the `validate_routing_against_config()` token from the line 8-9 parenthetical, leaving `validate_routing_against_live()`.
- Delete the line 33 bullet entirely, leaving the line 34 `validate_routing_against_live()` bullet.
- Leave all other docstring text (ownership model, ADR-003 citations, `RuntimeToolRegistry` authority notes) byte-for-byte.

## Alternatives considered
- Rewriting the whole docstring: rejected as scope creep; only the removed-function references are obsolete.
- Repurposing the docstring to describe the new registry manifest (row 9): out of scope; that is a separate documentation concern.

## Implementation
### Target file
`scripts/shared/tool_registry.py`

### Procedure
Remove the two `validate_routing_against_config()` mentions from the module docstring.

### Method
- Line 8-9: change
  ```
        (validate_routing_against_live()/validate_routing_against_config() in
        shared/tool_routing_validation.py) and config drift checks
  ```
  to
  ```
        (validate_routing_against_live() in
        shared/tool_routing_validation.py) and config drift checks
  ```
- Lines 33-34: delete the line 33 bullet, leaving
  ```
     - validate_routing_against_live(): validates live /v1/tools responses against registry
  ```

### Details
- Confirm no `validate_routing_against_config` token remains anywhere in the docstring (or elsewhere in the module — it is not defined here and must not be re-added).
- Do not touch `validate_tool_names_match()` (lines 128-154), `validate_live_tools_match()` (lines 156+), or the ADR-003 / ownership-model prose.

## Compatibility considerations
Docstring-only. No behavioral or API impact. The module still documents `validate_routing_against_live()` as the live routing-drift validator.

## Security considerations
N/A: documentation edit. The live routing-drift validator (`validate_routing_against_live()`) remains the documented authority; removing the config-source reference removes a weaker, now-absent drift path from the docs.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Grep `scripts/shared/tool_registry.py` for `validate_routing_against_config`: assert zero occurrences.
- Assert `validate_routing_against_live()` still appears (lines 8-9 area and the drift-detection bullet).
- Import the module and confirm `ToolRegistry.validate_tool_names_match` / `validate_live_tools_match` still exist and are callable (unchanged).
- Run `tests/shared/test_tool_registry.py` (row 20 scope row rewrites its config-drift classes; until then the live-match tests still pass).

## Completion criteria
`scripts/shared/tool_registry.py` contains no `validate_routing_against_config()` reference; `validate_routing_against_live()` remains documented; the module imports cleanly.

## Out of Scope
The `validate_routing_against_config()` removal (`tool_routing_validation.py`, row 8), the `check_routing_drift()` removals (`routing_drift.py` row 16, `startup_validation.py` row 17), the `McpServerConfig.tool_names` field removal (`mcp_config.py`, row 5), the `test_tool_registry.py` config-drift class removals (row 20), and the `config/tool_catalog.toml` registry (row 9).

### Observation (not implemented here)
The same docstring still references the removed field in three places that become stale under `REQ-003` (tool_names removal) but are OUT OF SCOPE for this row: line 21-22 ("Config mcp_servers.toml tool_names lists are optional; they are validated against the registry"), line 29 ("Config `tool_names` is NOT a routing input; it is drift validation metadata only."), and the `validate_tool_names_match` method (which validates "config tool_names"). These describe a `tool_names` source that this Plan removes. Recommend a follow-up cleanup of these lines in the same release if desired; they are not required to keep the build green and are outside row 18's stated scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Line numbers are against current source; re-verify if `agentcfg001` lands first. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Docstring-only; likely no edit needed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | See the Observation block above (out of scope). |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `scripts/shared/tool_registry.py`
