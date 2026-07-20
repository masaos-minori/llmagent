# Implementation procedure: `scripts/shared/runtime_tool_registry.py` (drop stale "ToolRegistry remains sole routing authority" docstring sentence)

Source plan: `plans/done/20260720-134821_plan.md`, Implementation step Phase 2 (item 3, second half).

Prior doc `implementations/done/20260717-203200_runtime_tool_registry.py.md` is this file's original
creation doc (requirement 03, base `RuntimeToolRegistry` class design) — read in full and confirmed
it predates and does not address today's docstring correction; it is the reason the stale sentence
exists in the first place, not a fix for it. This is a new document.

## Goal

Remove/rewrite the module docstring sentence stating "`shared.tool_registry.ToolRegistry` remains
the sole routing authority for now, per that module's own docstring" — false in both directions once
this plan lands: `RuntimeToolRegistry` (this module) is now the sole routing authority, and
`ToolRegistry` is not a routing authority (sole or otherwise) at all anymore.

## Scope

**In scope**: `scripts/shared/runtime_tool_registry.py` module docstring only (current lines 2-9,
specifically the second paragraph).

**Out of scope**: The "Import-layer design decisions" and `is_side_effect()` duplication-rationale
paragraphs later in the same docstring — both still accurate, untouched. No class/method code
changes — this file's `RuntimeToolRegistry` class itself needs no behavior change for this plan.

## Assumptions

1. Current docstring (verbatim, confirmed by direct read of `scripts/shared/runtime_tool_registry.py`
   lines 2-9):
   ```
   In-memory registry of `RuntimeTool` instances.

   This module is additive and unused until a later implementation step (MCP
   discovery) populates it, and until subsequent steps wire existing call sites
   (`route_resolver.py`, `tool_executor_helpers.py`, `tool_policy.py`,
   `tool_runner.py`) to actually consult it. `shared.tool_registry.ToolRegistry`
   remains the sole routing authority for now, per that module's own docstring.
   ```
   This entire paragraph describes a bootstrapping-era state ("additive and unused until...") that
   has since been superseded: `McpToolDiscoveryService` now populates this registry (requirement 03
   landed), `route_resolver.py` now consults it as sole authority (this plan), and `tool_registry.py`
   no longer claims routing-authority status (companion `tool_registry.py` doc in this same plan).
   None of the paragraph's premises hold anymore.
2. The other two call sites this module was originally meant to wire into —
   `tool_executor_helpers.py`, `tool_policy.py`, `tool_runner.py` — are out of scope for this plan
   (not mentioned in the plan's Scope or Affected Areas); this doc does not claim they have been
   wired and must not imply otherwise. Only `route_resolver.py`'s consultation status changes here.

## Implementation

### Target file

`scripts/shared/runtime_tool_registry.py`

### Procedure

1. Replace the "additive and unused until..." paragraph. It should now state, in present tense:
   - This registry is populated by `McpToolDiscoveryService.discover_all()` (via
     `agent/services/mcp_tool_discovery.py`) at startup and wired into `ToolRouteResolver` via
     `ToolExecutor.set_runtime_registry()`.
   - `ToolRouteResolver.resolve()` (in `route_resolver.py`) consults this registry as its sole
     routing authority — no fallback to `ToolRegistry` exists.
   - Whether `tool_executor_helpers.py`/`tool_policy.py`/`tool_runner.py` consult this registry
     remains a separate, still-open question not addressed by this edit (do not claim it is wired
     into those call sites unless independently verified — out of scope here).
2. Delete the sentence "`shared.tool_registry.ToolRegistry` remains the sole routing authority for
   now, per that module's own docstring" outright — do not replace it with an equivalent claim about
   `RuntimeToolRegistry` being "sole" *inside this same sentence slot* if it duplicates what step 1
   already states; avoid saying the same thing twice.
3. Leave untouched: "Import-layer design decisions" paragraph (the `classify_operation_type()`/
   `apply_policy()` rationale) and the `is_side_effect()` duplication-rationale paragraph — both
   remain accurate.

### Method

Direct text edit of the module docstring string literal only; zero logic/behavior change; no
import/signature change to the `RuntimeToolRegistry` class.

### Details

- Suggested replacement text (paraphrase; implementer judgment call on exact wording):
  ```
  In-memory registry of `RuntimeTool` instances, populated by
  `McpToolDiscoveryService.discover_all()` at startup and wired into
  `ToolRouteResolver` via `ToolExecutor.set_runtime_registry()`.
  `shared.route_resolver.ToolRouteResolver.resolve()` consults this registry as
  the sole routing authority — no fallback to `shared.tool_registry.ToolRegistry`
  exists.
  ```
- Verify no other stale reference to "sole routing authority" belonging to `ToolRegistry` remains
  elsewhere in this file: `grep -n "sole routing authority" scripts/shared/runtime_tool_registry.py`
  should, after the edit, show this module (not `ToolRegistry`) as the subject of that phrase, or
  the phrase should be dropped in favor of the wording above.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Docstring text review | `grep -n "sole routing authority\|additive and unused" scripts/shared/runtime_tool_registry.py` | No remaining claim that `ToolRegistry` is sole/for-now authority; no stale "additive and unused" framing |
| Format/lint | `uv run ruff format scripts/shared/runtime_tool_registry.py && uv run ruff check scripts/shared/runtime_tool_registry.py` | 0 errors |
| Full suite | `uv run pytest` | No new failures (docstring-only) |
| Docs consistency | `uv run check-mcp-docs` | Routing-authority language check passes |
