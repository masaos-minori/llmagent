# Remove direct MCP execution routes and require idempotency keys for side effects

## Priority
High

## Summary
Remove the operation-specific POST execution routes that coexist with `/v1/call_tool` on the MCP FastAPI servers, and reject keyless side-effecting `/v1/call_tool` requests before dispatch, so every accepted side effect goes through the common dispatch, dedup, and audit path.

## Background
Source: `memo-issue.md` (Issue B), re-verified against current source on 2026-11-11.

- `Explicit in code`: `read_server.py` registers 9 direct POST routes (`/list_directory`, `/list_directory_with_sizes`, `/directory_tree`, `/read_text_file`, `/read_media_file`, `/read_multiple_files`, `/search_files`, `/grep_files`, `/get_file_info`), `write_server.py` 4 (`/write_file`, `/edit_file`, `/create_directory`, `/move_file`), `delete_server.py` 2 (`/delete_file`, `/delete_directory`), `shell_server.py` 1 (`/shell_run`), and `rag_pipeline_server.py` 2 (`/rag_run_pipeline`, `/rag_debug_pipeline`). Each server also keeps `/health`, `/v1/tools`, and `/v1/call_tool`; the file-read server also has `GET /list_allowed_directories`.
- `Strongly implied by code`: the GitHub package declares 21 route decorators across four router modules (issues, pull requests, repository, file). That they are all POST execution routes is `Needs confirmation`.
- `Explicit in code`: the direct routes call service methods directly; the memo reports that they bypass shared dispatch, dedup, and `mcp_tool_exec` audit. This was not re-verified per route in this pass (`Needs confirmation`).
- `Documentation only` (memo): `dispatch_tool()` accepts `idempotency_key=None` by design, so a keyless side-effecting call executes without touching the overlay cache or durable store.

## Problem
Direct routes are a second execution contract that skips availability gating, argument validation, dedup, and shared audit. Separately, a keyless side-effecting call always executes, so retried or duplicated requests can repeat side effects, and changing only the dispatcher cannot fix this while direct routes remain.

## Reason for Change
These routes are a security and reliability bypass on the write, delete, shell, and GitHub paths. The change is also a breaking API removal and benefits from being decided before further MCP work builds on the routes.

## Implementation Intent
- Treat `/v1/call_tool` as the single execution path for every MCP server.
- Enforce the idempotency-key requirement at the shared request boundary (before dispatch) rather than inside `dispatch_tool()`, so read-only tools may stay keyless if the contract says so.
- Make the set of keyed tools come from the single side-effect classification defined by the sibling issue for tool classification, not from a second list.
- Add a route-inventory test per MCP app so reintroduction fails.

## Target Files or Areas
- `scripts/mcp_servers/file/read_server.py`, `write_server.py`, `delete_server.py`
- `scripts/mcp_servers/shell/shell_server.py`
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
- `scripts/mcp_servers/github/` (four router modules)
- `scripts/mcp_servers/server.py` and `scripts/mcp_servers/models.py` (candidate request-boundary enforcement points; `Needs confirmation`)
- Existing tests under `tests/mcp_servers/file/`, `shell/`, `rag_pipeline/`, `github/`
- Callers under `deploy/`, `scripts/ops/`, `scripts/admin/`, `.github/workflows/`, `tests/integration/` (search required)
- MCP API reference documents under `docs/22_mcp/`

## Required Changes
- Remove all operation-specific POST execution routes listed above.
- Keep only `/v1/tools`, `/v1/call_tool`, `/health`, and explicitly approved non-execution diagnostics.
- Decide whether `GET /list_allowed_directories` stays; it returns resolved path values and is a sensitive diagnostic, not a tool-execution exception.
- Add a shared request-boundary check: a side-effecting tool with an empty `X-Idempotency-Key` returns 400 or 422 before dispatch.
- Keep keyless read-only calls only if documented and tested.
- Migrate all deployment, operations, admin, CI, and integration-test callers to `/v1/call_tool`.
- Remove direct-route request and response models only after confirming `/v1/call_tool` handlers do not reuse them.
- Add route-inventory tests for every MCP FastAPI app.
- Update server module docstrings and MCP API references.

