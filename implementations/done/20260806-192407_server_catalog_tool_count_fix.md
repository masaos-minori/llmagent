## Goal

Correct factual errors in the "Server Catalog" table within MCP system overview documentation regarding tool counts for web-search-mcp and mdq-mcp servers.

## Scope

- **In-Scope**:
  - Update `web-search-mcp` tool count from `1` to `2` in `docs/04_mcp_01_system_overview.md`.
  - Update `mdq-mcp` tool count from `9` to `7` in `docs/04_mcp_01_system_overview.md`.
  - Add an inline note/annotation next to `web-search-mcp` stating its count changed from 1 to 2 due to `browser_fetch` integration.
- **Out-of-Scope**:
  - Implementing a general versioning/history system for the table.
  - Modifying any source code.

## Assumptions

1. The current tool counts in `scripts/mcp_servers/web_search/web_search_tools.py` (2) and `scripts/mcp_servers/mdq/mdq_tools.py` (7) are correct and represent the latest state.
2. Existing doc style uses parenthetical annotations for notes.

## Design decisions

- Use a parenthetical inline annotation rather than a separate footnote — keeps the correction visible without requiring reader navigation.
- Minimal edit surface: only modify the two affected cells plus one annotation.

## Alternatives considered

- Add a changelog section below the table: rejected because it adds unnecessary vertical space for a small correction.
- Create a revision history column in the table: over-engineered for a one-time fix.

## Compatibility considerations

- Readers relying on the tool count for capacity planning will see updated numbers.
- No API contract changes — this is purely a documentation correction.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If the annotation format causes rendering issues, revert to a simple cell update without the annotation.
- If other rows in the same table need updating simultaneously, coordinate before making changes.

## Implementation

### Target file

`docs/04_mcp_01_system_overview.md`

### Procedure

1. Locate the "Server Catalog" table in the document.
2. Find the `web-search-mcp` row and update the tool count cell from `1` to `2`.
3. Add inline annotation next to `web-search-mcp` indicating the count change reason.
4. Find the `mdq-mcp` row and update the tool count cell from `9` to `7`.

### Method

Direct file edit using sed or manual editing with precise string matching.

### Details

- Search for `web-search-mcp` in the Server Catalog table.
- Replace the tool count cell value `1` → `2`.
- Add annotation: `(Updated: 1 -> 2 due to browser_fetch integration)` adjacent to the count.
- Search for `mdq-mcp` in the Server Catalog table.
- Replace the tool count cell value `9` → `7`.
- Verify no adjacent rows/columns were modified.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_01_system_overview.md` | Manual visual inspection | `cat docs/04_mcp_01_system_overview.md` | Table shows correct counts and the specified note. |

## Out of scope

- Source code modifications (`scripts/`).
- General table versioning or history tracking.
- Changes to other documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-120000_plan_181423_req_fix.md
- Source implementation procedure: N/A
- Generated at: 20260806-192407
- Related target files: docs/04_mcp_01_system_overview.md
