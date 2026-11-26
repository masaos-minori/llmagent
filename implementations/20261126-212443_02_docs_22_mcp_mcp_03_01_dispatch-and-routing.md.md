## Goal

Complete the single id-definition table, state Agent-managed replay, and add proving-test
references for the dedup ownership claims (REQ-001, REQ-003, AC-1, AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The key-separation paragraph is at `docs/22_mcp/mcp_03_01_dispatch-and-routing.md:61`
  (re-verified 20261126, Step 3a).
- The file already cites the layer-consistency tests at line 141; the missing references are
  the proving tests for the dedup ownership claims, not general test citations (Step 3a
  correction of the Step 2 claim).
- The single id table is defined in `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`
  (procedure 12); this document cites it rather than restating it (`skills/DESIGN.md`, no
  implementation-reference duplication).

## Design decisions
- Claims name the enforcement point (`dispatch_tool()` in `scripts/mcp_servers/dispatch.py`,
  `HttpTransport.call()`), the failure behavior, and the proving test.
- Replay is described as Agent-managed (`scripts/agent/tool_preparation.py` `ReplayDirective`);
  no text is written that implies LLM-controlled replay identity.

## Alternatives considered

N/A: the routing document already owns the transport-key description; only the missing
proving-test references are added.

## Implementation
### Target file
`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
### Procedure
- Extend the key-separation paragraph at line 61 with the Agent-managed replay statement and a
  pointer to the single id table in procedure 12's target file.
- Add proving-test references to the dedup ownership claims (the claims that name server-side
  dedup, lease acquisition, and terminal evidence).
### Method
- Verify each claim against `scripts/mcp_servers/dispatch.py` and `scripts/shared/mcp_dedup.py`
  before writing it; cite only tests that exist and pass.
### Details
- Proving tests: `tests/mcp_servers/test_mcp_dispatch.py` (store_error overlay path,
  `test_store_error_retryable_proceeds_non_retryable_fails_closed`),
  `tests/mcp_servers/test_mcp_dispatch_concurrency.py` (lease renewal and lost-lease
  behavior).

## Compatibility considerations

N/A: no pinned counts change; the file is shared with plan mcpai013, whose contribution is the
cross-scope-conflict note — judged compatible (Plan Risks).

## Security considerations

N/A: documentation-only change describing existing enforcement.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`
- `uv run pytest tests/mcp_servers/test_mcp_dispatch.py tests/mcp_servers/test_mcp_dispatch_concurrency.py`

## Completion criteria

- Every dedup ownership claim in the file names enforcement point, failure behavior, and a
  proving test that exists and passes; replay reads as Agent-managed.

## Out of Scope

- No behavior change; the governance items are not resolved here.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the docs checkers (`rules/tool-gates.md`) and the cited proving tests | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (single id table and Agent-managed replay), `REQ-003` (proving-test references)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
