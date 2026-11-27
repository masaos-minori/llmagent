## Goal

Run the CI/CD section consistency sweep against current source (REQ-002, REQ-008, AC-1, AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The file is 6610 B and its scope is the CI/CD server section per the document map recorded by
  procedure 01.
- The sweep is confirmation-only where the section already matches the implementation; only
  contradicting statements are rewritten.

## Design decisions
- Claims that name an enforcement point, failure behavior, and proving test are left untouched
  (`skills/DESIGN.md`, no implementation-reference duplication).
- The four-layer tool-definition consistency claim is verified against the layer-consistency
  test rather than restated.

## Alternatives considered

N/A: the sweep is scoped by the document map; no alternative section assignment.

## Implementation
### Target file
`docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`
### Procedure
- Check the CI/CD section's configuration, allowlist, and HTTP-client lifecycle statements
  against `scripts/mcp_servers/cicd/` and correct any statement that contradicts the code.
- Add a proving-test reference for each claim the sweep changes.
### Method
- Locate the section with grep, read the limited range, and verify each named symbol before
  writing it.
### Details
- Proving test: `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py`
  (`test_tool_constants_set_matches_schema`, `test_tools_registered_in_registry`).

## Compatibility considerations

N/A: the file is also targeted by plan mcpci001; judged compatible — that plan writes the
credential and schema contract facts, this row sweeps them afterward.

## Security considerations

N/A: documentation-only change describing existing controls.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`
- `uv run pytest tests/mcp_servers/cicd/test_tool_server_layer_consistency.py`

## Completion criteria

- No CI/CD statement contradicts the implementation, and every claim the sweep changed cites a
  proving test that passes.

## Out of Scope

- No CI/CD behavior change; the credential-config contract belongs to plan mcpci001.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-234310 | 20261126-234310 | confirmation-only sweep: config keys, allowlist guards (_assert_allowed_repo/_validate_and_parse_repo/_assert_allowed_workflow in cicd_service_guards.py), job-count and max_log_size_kb limits, dry_run, health, audit layers all match source; no contradicting statement, no file change |
| 3 | Run the docs checkers (`rules/tool-gates.md`) and the cited proving test | Completed | 20261126-234310 | 20261126-234310 | docs checkers pass; layer-consistency test 62 passed |

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
- **Requirement ID**: `REQ-002` (server-section consistency), `REQ-008` (terminology)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`