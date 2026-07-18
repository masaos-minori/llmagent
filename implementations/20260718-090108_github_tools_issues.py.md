# Implementation: scripts/mcp_servers/github/tools_issues.py — rename requires_config to config_dependent

Source plan: `plans/20260717-173602_plan.md` ("Replace requires_config with config_dependent in MCP tool definitions")

## Goal

Rename the `"requires_config"` dict key to `"config_dependent"` in every tool
definition of `scripts/mcp_servers/github/tools_issues.py`, value unchanged
(`True` in all cases). Pure mechanical rename.

## Scope

**In scope**: rename the key in all 5 tool-definition dicts in this file.

**Out of scope**: `enabled`/`disabled_reason`; any other field/schema
change.

## Assumptions

- `TOOL_LIST: list[dict] = [` at line 9 — plain dict literal, no
  TypedDict/dataclass.
- No runtime code reads `requires_config` (verified repo-wide grep across
  `scripts/agent scripts/shared scripts/rag scripts/db` — zero matches).

## Implementation

### Target file

`/home/sugimoto/llmagent/scripts/mcp_servers/github/tools_issues.py`

### Procedure

1. Locate the 5 occurrences of `"requires_config"` at lines: 29, 46, 77, 100,
   122 (verified via `grep -n "requires_config" scripts/mcp_servers/github/tools_issues.py`;
   all 5 `True`).
2. Replace key text `"requires_config"` -> `"config_dependent"` on each of
   the 5 lines; value and comma unchanged.

### Method

Literal find-and-replace, 5 occurrences.

```
-        "requires_config": True,
+        "config_dependent": True,
```

### Details

- All 5 occurrences currently `True`, matching Scope ("5 occurrences, all
  True").
- Post-edit: `grep -n "requires_config" scripts/mcp_servers/github/tools_issues.py`
  → 0 matches; `grep -c "config_dependent" scripts/mcp_servers/github/tools_issues.py`
  → 5.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Residual check (this file) | `grep -n "requires_config" scripts/mcp_servers/github/tools_issues.py` | 0 matches |
| New key present | `grep -c "config_dependent" scripts/mcp_servers/github/tools_issues.py` | 5 |
| Format | `uv run ruff format scripts/mcp_servers/github/tools_issues.py` | clean |
| Lint | `uv run ruff check scripts/mcp_servers/github/tools_issues.py` | 0 errors |

Full cross-file validation is covered by the cross-cutting doc
`full_validation_pass_config_dependent_rename.md`.
