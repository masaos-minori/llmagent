## Goal

Drop the now-obsolete `validate_routing_against_config()` reference from the validation-functions summary in `docs/40_shared/shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` (`REQ-004`, scope approved). The config-vs-registry drift path is eliminated: `validate_routing_against_config()` is removed by row 8 (`tool_routing_validation.py`) and its only production caller chain (`routing_drift.py` → `startup_validation.py`) by rows 16-17. Keep `validate_routing_against_live()` and `all` as the surviving validators named here.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- Current source has ONE reference: the "Validation functions" paragraph at line 48 reads:
  ```
  `validate_routing_against_config`/`live`/`all` return an empty dictionary if no drift is detected.
  ```
- After removing the config member, the surviving validators named in this sentence are `live` and `all`.

## Design decisions
- Delete the `/config` member from the slash-list, leaving `` `validate_routing_against_live`/`all` return an empty dictionary if no drift is detected. ``
- Leave all other prose byte-for-byte.

## Alternatives considered
- Rewriting the whole "Validation functions" section: rejected as scope creep; only the removed-function member is obsolete.

## Implementation
### Target file
`docs/40_shared/shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`

### Procedure
Remove the `/config` member from the validation-functions slash-list on line 48.

### Method
Replace:
```
`validate_routing_against_config`/`live`/`all` return an empty dictionary if no drift is detected.
```
with:
```
`validate_routing_against_live`/`all` return an empty dictionary if no drift is detected.
```

### Details
- Confirm no `validate_routing_against_config` token remains anywhere in the document.
- Confirm `validate_routing_against_live` and `all` still appear in the sentence.
- Do not touch the surrounding bullet list (L30-31) or other sections.

## Compatibility considerations
Doc-only. No behavioral or API impact. The summary still lists `validate_routing_against_live()` and `all` as the surviving validators.

## Security considerations
N/A: documentation edit. The live routing-drift validator (`validate_routing_against_live()`) remains the documented authority; removing the config-source reference removes a weaker, now-absent drift path from the docs.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Grep `docs/40_shared/shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` for `validate_routing_against_config`: assert zero occurrences.
- Assert `validate_routing_against_live` and `all` still appear in the "Validation functions" sentence.

## Completion criteria
`shared_03_02...md` contains no `validate_routing_against_config` reference; `validate_routing_against_live`/`all` remain the documented validators.

## Out of Scope
The `validate_routing_against_config()` removal (`tool_routing_validation.py`, row 8), the `check_routing_drift()` removals (`routing_drift.py` row 16, `startup_validation.py` row 17), the `McpServerConfig.tool_names` field removal (`mcp_config.py`, row 5), the `tool_registry.py` docstring edit (row 18), the `mcp_03_02_tool-registry.md` table-row correction (row 21), and any `tool_names` prose elsewhere in this doc. Those describe a `tool_names` source this Plan removes but are outside row 22's stated scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120 | 20261120 | Deleted the `/config` member from the validation-functions slash-list on L48, leaving `` `validate_routing_against_live`/`all` return an empty dictionary if no drift is detected. `` No `validate_routing_against_config` token remains; `validate_routing_against_live` and `all` still present. |
| 2 | Add or update tests per Validation plan | N/A | — | — | Doc-only; no tests. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120 | 20261120 | Grep confirms zero `validate_routing_against_config` occurrences; `validate_routing_against_live`/`all` remain. Full-suite regression diff DEFERRED to the `_16`–`_27` coupled-unit final check. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261120 | 20261120 | This is the doc edit itself. Out-of-scope `tool_names` prose left untouched per row scope. |

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
- **Related target files**: `docs/40_shared/shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`
