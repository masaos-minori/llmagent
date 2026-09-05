## Goal
Add a contract test comparing `TOOL_LIST`'s advertised tool names, `/v1/tools`'
enabled tool names, `GitService.get_dispatch_table()`'s registered names, and the set
of tool names `POST /v1/call_tool` can actually reach — failing if any two sets
diverge (`REQ-007`, `AC-6`), and resolving `UNK-01` in favor of this contract test as
the automated-validation option (no separate startup-time duplicate/missing-handler
check added elsewhere, per the Plan's Assumptions).

## Scope
- In scope: this file only — one new contract test (and a small fixture/import
  addition if a `TestClient` is needed to exercise `/v1/call_tool` live).
- Out of scope: `TOOL_LIST` itself (`scripts/mcp_servers/git/git_tools.py`, Reference
  File, no change); `get_dispatch_table()` (`scripts/mcp_servers/git/git_service.py`'s
  own procedure document implements the read/write split, not this table's contents,
  which are already correct); per-tool HTTP behavior tests (`tests/mcp_servers/git/
  test_git_security_compliance.py`'s own procedure document).

## Assumptions
- This file currently has no `TestClient`/FastAPI import (confirmed: only `GitService`/
  `RepositoryState` imports at the top, no `fastapi.testclient` import) — the contract
  test needs one to assert what `/v1/call_tool` can "actually reach", following the
  same `TestClient(git_server.app)` pattern `tests/mcp_servers/git/
  test_git_security_compliance.py` already uses (its `client` fixture, module scope).
- "Actually reach" (per `REQ-007`'s wording) means: for each tool name in the union of
  all four sets, a `POST /v1/call_tool` call with that name does not return
  `"Unknown tool: {name}"` — not that the call succeeds end-to-end (that would require
  a real repo fixture per tool, redundant with `test_git_security_compliance.py`'s
  per-tool tests). A minimal probe (e.g. an intentionally-invalid `repo_path` that
  still reaches dispatch before failing for an unrelated reason) is sufficient to
  distinguish "unknown tool" from "known tool, rejected for another reason".

## Design decisions
- Compute all four sets programmatically at test time (`{t["name"] for t in TOOL_LIST}`, `{t["name"] for t in build_tools_response(...)-equivalent enabled set}` via a live `GET /v1/tools` call, `set(GitService(...).get_dispatch_table().keys())`, and the "reachable via `/v1/call_tool`" set built by probing each name) rather than hardcoding the expected 10 names — so the test continues to catch drift if a tool is added or removed later, per `REQ-007`'s "failing if any two sets diverge" (not "failing if not exactly these 10").
- Build the "enabled via `/v1/tools`" set from a config with non-empty `allowed_repo_paths` and `read_only=False`, so all 10 tools are enabled rather than gated off by `_git_tool_availability()` — the contract test's purpose is dispatch-table consistency, not availability-gating (already covered by `test_tools_endpoint.py`).

## Alternatives considered
- Assert dispatch reachability via `GitMCPServer.dispatch()` instead of `/v1/call_tool`: rejected — `git_server.py`'s own procedure document removes `GitMCPServer.dispatch()` entirely (`REQ-006`); the contract test must exercise the actual live HTTP path this Plan makes canonical.
- A pure set-equality assertion on `TOOL_LIST` vs. `get_dispatch_table()` without probing `/v1/call_tool` live: rejected — this would not catch the exact bug this Plan fixes (both sets already had all 10 names before this Plan; the drift was that the *live HTTP path* didn't reach 7 of them), so it would not fail against the pre-fix code as `AC-6` requires.

## Implementation
### Target file
`tests/mcp_servers/git/test_mcp_git.py`

### Procedure
1. Add imports: `from fastapi.testclient import TestClient`, `from mcp_servers.git import git_tools` (for `TOOL_LIST`), `from mcp_servers.git import git_server` (for the FastAPI `app` and `build_tools_response`/`_annotate_tool`, or simply drive `/v1/tools` via `TestClient` rather than calling internals directly).
2. Add a fixture (module- or test-scoped) constructing a `TestClient` against a `GitService`/`GitConfig` with non-empty `allowed_repo_paths` and `read_only=False` — mirror `test_git_security_compliance.py`'s `client` fixture construction, adjusted for a config where all 10 tools are enabled.
3. Add `TestDispatchContractTest` (or similar) with one test:
   - `advertised = {t["name"] for t in TOOL_LIST}`
   - `enabled = {t["name"] for t in client.get("/v1/tools").json()["tools"] if t["enabled"]}` (adjust field access to the actual `/v1/tools` response shape — confirm via a quick read of `build_tools_response`'s return structure during implementation)
   - `registered = set(GitService(...).get_dispatch_table().keys())`
   - `reachable = {name for name in advertised if client.post("/v1/call_tool", json={"name": name, "args": {"repo_path": "/nonexistent"}}).json()["result"] != f"Unknown tool: {name}"}`
   - Assert `advertised == enabled == registered == reachable`.
4. Confirm this test fails against the pre-change `git_server.py` (where `reachable`
   would be only `{git_checkout, git_pull, git_push}`, 7 short of `advertised`) —
   per `AC-6`, verify this either by running the test before `git_server.py`'s
   procedure document lands, or by asserting it structurally could not pass against
   the current 3-tool `handlers` dict (documented reasoning suffices if running
   pre-fix is impractical in the same session).

### Method
The test builds all four sets independently from their own sources of truth
(`TOOL_LIST`, a live `/v1/tools` call, `get_dispatch_table()`, and per-name
`/v1/call_tool` probes) and asserts set equality — any future drift between
advertisement, availability-gating, the dispatch table, or the live HTTP path fails
this single test, satisfying `REQ-007`/`UNK-01`'s "reject ... via automated
validation" resolution.

### Details
- Use a `repo_path` value guaranteed to fail *after* dispatch (e.g. `/nonexistent`,
  which `_resolve_repo_path`/`is_within_allowed_paths` should reject with a message
  distinct from `"Unknown tool: {name}"`) so the probe distinguishes "tool not found"
  from "tool found, repo invalid" — confirm the exact rejection message during
  implementation does not coincidentally match the `"Unknown tool: ..."` string.
- If `/v1/tools`'s response shape nests tool entries differently than assumed above
  (e.g. under a `"tools"` key vs. top-level list), adjust the parsing accordingly —
  this is a Non-blocking evidence gap; confirm the actual shape via
  `build_tools_response`'s definition (`shared/` or `mcp_servers/` helpers) at
  implementation time.

## Compatibility considerations
- Purely additive; no existing test in this file changes.

## Security considerations
- N/A: this is a test file; the contract test verifies but does not itself enforce
  security behavior. The `TestClient` fixture must use a config with a
  non-privileged, test-only `allowed_repo_paths` entry, consistent with this file's
  and `test_git_security_compliance.py`'s existing test-repo conventions.

## Rollback considerations
- Purely additive; revertible via `git revert` alone.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_mcp_git.py -v` — new contract test passes
  once `git_server.py`'s and `git_service.py`'s procedure documents land.
- `uv run pytest tests/mcp_servers/git/ -v` (full suite) — no new failures.

## Completion criteria
- One test asserts `advertised == enabled == registered == reachable` for all git
  tool names, computed from live sources rather than hardcoded (AC-6).
- The test is confirmed to fail against the pre-`REQ-002` code (3-tool `handlers`
  dict) and pass after.

## Out of scope
- Per-tool behavioral HTTP tests for the 7 newly-reachable tools —
  `tests/mcp_servers/git/test_git_security_compliance.py`'s own procedure document.
- `_run_tool()`'s read/write split — `scripts/mcp_servers/git/git_service.py`'s own
  procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestClient` fixture and imports (Procedure steps 1-2) | Pending | — | — | |
| 2 | Add the four-set contract test (Procedure step 3) | Pending | — | — | |
| 3 | Confirm fail-before/pass-after against `REQ-002`'s fix (Procedure step 4) | Pending | — | — | |
| 4 | Run validation plan (this file + full suite) | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (contract test), resolving `UNK-01` (automated-validation choice)
- **Source issue**: issues/20260902-144910_gitdispatch_unify_git_mcp_tool_dispatch_and_write_protection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-191458_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-203805
- **Related target files**: tests/mcp_servers/git/test_mcp_git.py
