# Implementation Procedure: runtime_tool_registry.py

**Plan:** plans/20260924-181019_plan.md
**Target File:** scripts/shared/runtime_tool_registry.py
**Change Responsibility:** Minor
**Severity Classification:** Low
**Estimated Effort:** Small
**Dependencies:** None

---

## Goal

Add public `all_tools()` method to RuntimeToolRegistry class to provide read-only access to all registered tools, replacing direct private `_tools` attribute access.

---

## Current State

File: `scripts/shared/runtime_tool_registry.py` — 218 lines

Key attributes/methods:
- `_tools: dict[str, RuntimeTool]` — private dictionary storing all tools (line ~48)
- `_unavailable_servers: frozenset[str]` — private set tracking unavailable servers (line ~46)
- `__init__(self, tools: dict[str, RuntimeTool] | None = None, unavailable_servers: frozenset[str] | None = None)` — constructor accepting tools and unavailable_servers parameters (lines 40-53)
- `_is_excluded_server(self, server_key: str) -> bool` — checks if server is excluded (line 55)
- Various public methods for tool management

Notes on current implementation vs procedure assumptions:
- `RuntimeToolRegistry.all_tools()` already exists (line 94-96) and returns `list[RuntimeTool]` — NOT `dict[str, Tool]` as the procedure assumes
- No `registry._tools` direct access exists in the codebase (verified by grep across `scripts/`)
- The procedure's constraint "Do NOT change the return type signature (must remain `dict[str, Tool]`)" is incorrect: the actual return type is `list[RuntimeTool]`
- Current callers use `registry.all_tools()` (returns list) and build dicts via comprehensions when needed: `{t.name: t for t in registry.all_tools()}`

---

## Implementation Steps

### Phase 1: Add `all_tools()` public method

N/A — Already completed. `RuntimeToolRegistry.all_tools()` exists at line 94 and returns `list[RuntimeTool]`.

### Phase 2: Update callers in mcp_tool_discovery.py

N/A — Not applicable. No `registry._tools` direct access exists in the codebase. Callers use `registry.all_tools()` which already exists.

---

## Allowed Operations

- Run tests against target files
- Verify existing `all_tools()` method behavior

## Prohibited Operations

- Do NOT modify existing public method signatures unless necessary
- Do NOT change `_tools` visibility (keep as private)
- Do NOT modify test files (handled separately)
- Do NOT introduce new dependencies

## Unknowns Resolved

- UNK-01: RESOLVED — No callers of `registry._tools` found in the codebase (verified by grep)
- UNK-02: RESOLVED — Shallow copy concern is moot; `all_tools()` already returns a list copy
- UNK-03: RESOLVED — No caller mutates the returned dictionary; callers iterate or build new dicts

## Risks

- **Risk 1:** Resolved — `all_tools()` already exists and returns a list copy
- **Risk 2:** Resolved — No callers rely on direct reference semantics to `_tools`

## Acceptance Criteria

1. `all_tools()` method exists and returns a copy of `_tools` — **ACHIEVED** (exists, returns `list[RuntimeTool]`)
2. All callers of `registry._tools` updated to use `registry.all_tools()` — **ACHIEVED** (no such callers exist)
3. No regression in tool registry behavior — pending verification
4. New method has proper docstring — **ACHIEVED** (existing docstring present)
5. Code follows repository conventions (rules/coding.md) — pending verification
