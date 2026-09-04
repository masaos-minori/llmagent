# Unify Git MCP tool dispatch and enforce write protection for every advertised tool

## Priority
High

## Summary
Provide one auditable dispatch path for all Git MCP tools advertised by `/v1/tools`, so every
write tool passes through the same enforced protection pipeline without special-case bypasses
and every read-only tool remains callable.

## Background
No existing issue was found covering tool-dispatch consistency for the Git MCP server
specifically. This is filed alongside `gitauth`/`gitpipeline`, which address the protection
pipeline's internal correctness — this issue addresses whether every advertised tool actually
reaches that pipeline through one path.

## Problem
The server advertises a broader Git tool set than the visible HTTP handler map processes, while
a separate service dispatch helper also exists. Multiple dispatch paths can make enabled tools
unreachable or allow write operations to follow a path that does not apply the same protection
pipeline.

## Reason for Change
Tool advertisement, availability, validation, dispatch, and protection must share one canonical
registry, or a write tool could bypass the pipeline `gitauth`/`gitpipeline` are hardening.

## Implementation Intent
Compare every tool advertised by `/v1/tools` with the service dispatch table and HTTP call
path; select one canonical dispatch implementation and remove or redirect partial
alternatives; route all read-only tools through the canonical path without applying
write-only rejection rules; route all write tools through the same protection pipeline; reject
duplicate handlers, missing handlers, and unregistered tools during startup or automated
validation; add a contract test comparing advertised, enabled, registered, and callable tool
names.

## Target Files or Areas
- `scripts/mcp_servers/git/git_server.py`
- `scripts/mcp_servers/git/git_service.py`
- `scripts/mcp_servers/git/git_tools.py`
- `scripts/mcp_servers/git/repository_state.py`
- `tests/test_git_server.py`

Confirm file existence and responsibility before editing; modify only files required by the
verified implementation path.

## Required Changes
- Compare every tool advertised by `/v1/tools` with the service dispatch table and HTTP call path.
- Select one canonical dispatch implementation and remove or redirect partial alternatives.
- Route all read-only tools through the canonical path without applying write-only rejection rules.
- Route all write tools through the same protection pipeline (`gitpipeline`).
- Reject duplicate handlers, missing handlers, and unregistered tools during startup or automated validation.
- Add a contract test that compares advertised, enabled, registered, and callable tool names.

## Constraints
- Do not guess unverified behavior; record unresolved design decisions as Needs Confirmation.
- Preserve unrelated behavior.
- Do not introduce a second authorization or dispatch path — this issue's purpose is to eliminate an existing second path, not add another.
- Update documentation only after implementation and tests establish the current behavior.
- If investigation disproves an assumption in this issue, update the issue with evidence before implementation.

## Acceptance Criteria
- Every enabled tool returned by `/v1/tools` is callable through `/v1/call_tool`.
- Every advertised write tool uses the mandatory write-protection pipeline.
- Read-only tools are not reported as unknown because of a partial handler map.
- Unknown and disabled tools are rejected consistently.
- No unused alternative dispatch path remains capable of producing divergent behavior.
- The tool-contract test fails when advertisement and dispatch drift apart.

## Testing Expectations
Add focused unit tests for all changed rules. Add or update integration tests for the HTTP and
service dispatch paths. Confirm each new test fails before the fix and passes after the fix.
Run the complete existing Git MCP test suite and resolve regressions. Do not treat
documentation statements as proof of runtime behavior.

## Documentation Impact
Update `docs/04_mcp_04_05_git.md`'s tool inventory/dispatch description once implementation and
tests establish the current behavior.

## Out of Scope
- Protected-branch/ref authorization content itself (`gitauth`).
- The write-protection pipeline's internal stage correctness (`gitpipeline`).
- Repository-path containment and audit hardening (`gitpathaudit`).

## Dependencies
Write tools this issue routes into the protection pipeline depend on `gitpipeline`'s pipeline
being the correct, complete enforcement point — coordinate sequencing with that issue.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Before editing, enumerate the actual current advertised tool set, HTTP handler map, and service
dispatch table (`grep -rn "def.*tool\|dispatch" scripts/mcp_servers/git/git_server.py
scripts/mcp_servers/git/git_service.py`), since this issue's evidence may go stale. Do not
change tool names, arguments, or read-only tool behavior beyond what is needed to unify
dispatch.
