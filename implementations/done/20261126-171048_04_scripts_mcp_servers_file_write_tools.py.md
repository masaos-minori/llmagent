## Goal
- Generate the write tool schemas from the strict models with the shared generator instead of hand-maintained dictionaries (REQ-001, shared schema source).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the four hand-maintained `inputSchema` dicts at lines 17, 52, 101, 132.
- Out of scope: the model base swap (seq 03).

## Assumptions
- Verified in Step 3a: hand-maintained dicts confirmed at the cited lines.

## Design decisions
- Use `build_input_schema()` from `scripts/mcp_servers/request_contract.py` as the single schema source for all four write tools.

## Alternatives considered
- N/A: single-source change with no contract decision of its own.

## Implementation
### Target file
`scripts/mcp_servers/file/write_tools.py`

### Procedure
1. Import `build_input_schema` from `scripts/mcp_servers/request_contract.py`.
2. Replace each hand-maintained `inputSchema` dict with `build_input_schema(model)` for the corresponding request model.

### Method
- N/A: mechanical replacement; descriptions that exist only in the hand-written schema (not on the model fields) move to the model field descriptions in seq 03 or are dropped as presentation-only.

### Details
- The consistency tests in seq 20 pin that runtime and discovery schemas match after the switch.

## Compatibility considerations
- Hand-written schema text (per-property `description` strings not backed by model fields) is replaced by model-generated text; the tool contract for valid requests stays the same, extra fields are rejected after seq 03.

## Security considerations
- N/A: no secrets.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/file/test_file_schema_consistency.py -v` (seq 20); full `rules/toolchain.md` sequence.

## Completion criteria
- No hand-maintained `inputSchema` dict remains; all four write tool schemas are generated from the strict models; tests pass (AC-1).

## Out of Scope
- Model inheritance (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-175832 | 20261126-175832 | 4 hand-maintained inputSchema dicts replaced with build_input_schema(model); model imports added; docstring dependency line added. Files: scripts/mcp_servers/file/write_tools.py. Repeated operation extracted to tools/replace_hand_maintained_schemas.py (AGENTS.md rule 7), registered in tools/TOOL_DESCRIPTIONS.md |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-201535 | 20261126-201535 | ruff/mypy/lint-imports/tool-descriptions-sync/module-size-tools/reference-table pass; targeted tests 233 passed (no test change needed); known pending failure in test_file_write_health_posture.py owned by seq 12; full-suite run deferred to end of plan batch; Step 5/6: N/A: no docs/00_index.md task-scope mapping for scripts/mcp_servers/file/write_tools.py End-of-batch full-suite run passed (15774 passed, 5 skipped), resolving the pending supported_extensions failures; diff-cover 100% on changed lines; gates pass including tool-descriptions-sync. Intermittent flaky failures in 3 unrelated tests under -n logical, all pass serially. |

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
- **Requirement ID**: `REQ-001` (shared strict base and shared schema generator)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `scripts/mcp_servers/file/write_tools.py`