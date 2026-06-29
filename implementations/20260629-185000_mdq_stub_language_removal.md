# Implementation: mdq-mcp stub language removal from documentation

## Goal

Remove remaining "stub" and "experimental" language for mdq-mcp from documentation so the server is unambiguously treated as production-ready.

## Scope

- **In-Scope**:
  - Verify MCP-03 and MCP-05 entries in `docs/04_mcp_90_inconsistencies_and_known_issues.md` are properly handled (already addressed by plan 20260629-103842)
  - Confirm no remaining "stub" or "experimental" language in mdq-mcp sections of `docs/04_mcp_04_server_catalog.md`

- **Out-of-Scope**:
  - `scripts/mcp/mdq/tools.py` — already has `status: "production"` on all 7 non-admin tools; no change needed.
  - `scripts/mcp/mdq/server.py` — `/health` already returns no `stub` field; no change needed.
  - Any other MCP server files or test files.

## Assumptions

- The code is already production-ready: all 7 non-admin tools in `tools.py` have `status: "production"`, and `/health` has no `stub: true`.
- The two admin tools (`fts_consistency_check`, `fts_rebuild`) with `status: "admin"` are intentionally admin-only, not stubs.

## Verification Result

**No additional changes needed.** Plan 20260629-103842 already addressed:
1. MCP-03 wording fix (changed "mixed statuses (production and stub)" to "mixed statuses (production and admin)")
2. MCP-05 resolution note added
3. Tool status declaration added to mdq-mcp section in `docs/04_mcp_04_server_catalog.md`

The remaining "stub" references in `docs/04_mcp_90_inconsistencies_and_known_issues.md` are part of the MCP-03/MCP-05 historical entries that were already updated. No additional stub/experimental language exists in mdq-mcp sections beyond these entries.

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_90_inconsistencies_and_known_issues.md` | Text grep | `grep -n -i "stub\|experimental" docs/04_mcp_90_inconsistencies_and_known_issues.md` | Only MCP-03/MCP-05 historical entries contain "stub"; no new stub language in mdq sections |
| `docs/04_mcp_04_server_catalog.md` | Text grep | `grep -n -i "stub\|experimental" docs/04_mcp_04_server_catalog.md` | Zero matches in mdq-mcp section |

## Risks & Mitigations

- **Risk**: Deleting MCP-03/MCP-05 entries removes historical context that other documentation may reference → **Mitigation**: Keep MCP-03/MCP-05 entries as historical records; the "stub" language there is part of the resolved issue description, not active documentation.
