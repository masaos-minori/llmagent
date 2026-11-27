## Goal

Run the MDQ enforcement and lockdown section consistency sweep against current source
(REQ-002, REQ-008, AC-1, AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The file is 6128 B and its scope is the MDQ enforcement and lockdown section per the document
  map recorded by procedure 01.
- The sweep is confirmation-only where the section already matches the implementation.

## Design decisions
- Enforcement claims name the gate (file and function), the failure behavior, and the proving
  test; conforming claims are left untouched.
- The config-gate claim at line 69 is verified against `grep_docs()` before restating it.

## Alternatives considered

N/A: the sweep is scoped by the document map.

## Implementation
### Target file
`docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`
### Procedure
- Check the enforcement and lockdown statements against `scripts/mcp_servers/mdq/` and correct
  any statement that contradicts the code.
- Add the proving-test reference for each claim the sweep changes.
### Method
- Locate each claim with grep, read the limited range, and verify the named symbol before
  writing it.
### Details
- Proving tests: `tests/mcp_servers/mdq/test_mdq_path_jail.py`
  (`test_denied_path_raises`, `test_dotdot_traversal_denied`, `test_symlink_escape_denied`),
  `tests/mcp_servers/mdq/test_mdq_read_authorization.py`.

## Compatibility considerations

N/A: documentation-only change; the boundary section is swept by procedure 10.

## Security considerations

N/A: documentation-only change describing existing enforcement.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`
- `uv run pytest tests/mcp_servers/mdq/test_mdq_path_jail.py tests/mcp_servers/mdq/test_mdq_read_authorization.py`

## Completion criteria

- No enforcement or lockdown statement contradicts the implementation, and every claim the sweep
  changed cites a proving test that passes.

## Out of Scope

- No MDQ enforcement behavior change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-234310 | 20261126-234310 | confirmation-only sweep: authorize_path (auth.py:19, empty allowlist denies all, Path.resolve normalization), tool coverage (outline/get_chunk/_validate_paths/_resolve_grep_paths/search), silent exclusion vs explicit rejection, stats bypass, Bearer-before-path order, enable_grep gate, bm25-only mode all match source; no contradiction. Added proving-test references to the four path-authorization claims. |
| 3 | Run the docs checkers (`rules/tool-gates.md`) and the cited proving tests | Completed | 20261126-234310 | 20261126-234310 | docs checkers pass; 15 passed (path_jail + read_authorization) |

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
- **Requirement ID**: `REQ-002` (enforcement consistency), `REQ-008` (terminology)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`