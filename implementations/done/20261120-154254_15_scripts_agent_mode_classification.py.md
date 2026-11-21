## Goal

Stop reading the removed `McpServerConfig.tool_names` field in `scripts/agent/mode_classification.py` (`REQ-003`, fallout from row 5). `classify_and_inject_mode()` checks MDQ availability at lines 52-55 via `srv.tool_names`; once the field is gone that breaks. Derive MDQ availability from the RuntimeToolRegistry (`ctx.services_required.runtime_tools`) — the ADR-003 sole tool authority — and preserve the "fall back to RAG when MDQ tools are unavailable" behavior unchanged.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- Lines 52-55 (`mdq_available = any("search_docs" in (srv.tool_names or []) for srv in ctx.cfg.mcp.mcp_servers.values())`) are the only read of `.tool_names` in `mode_classification.py`.
- `ctx.services_required.runtime_tools` is a `RuntimeToolRegistry | None`, wired at `startup_validation.py:240`; `all_tools()` exposes `RuntimeTool.name`.
- The MDQ marker tool is named `"search_docs"` (current literal at line 53); confirm this name is stable before hard-coding it.

## Design decisions
- Replace the `srv.tool_names` comprehension with a registry membership check: MDQ is available iff `"search_docs"` is among the names returned by `ctx.services_required.runtime_tools.all_tools()`. When the registry is `None`, treat MDQ as unavailable (fail to RAG), matching the current empty-config behavior.
- Keep the surrounding `_mode_hint` / classification-validation flow (lines 49, 56-60, 61-66) unchanged.

## Alternatives considered
- Iterating `ctx.cfg.mcp.mcp_servers` and reading a manifest-derived per-server tool set: rejected as an extra loader dependency; the runtime registry already holds discovered tools and is the ADR-003 authority.
- Reading the required-capability manifest (row 9): the manifest declares *requirements*, not which surfaced tools provide them; the live registry is the correct source for "is MDQ actually available".

## Implementation
### Target file
`scripts/agent/mode_classification.py`

### Procedure
Replace the MDQ-availability comprehension (lines 52-55) with a RuntimeToolRegistry membership check.

### Method
Replace lines 52-55:
```python
        mdq_available = any(
            "search_docs" in (srv.tool_names or [])
            for srv in ctx.cfg.mcp.mcp_servers.values()
        )
```
with:
```python
        _mdq_names = (
            {t.name for t in ctx.services_required.runtime_tools.all_tools()}
            if ctx.services_required.runtime_tools is not None
            else set()
        )
        mdq_available = "search_docs" in _mdq_names
```

### Details
- Confirm no `.tool_names` reference remains in `mode_classification.py`.
- Do not change `resolve_mode`, `_mode_hint`, or `_validate_classification`.
- The `ctx.cfg.mcp.mcp_servers` iteration disappears; ensure nothing else in the file reads that mapping for tool presence.

## Compatibility considerations
Behavior-preserving by intent. MDQ mode still falls back to RAG when `"search_docs"` is not surfaced, now judged by discovered tools rather than configured `tool_names`. A server undiscoverable at the time of classification degrades to RAG (safe default). No public API change.

## Security considerations
Fail-safe preserved: when MDQ availability cannot be confirmed (registry absent), classification falls back to RAG rather than asserting MDQ. No security-relevant routing change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run `tests/agent/test_mode_classification.py`. **This file currently constructs `McpServerConfig(..., tool_names=[...])` at line 25 and drives MDQ availability through that field; it will break once `tool_names` is removed and must be updated to set `ctx.services_required.runtime_tools` (a `RuntimeToolRegistry` containing a `"search_docs"` tool) instead.** NOTE: `tests/agent/test_mode_classification.py` is **not** listed in this Plan's `Implementation Target Files`, so updating it is an *additional target file discovery* per `rules/workflow-lifecycle.md` — it requires a Plan amendment (new row) before this fallout row can be validated to completion. Also consumer-scan any other test constructing `McpServerConfig(..., tool_names=...)`.

## Completion criteria
`mode_classification.py` contains no `.tool_names` reference; MDQ availability is derived from the RuntimeToolRegistry; the RAG fallback on unavailable MDQ still fires.

## Out of Scope
The `McpServerConfig.tool_names` field removal (`mcp_config.py`, row 5), the server-tier derivation in `mcp_status.py` (fallout row 14), the required-capability model (`mcp_tool_discovery.py`, row 7), the static registry (`config/tool_catalog.toml`, row 9), and the (non-Plan-listed) `tests/agent/test_mode_classification.py` edit described above.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120 | 20261120 | Replaced the MDQ-availability comprehension (lines 52-55) with a RuntimeToolRegistry membership check: `_mdq_names = {t.name for t in ctx.services_required.runtime_tools.all_tools()} if ctx.services_required.runtime_tools is not None else set()`; `mdq_available = "search_docs" in _mdq_names`. No `.tool_names` reference remains; `resolve_mode`/`_mode_hint`/`_validate_classification` unchanged. |
| 2 | Add or update tests per Validation plan | Completed | 20261120 | 20261120 | `tests/agent/test_mode_classification.py` is an additional-target-file Fallout edit (plan amended 2026-11-20: new row + amendment note added to `Implementation Target Files`). Rewrote `_make_ctx` to drop `McpServerConfig(..., tool_names=...)` and drive MDQ availability through a real `RuntimeToolRegistry` (or `None`) via `ctx.services_required.runtime_tools`. Consumer scan confirmed no other test builds a real `McpServerConfig(..., tool_names=...)` (the two remaining hits use `MagicMock`). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120 | 20261120 | ruff format/check clean (prod + test); mypy clean; target 7 pass; full-suite diff vs baseline IDENTICAL (zero new failures). Plan amendment verified: `audit_plan_target_paths.py` 0 findings, `check_plan_target_overlaps.py` no findings. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Test-only + production fix; docs rows are out of scope. |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `scripts/agent/mode_classification.py`
