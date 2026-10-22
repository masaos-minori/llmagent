# Fix the stale anchor in the MCP dispatch document

## Priority
Low

## Summary
Repair one link in `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` whose `#anchor` no longer matches any heading of its target document.

## Background
The anchor check added to the shared docs link check (`tools/_docs_consistency_lib.py`, `check_broken_internal_links`) reports a Warning for a link whose anchor matches no heading of the target. On live docs it reports exactly one: `mcp_03_01_dispatch-and-routing.md` links to `mcp_06_07_mcp-failure-diagnosis.md#llm-called-a-tool-but-execution-failed-with-unknown-tool`, while the target heading reads "LLM sees a tool but execution fails with \"Unknown tool\"" (GitHub-style slug `llm-sees-a-tool-but-execution-fails-with-unknown-tool`). Confirmed by running `uv run python tools/check_docs_consistency.py --domain mcp`.

## Problem
The link no longer scrolls to the intended section, because the heading was reworded after the link was written.

## Reason for Change
The finding is the only live Warning of the new anchor check; leaving it makes the MCP domain run noisy and hides future anchor regressions.

## Implementation Intent
Point the link at the current heading's anchor; keep the surrounding sentence unchanged.

## Target Files or Areas
- `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`

## Required Changes
- Replace the stale anchor with `#llm-sees-a-tool-but-execution-fails-with-unknown-tool` in the link at the end of the tool-name paragraph.

## Constraints
- Do not rename the target heading (other documents may link to it).
- Documentation stays in English and follows the docs content policy.

## Acceptance Criteria
- `uv run python tools/check_docs_consistency.py --domain mcp` reports no anchor Warning.
- The docs checkers named in `routing.md` Tools pass for the edited file.

## Testing Expectations
- `uv run python tools/check_docs_consistency.py --domain mcp`
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`

## Documentation Impact
Yes, one link in the MCP dispatch document; no new information is documented.

## Out of Scope
- Other documents, other anchors, and the anchor check itself.

## Dependencies
- Depends on the anchor check landing (`tools/_docs_consistency_lib.py`); that change is already applied.
- Sibling-issue check: no other open issue under `issues/` touches this file.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Change only the one link target in the named file; do not edit other text or the target document.

## Traceability
- **Workflow phase**: code-implementation
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261022-093452_plan.md
- **Source implementation procedure**: implementations/done/20261022-100402_01_tools__docs_consistency_lib.py.md
- **Generated at**: 20261022-104121
- **Related target files**: docs/22_mcp/mcp_03_01_dispatch-and-routing.md
