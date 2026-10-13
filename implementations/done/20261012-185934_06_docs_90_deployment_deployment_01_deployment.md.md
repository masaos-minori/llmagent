## Goal

Remove the clause stating that web-search's `/health` endpoint is admitted from a loopback
client without a token from the note after the environment file example
(`REQ-004`; AC-5).

## Scope

Only `docs/90_deployment/deployment_01_deployment.md`.

## Assumptions

- Line 178 is the sole mention of "loopback" in the document; the target clause sits inside
  the post-environment-file Note about web-search's shared token.

## Design decisions

- Delete only the admission clause; keep the surrounding sentences about the shared token and
  the retired browser token.

## Alternatives considered

N/A: a single clause removal in a documentation-only change.

## Implementation

### Target file

`docs/90_deployment/deployment_01_deployment.md`

### Procedure

In the Note (line 178), delete the clause
", and its `/health` endpoint is admitted from a loopback client without a token", leaving
"> **Note:** web-search authenticates with the same shared `MCP_WEB_SEARCH_AUTH_TOKEN` as
its `agent.toml` entry. The former separate browser token was retired; ...".

### Method

Edit line 178, then run the documentation checkers named below.

### Details

Line 178 currently reads:
"> **Note:** web-search authenticates with the same shared `MCP_WEB_SEARCH_AUTH_TOKEN` as
its `agent.toml` entry, and its `/health` endpoint is admitted from a loopback client
without a token. The former separate browser token was retired; ..." The retained sentences
(the shared token and the retired browser token) are unaffected and still accurate, as is
the trailing "(Explicit in code — ...)" reference.

## Compatibility considerations

N/A: removing the clause changes no other claim; the remaining note stays correct.

## Security considerations

Removes a misleading statement that implied an unauthenticated `/health` path.

## Rollback considerations

N/A: revert the commit.

## Validation plan

`uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
`check_docs_content_policy.py`, `check_docs_consistency.py --domain deployment`,
`check_docs_japanese.py` (per the Plan validation plan) — no issues.

## Completion criteria

The document contains no statement that `/health` is admitted without a token; the
documentation checkers report no issues.

## Out of scope

The MCP authentication document (`docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`), the
code, and the tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the documentation clause describing the loopback health admission | Completed | — | 20261013-175629 |  |
| 2 | Run the documentation checkers (`rules/toolchain.md`) | Completed | — | 20261013-175629 |  |

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
- **Requirement ID**: `REQ-004` (no document says `/health` is admitted without a token)
- **Source issue**: issues/20261012-185047_mcp006_remove-the-loopback-health-admission-from-the-shared-auth-middleware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-185654_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-185934
- **Related target files**: docs/90_deployment/deployment_01_deployment.md