## Constraints
- Breaking change to the MCP HTTP surface; the repository policy is no backward-compatibility shims (`tools/check_compat_shims.py`).
- Do not change disabled-tool rejection semantics in this issue.
- Follow `rules/toolchain.md` Impact-radius check: measure test and caller references before removal.

## Acceptance Criteria
- No MCP FastAPI app registers an operation-specific execution POST route.
- A keyless side-effecting `/v1/call_tool` request is rejected before execution.
- Every accepted side effect passes availability gating, argument validation, common dispatch, dedup, and approved audit behavior.
- The `/list_allowed_directories` path-disclosure question has an explicit recorded decision.
- Route-inventory tests fail if an operation-specific route is reintroduced.
- No repository caller still uses a removed route (`rg` check recorded).

## Testing Expectations
- Route-inventory tests for each MCP FastAPI app.
- Tests for keyless side-effecting, keyless read-only, and keyed requests at `/v1/call_tool`.
- Update or remove tests under `tests/mcp_servers/` that call the removed routes.
- Run targeted pytest for `tests/mcp_servers/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run ruff check scripts/`, and `uv run python tools/check_docs_consistency.py --domain mcp`.

## Documentation Impact
Update `docs/22_mcp/` API references to remove the direct-route contract and document the idempotency-key requirement, the retained non-execution endpoints, and the failure behavior. Do not add literal ports or per-route catalogs (`skills/DESIGN.md` Docs content policy). Run `uv run python tools/generate_reference_table.py --check` if guarded blocks drift.

## Out of Scope
- Redefining the dedup store ownership or retry classes.
- RAG audit gap and MCP authentication ADR work.
- Changing the content of any tool's behavior behind `/v1/call_tool`.

## Dependencies
Duplicate and overlap check (2026-11-11): no open issue duplicates this one. Overlapping open plans:
- `plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md` (overlap: partial): make every WRITE_DANGEROUS MCP tool leave a server-side audit record (closing the `rag_delete_document` gap in `rag_pipeline_server.py` `call_tool`) and define MCP authentication once in a new ADR. It covers `/v1/call_tool` audit only; the direct routes and the keyless rule are not covered.
- `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md` (overlap: partial): classify `mcp_dedup.sqlite` as a disposable cache, fail closed for non-retryable tools when the store is lost, and split `config/mcp_dedup.toml` per process. It does not remove direct routes or require keys.

Ordering and other dependencies:
- Depends on `issues/20261111-163800_sideeffect001_side-effect-classification-central.md`: the key requirement needs the canonical set. Fix classification first or together.
- Sequence with `adrrev011` (same file `rag_pipeline_server.py`) and re-verify against `adrrev008` after it lands.

## Unresolved Questions
Decisions required from the maintainer before implementation:
- Decision 1 (`GET /list_allowed_directories`): keep it (and accept disclosure of resolved allowlist paths, treated as a sensitive diagnostic) or remove it.
- Decision 2 (keyless read-only calls): allow keyless read-only `/v1/call_tool` requests (documented and tested), or require a key for every call.
- Decision 3 (rejection status): 400 or 422 for a keyless side-effecting request.
- Decision 4 (deprecation): remove the routes immediately (assumed, per the no-shim policy) or allow a transition period.

Open facts (不明):
- 不明: whether the GitHub route decorators are all POST execution routes, and the exact caller inventory.
- 不明: which module is the best shared enforcement point (`server.py` or `models.py`).

## AI Implementation Instruction
- Remove only the routes and models confirmed unused by `/v1/call_tool`; do not refactor service methods.
- Stop and report if a caller of a removed route cannot be migrated.
- Do not add compatibility aliases.
- Do not implement out-of-scope items.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261111-163724
- **Related target files**: `scripts/mcp_servers/file/read_server.py`, `scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/file/delete_server.py`, `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/github/`, `scripts/mcp_servers/server.py`, `scripts/mcp_servers/models.py`
