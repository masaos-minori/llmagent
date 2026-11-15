## Goal

Revise the `ToolConfig.tool_definitions` comment in `config_dataclasses.py` to reflect that the static list is drift-validation and fixture-shape only, once the last runtime consumer is removed. (`REQ-004`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- This is a documentation-only change to a code-file comment; no behavior change.
- The two runtime readers removed by this Plan are `llm_turn_runner.py::_stream_llm()` (`REQ-001`) and the `/mcp status` + `/help` counts in `cmd_mcp.py` (`REQ-002`) + `registry.py` (`REQ-003`). This row MUST be implemented after those removals, or the comment will again be stale.
- The `tool_definitions` field itself stays (drift validation and test fixtures still use it).

## Design decisions
- Edit the existing comment at lines 204-213 in place: remove the "Still read at runtime in two places…" claim and restate that the field is retained only as the shape template for test fixtures.
- Keep the drift-validation reference intact: `agent/services/tool_validation.py::_check_tool_definitions` still reads this field at startup, which is why the field stays.
- Do not delete the field or change `__post_init__`.

## Alternatives considered
- Rewriting the comment from scratch: risk of dropping the already-correct drift-validation note; extend the existing block instead.

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`

### Procedure
1. After implementing `REQ-001`/`REQ-002`/`REQ-003` (no remaining runtime readers), edit the `tool_definitions` field comment at lines 204-213.
2. Replace the "Still read at runtime in two places: `llm_turn_runner.py::_stream_llm()` … and `cmd_mcp.py` + `registry.py`…" sentences with a statement that the field is no longer read at runtime and is retained solely for (a) startup drift validation against `/v1/tools` (`agent/services/tool_validation.py::_check_tool_definitions`) and (b) the shape template for test fixtures.
3. Keep the existing "Compatibility-only static tool schema list … sole runtime authority for tool validation/scheduling/approval/execution" framing.

### Method
Locate the `tool_definitions` field at line 214 with `grep -n "tool_definitions: list" scripts/agent/config_dataclasses.py`; edit the preceding comment block.

### Details
- Current comment (lines 204-213) explicitly lists two runtime readers; those readers are removed by sibling rows, so the comment must be updated here to avoid documenting a non-existent reader.

## Compatibility considerations
Comment-only; no API or behavior change.

## Security considerations
None.

## Rollback considerations
Revert the commit.

## Validation plan
- Read the comment confirms no runtime-reader claim remains.
- No linter/test impact (comment only).

## Completion criteria
- The `tool_definitions` field comment states it is drift-validation/fixtures only, with no runtime readers.

## Out of Scope
- Deleting the `tool_definitions` field (kept for drift validation and fixtures).
- Changes to drift validation (`tool_validation.py`) or fixtures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-184507 | 20261115-184507 | Depends on REQ-001/002/003 removing the runtime readers REQ-004: tool_definitions comment no longer claims runtime readers; ruff clean |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-184507 | 20261115-184507 | comment-only; ruff format+check clean |

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
- **Requirement ID**: `REQ-004` — revise ToolConfig.tool_definitions comment after runtime consumers gone
- **Source issue**: `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-050235_rtregistry001_runtime-registry-sole-authority.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-090843
- **Related target files**: `scripts/agent/config_dataclasses.py`