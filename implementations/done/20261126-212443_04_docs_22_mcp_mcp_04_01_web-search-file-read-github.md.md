## Goal

Confirm the GitHub read-authorization, search-scope, and file-read control statements against
current source, and state the symlink and traversal-limit policy as failure behavior
(REQ-002, AC-1).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The symlink policy and traversal-limit reporting are already present at
  `docs/22_mcp/mcp_04_01_web-search-file-read-github.md:76-77` (Step 3a correction: the Step 2
  claim that the file has no symlink/traversal-limit policy is stale), so this row confirms and
  links them rather than adding them.
- The proving tests named by the Plan for this row do not exist yet:
  `tests/mcp_servers/github/test_github_security_compliance.py` is a pending output of
  procedures `implementations/20261126-205430_03` and `_04` (mcpai010). The claim must cite the
  test at execution time, after those procedures land; if the file is still absent, cite the
  existing GitHub security tests instead (`tests/mcp_servers/github/test_service_security.py`,
  `test_github_security_validation.py`).

## Design decisions
- Each claim names the enforcement point (`github_service_security.py`, `_get_repo()`,
  `_assert_allowed_repo()`), the failure behavior, and the proving test.
- Search scope is described as enforced at query-construction time, not as a post-call filter.

## Alternatives considered

N/A: the section already describes the implemented controls; only the proving-test references
and the failure-behavior wording are added.

## Implementation
### Target file
`docs/22_mcp/mcp_04_01_web-search-file-read-github.md`
### Procedure
- Verify the read-authorization, search-scope, and file-read control statements against
  `scripts/mcp_servers/github/github_service_security.py` and the file-read traversal code.
- Add the proving-test reference to each claim this sweep changes, including the symlink and
  traversal-limit failure behavior at lines 76-77.
### Method
- Confirm each enforcement point with `rg` before writing; do not restate a claim that already
  conforms (`skills/DESIGN.md`, no implementation-reference duplication).
### Details
- Proving tests: `tests/mcp_servers/file/test_read_service.py`
  (`test_resolve_safe_rejects_symlink_outside_allowed`, `test_resolve_safe_rejects_traversal_etc_shadow`);
  the mcpai010 GitHub compliance test once it lands.

## Compatibility considerations

N/A: documentation-only change; the file is shared with plan mcpai013, whose contribution is
the cross-scope-conflict note — judged compatible.

## Security considerations

N/A: the document describes existing security controls; no control is changed.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`
- `uv run pytest tests/mcp_servers/file/test_read_service.py`

## Completion criteria

- Every security claim in the file names enforcement point, failure behavior, and a proving test
  that exists and passes at execution time.

## Out of Scope

- No read-tool scope-declaration change (mcpai013 owns the scope vocabulary).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-234310 | 20261126-234310 | claims confirmed against source, no stale claim found; proving tests cited (mcpai010 compliance test now exists, so the assumption's fallback was not needed) |
| 3 | Run the docs checkers (`rules/tool-gates.md`) and the cited proving tests | Completed | 20261126-234310 | 20261126-234310 | docs checkers pass; test_read_service.py 115 passed; compliance test 10 passed |

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
- **Requirement ID**: `REQ-002` (GitHub read authorization, search scope, file-read controls)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`