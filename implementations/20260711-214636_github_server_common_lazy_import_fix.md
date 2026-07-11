# Implementation Procedure: github/server_common.py — lazy imports to break circular import

Source plan: `plans/20260711-195005_plan.md` — Phase 2 (Core Logic Implementation)

## Goal

Fix the GitHub MCP server startup failure caused by a circular import between `server.py` and `server_common.py`, by converting the module-level `_service`/`logger` imports in `server_common.py` into lazy, function-local imports.

## Scope

**In:**
- `scripts/mcp_servers/github/server_common.py`: remove the module-level `from mcp_servers.github.server import _service, logger` import; add equivalent lazy imports inside `_get_service()` and `_info()`.

**Out:**
- No change to any endpoint function signature in `server_file.py`, `server_issues.py`, `server_pull_requests.py`, `server_repository.py` — their public API is unaffected since `_get_service()`/`_info()`'s external behavior does not change.
- No `shared_state.py` creation — explicitly out of scope per the plan (a longer-term architectural alternative, not needed for this fix).
- No CI circular-import detection addition — separate initiative.
- No fix for a missing `GITHUB_TOKEN` — a distinct, separate issue (see sibling plan `plans/20260711-200907_plan.md` / its companion doc for the CICD server's token, a different server).

## Assumptions

1. Python's module-level import cache makes a lazy (function-local) import negligible in cost after the first call — standard Python behavior, not a new consideration.
2. The existing `# noqa: PLC0415` suppression on the original module-level import line is valid and should be preserved on the new lazy-import lines (PLC0415 flags imports not at the top of the file; moving the import inside a function is exactly the pattern this suppression already anticipates).
3. `_service` and `logger` are guaranteed to be initialized (in `server.py`) before any endpoint function that calls `_get_service()`/`_info()` is invoked at runtime — this is the existing runtime guarantee the plan relies on; this fix does not change that guarantee, only when the import binding is resolved (at call time instead of at module-load time), which is exactly what avoids the circular-import failure.
4. Per the plan's Assumption 4, this fix targets both the production deployment path (`/opt/llm/scripts/mcp_servers/github/server_common.py`) and the source repository copy (`/home/sugimoto/llmagent/...` or, in this repo's working directory, the equivalent path under `scripts/mcp_servers/github/`) — confirmed by the plan these are separate, non-git-linked file systems; both need the identical edit, deployed independently via the standard deploy workflow (`deploy/deploy.sh`).

## Implementation

### Target file

`scripts/mcp_servers/github/server_common.py`

### Procedure

1. Read the current file to locate the exact module-level import line: `from mcp_servers.github.server import _service, logger  # noqa: PLC0415` (or similar — confirm exact current wording/line number, since the plan's own Phase 1 calls for re-verifying this before editing).
2. Remove that module-level import line entirely.
3. Inside `_get_service()`'s function body (as its first statement, or immediately before first use of `_service`), add:
   ```python
   from mcp_servers.github.server import _service  # noqa: PLC0415
   ```
4. Inside `_info()`'s function body (as its first statement, or immediately before first use of `logger`), add:
   ```python
   from mcp_servers.github.server import logger  # noqa: PLC0415
   ```
5. If either function already has other lazy imports at its top, place the new import there consistently, keeping one import per line and preserving existing suppression-comment style.

### Method

Two localized, single-line import relocations (module scope → function scope) in one file. No signature, return type, or control-flow change in either function.

### Details

- Do not remove the `# noqa: PLC0415` suppression — it remains valid and necessary for the new lazy-import lines.
- If `_info()` is called before `logger` is guaranteed to be set (per Assumption 3), consider a defensive `if logger is None: return` guard per the plan's Risk table — but only add this if the verification step (Phase 3) actually observes a `None`-logger failure; do not add speculative guards not called for by an observed failure.
- Apply the identical change to both the production (`/opt/llm`) and repository (source tree) copies of this file, per Assumption 4 — treat them as two independent edits requiring two independent deploys, not a single shared file.

## Validation plan

Filtered from the plan's Validation Plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Import test | `uv run --directory /opt/llm python -c "from mcp_servers.github.server_common import _get_service, _info; print('OK')"` | No `ImportError` |
| Startup test | `cd /opt/llm && uv run python scripts/mcp_servers/github/server.py &` | Server starts without crash |
| Health endpoint | `curl http://127.0.0.1:8006/health` | HTTP 200 with service info |
| Tool definitions | `curl http://127.0.0.1:8006/v1/tools` | Returns tool list JSON |
| Manual | Restart via agent REPL, confirm watchdog stops reporting "exited early" | No more early-exit warnings for the GitHub MCP server |
