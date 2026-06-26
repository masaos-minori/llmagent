# Goal

Remove all "Experimental" and "stub" markers from mdq-mcp documentation to reflect production status.

## Scope

**In-Scope**:
- Remove "Status: Experimental" from `docs/04_mcp_05_security_and_safety_model.md` (2 locations)
- Remove `"stub": true` and its explanation comment from `docs/04_mcp_06_configuration_and_operations.md`
- Remove "Experimental" from MDQ description in `docs/05_agent_09_data-layer.md`

**Out-of-Scope**:
- Code changes (tools.py, server.py already completed)
- Other documentation files not listed above

## Assumptions

1. mdq-mcp is production-ready and should be described as such across all docs
2. Removing "Experimental" markers does not affect any other system behavior

## Implementation

### Target file 1: `docs/04_mcp_05_security_and_safety_model.md`

#### Procedure

1. **Line 358**: Remove "Experimental — FTS5 search is functional but not production-validated." from MDQ status line
   - Change to: "Status: Production-ready"

2. **Line 441**: Remove "Experimental. FTS5 search is functional but not production-validated." from Current Status section
   - Change to: "MDQ: Production-ready. FTS5 search and indexing implemented."

#### Method

Use Edit tool to replace the specific lines with updated text.

#### Details

```
Line 358:
Before: **Status:** Experimental — FTS5 search is functional but not production-validated.
After:  **Status:** Production-ready

Line 441:
Before: - **MDQ:** Experimental. FTS5 search is functional but not production-validated.
After:  - **MDQ:** Production-ready. FTS5 search and indexing implemented.
```

### Target file 2: `docs/04_mcp_06_configuration_and_operations.md`

#### Procedure

1. **Lines 185-190**: Remove `"stub": true` from JSON example and its explanation comment

#### Method

Use Edit tool to remove the stub line and update the explanation comment.

#### Details

```
Before (lines 181-190):
**mdq-mcp (port 8013):**
```json
{
  "status": "ok",
  "ready": true,
  "stub": true,
  "dependencies": {},
  "details": {"service": "mdq-mcp"}
}
```
Root-level `stub: true` marks experimental status (not non-functional).

After:
**mdq-mcp (port 8013):**
```json
{
  "status": "ok",
  "ready": true,
  "dependencies": {},
  "details": {"service": "mdq-mcp"}
}
```
```

### Target file 3: `docs/05_agent_09_data-layer.md`

#### Procedure

1. **Line 102**: Remove "Experimental" from MDQ description

#### Method

Use Edit tool to replace the line with updated text.

#### Details

```
Before: - **MDQ**: Experimental markdown query server. Access via `mdq-mcp` tools only. FTS5 search is functional but not production-validated. See [04_mcp_07_mdq_rag_boundary.md](04_mcp_07_mdq_rag_boundary.md) for the RAG/MDQ boundary.
After:  - **MDQ**: Markdown query server. Access via `mdq-mcp` tools only. FTS5 search and indexing implemented. See [04_mcp_07_mdq_rag_boundary.md](04_mcp_07_mdq_rag_boundary.md) for the RAG/MDQ boundary.
```

## Validation plan

| Target File | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/04_mcp_05_security_and_safety_model.md | Verify no "Experimental" references for MDQ remain | rg "mdq.*experimental\|MDQ.*Experimental" docs/04_mcp_05_security_and_safety_model.md | 0 matches |
| docs/04_mcp_06_configuration_and_operations.md | Verify "stub" removed from mdq-mcp health example | rg "mdq.*stub" docs/04_mcp_06_configuration_and_operations.md | 0 matches |
| docs/05_agent_09_data-layer.md | Verify "Experimental" removed from MDQ description | rg "MDQ.*Experimental" docs/05_agent_09_data-layer.md | 0 matches |