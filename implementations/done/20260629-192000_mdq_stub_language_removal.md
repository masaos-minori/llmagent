# Implementation Design: mdq-mcp Stub Language Removal

## Goal

Resolve mdq-mcp production-readiness and stub marker inconsistency by aligning code, documentation, and tests around a single verified status.

## Scope

- Fix MCP-03 in `docs/04_mcp_90_inconsistencies_and_known_issues.md`: change "mixed statuses (production and stub)" to "mixed statuses (production and admin)", update related text
- Mark MCP-05 in `docs/04_mcp_90_inconsistencies_and_known_issues.md` as resolved
- Add explicit tool status declaration to mdq-mcp section in `docs/04_mcp_04_server_catalog.md`
- No code changes required — all stub markers already removed from `scripts/mcp/mdq/tools.py`

## Affected Files

1. `docs/04_mcp_90_inconsistencies_and_known_issues.md`
   - MCP-03: Change "mixed statuses (production and stub)" → "mixed statuses (production and admin)"
   - MCP-03: Update "Current safe interpretation" to reflect accurate status
   - MCP-03: Update "Notes for AI reference" — no longer warn about stub markers
   - MCP-05: Mark as RESOLVED, remove "Recommended action" since resolved
2. `docs/04_mcp_04_server_catalog.md`
   - mdq-mcp section: Add "**Tool status:** 7 tools are `production`, 2 tools (`fts_consistency_check`, `fts_rebuild`) are `admin`."

## Verification

### Code verification (already confirmed)

- `scripts/mcp/mdq/tools.py`: 7 tools have `"status": "production"`, 2 tools have `"status": "admin"`, no `stub` key anywhere
- `scripts/mcp/mdq/server.py` `/health` endpoint: no `stub` field emitted in JSON response

### Post-fix verification

```bash
rg "stub.*mdq|mdq.*stub|mixed.*stub" docs/
```

Remaining results are only in the RESOLVED MCP-03/MCP-05 sections describing historical context — not contradictory wording.

## Acceptance Criteria

- [x] MCP-03 no longer references "stub" as a current status (only in RESOLVED historical context)
- [x] MCP-05 marked as RESOLVED with resolution date and summary
- [x] mdq-mcp section has explicit tool status declaration matching rag-pipeline-mcp pattern
- [x] No remaining "mixed statuses (production and stub)" wording in docs
