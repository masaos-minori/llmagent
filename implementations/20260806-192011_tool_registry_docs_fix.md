## Goal

Correct erroneous function references, consolidate duplicated procedures, and update constant listings in MCP documentation to match actual implementation.

## Scope

- **In-Scope**:
  - `docs/04_mcp_03_02_tool-registry.md`: Fix function names, reduce duplication by linking to canonical procedure, and update `_SIDE_EFFECT_TOOLS` list.
  - `docs/04_mcp_03_05_lifecycle-and-new-server.md`: Fix function names.
- **Out-of-Scope**:
  - Any modifications to source code (`scripts/`).

## Assumptions

1. `docs/04_mcp_03_05_lifecycle-and-new-server.md` is the intended canonical location for the full "add a new tool / new server" procedure.
2. The requirement to add `CICD_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, and `MDQ_WRITE_TOOLS` is based on the current `scripts/shared/tool_executor_helpers.py` implementation.

## Design decisions

- Consolidate the "add a new tool" procedure into a single canonical reference instead of duplicating it across two documents.
- Use `validate_routing_against_live()` as the authoritative function name per current implementation.

## Alternatives considered

- Keep both procedures duplicated: rejected because it creates maintenance burden and inconsistency risk.
- Inline the full procedure in `tool-registry.md`: rejected because `lifecycle-and-new-server.md` already serves as the canonical reference.

## Compatibility considerations

- Updating `_SIDE_EFFECT_TOOLS` must reflect the current state of `scripts/shared/tool_executor_helpers.py`.
- Cross-reference anchors in `lifecycle-and-new-server.md` must be verified after section reorganization.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If anchor links break after consolidation, restore the original section structure before adjusting links.
- If `_SIDE_EFFECT_TOOLS` update introduces incorrect tool lists, revert to the previous version and verify against `tool_executor_helpers.py`.

## Implementation

### Target file

`docs/04_mcp_03_02_tool-registry.md`

### Procedure

1. Replace `check_routing_drift_vs_live()` with `validate_routing_against_live()` at lines 54 and 59.
2. Replace the "新しいツールの追加" 7-step table (lines 47-59) with a concise summary that links to the canonical procedure in `docs/04_mcp_03_05_lifecycle-and-new-server.md`.
3. Update the `_SIDE_EFFECT_TOOLS` code excerpt (lines 113-116) and its accompanying prose note (line 123) to include `CICD_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, and `MDQ_WRITE_TOOLS`.

### Method

Direct file edits using sed or manual editing with careful attention to line numbers and formatting.

### Details

- Line 54: `check_routing_drift_vs_live()` → `validate_routing_against_live()`
- Line 59: `check_routing_drift_vs_live()` → `validate_routing_against_live()`
- Lines 47-59: Replace entire 7-step table with a paragraph referencing `docs/04_mcp_03_05_lifecycle-and-newserver.md#adding-a-new-tool`
- Lines 113-116: Add `CICD_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `MDQ_WRITE_TOOLS` to the tuple/list
- Line 123: Update prose note to mention the three new tool categories

### Target file

`docs/04_mcp_03_05_lifecycle-and-new-server.md`

### Procedure

1. Replace `check_routing_drift_vs_live()` with `validate_routing_against_live()` at line 53.
2. Review and adjust the `#adding-a-new-tool` anchor link to ensure it points correctly after consolidation.

### Method

Direct file edit.

### Details

- Line 53: `check_routing_drift_vs_live()` → `validate_routing_against_live()`
- Verify `#adding-a-new-tool` anchor still exists and has the correct heading level.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_03_02_tool-registry.md` | Content search | `grep -rn "check_routing_drift_vs_live"` | No matches found |
| `docs/04_mcp_03_05_lifecycle-and-new-server.md` | Content search | `grep -rn "check_routing_drift_vs_live"` | No matches found |
| All modified docs | Visual Inspection | Manual review | Corrected text, updated constants, and working links |

## Out of scope

- Source code modifications (`scripts/`).
- Changes to other MCP documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-110603_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-192011
- Related target files: docs/04_mcp_03_02_tool-registry.md, docs/04_mcp_03_05_lifecycle-and-new-server.md
