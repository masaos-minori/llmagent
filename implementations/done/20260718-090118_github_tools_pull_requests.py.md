# Implementation: scripts/mcp_servers/github/tools_pull_requests.py — rename requires_config to config_dependent

Source plan: `plans/20260717-173602_plan.md` ("Replace requires_config with config_dependent in MCP tool definitions")

## Goal

Rename the `"requires_config"` dict key to `"config_dependent"` in every tool
definition of `scripts/mcp_servers/github/tools_pull_requests.py`, value
unchanged (`True` in all cases). Pure mechanical rename.

## Scope

**In scope**: rename the key in all 6 tool-definition dicts in this file.

**Out of scope**: `enabled`/`disabled_reason`; any other field/schema
change.

## Assumptions

- `TOOL_LIST: list[dict] = [` at line 9 — plain dict literal, no
  TypedDict/dataclass.
- No runtime code reads `requires_config` (verified repo-wide grep across
  `scripts/agent scripts/shared scripts/rag scripts/db` — zero matches).

## Implementation

### Target file

`/home/sugimoto/llmagent/scripts/mcp_servers/github/tools_pull_requests.py`

### Procedure

1. Locate the 6 occurrences of `"requires_config"` at lines: 28, 48, 77, 100,
   132, 164 (verified via `grep -n "requires_config"
   scripts/mcp_servers/github/tools_pull_requests.py`; all 6 `True`).
2. Replace key text `"requires_config"` -> `"config_dependent"` on each of
   the 6 lines; value and comma unchanged.

### Method

Literal find-and-replace, 6 occurrences.

```
-        "requires_config": True,
+        "config_dependent": True,
```

### Details

- All 6 occurrences currently `True`, matching Scope ("6 occurrences, all
  True").
- Post-edit: `grep -n "requires_config" scripts/mcp_servers/github/tools_pull_requests.py`
  → 0 matches; `grep -c "config_dependent" scripts/mcp_servers/github/tools_pull_requests.py`
  → 6.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Residual check (this file) | `grep -n "requires_config" scripts/mcp_servers/github/tools_pull_requests.py` | 0 matches |
| New key present | `grep -c "config_dependent" scripts/mcp_servers/github/tools_pull_requests.py` | 6 |
| Format | `uv run ruff format scripts/mcp_servers/github/tools_pull_requests.py` | clean |
| Lint | `uv run ruff check scripts/mcp_servers/github/tools_pull_requests.py` | 0 errors |

Full cross-file validation is covered by the cross-cutting doc
`full_validation_pass_config_dependent_rename.md`.
