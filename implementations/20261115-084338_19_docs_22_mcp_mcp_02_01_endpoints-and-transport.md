## Goal

Update `docs/22_mcp/mcp_02_01_endpoints-and-transport.md` to remove the direct-route contract and document the `/v1/call_tool`-only execution path, the idempotency-key requirement, the retained non-execution endpoints, and the `/list_allowed_directories` decision. (`REQ-008`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The current API reference under `docs/22_mcp/` describes the direct POST execution routes that this Plan removes; those sections must be deleted.
- The doc must record that `/v1/call_tool` is the single execution path and that side-effecting calls require `X-Idempotency-Key` (REQ-004), while read-only keyless calls stay documented (UNK-02).
- The `/list_allowed_directories` disposition (AC-4) is a maintainer decision; the doc records whatever decision is recorded, and must not invent one.

## Design decisions
- Follow `skills/DESIGN.md` Docs content policy: do not add literal ports or per-route catalogs. Document the execution contract, not a route-by-route listing.
- Keep the reference in sync with any guarded/generated blocks via `tools/generate_reference_table.py --check` if the doc feeds a generated table.

## Alternatives considered
- Leaving the direct-route section as deprecated: rejected — the routes are removed, not deprecated (no-shim policy).

## Implementation
### Target file
`docs/22_mcp/mcp_02_01_endpoints-and-transport.md`

### Procedure
1. Remove every section describing the operation-specific direct POST execution routes (`/list_directory`, `/write_file`, `/shell_run`, `/get_file_contents`, etc.) now that they no longer exist.
2. Document `/v1/call_tool` as the single execution path for all tools.
3. Document the idempotency-key requirement for side-effecting calls (REQ-004) and the retained non-execution endpoints (`/v1/tools`, `/health`, plus the recorded `/list_allowed_directories` disposition).
4. Run the doc consistency checkers named in `routing.md` for the mcp domain.

### Method
- Locate direct-route sections with `grep -n -E "/(shell_run|write_file|get_file_contents|rag_run_pipeline)" docs/22_mcp/mcp_02_01_endpoints-and-transport.md` and remove them.
- Update the endpoint-summary prose to the `/v1/call_tool`-only contract.
- Run `uv run python tools/generate_reference_table.py --check` (if a guarded block depends on this doc) and `uv run python tools/check_docs_consistency.py --domain mcp`.

### Details
- The doc must not claim a `/list_allowed_directories` decision that has not been made; if AC-4 is unresolved, mark that section as pending the decision rather than fabricating one.

## Compatibility considerations
Documentation-only; no production impact.

## Security considerations
Documents the security-relevant idempotency-key requirement so consumers know side-effecting calls now require a key.

## Rollback considerations
Revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain mcp` passes.
- `uv run python tools/generate_reference_table.py --check` passes if a guarded block depends on this doc.
- No remaining mention of a removed direct route.

## Completion criteria
- The direct-route contract is removed from the reference; `/v1/call_tool` is documented as the sole execution path with the idempotency-key requirement and retained non-execution endpoints.

## Out of Scope
- Adding literal ports or per-route catalogs (`skills/DESIGN.md` Docs content policy).
- Deciding the `/list_allowed_directories` disposition (AC-4); the doc records the decision, does not make it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-008` — update the MCP API reference for the `/v1/call_tool`-only path and idempotency-key requirement
- **Source issue**: `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-045455_mcproute001_remove-direct-mcp-routes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084338
- **Related target files**: `docs/22_mcp/mcp_02_01_endpoints-and-transport.md`
