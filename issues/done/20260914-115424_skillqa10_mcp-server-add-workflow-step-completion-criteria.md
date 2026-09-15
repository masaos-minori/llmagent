# Add "Completed when" criteria to mcp-server-add workflow Steps 2, 3, 4, 5

## Priority
Medium

## Summary
`skills/mcp-server-add/workflow.md` Steps 1, 6, 7, 8 each state an explicit "Completed when," but Step 2 (Update deploy.sh), Step 3 (Update config/agent.toml), Step 4 (Update tool routing), and Step 5 (Deploy) do not.

## Background
This issue follows a skill/workflow design review (5 evaluation criteria, 55 files) requested and conducted in this session.

## Problem
Confirmed by direct reading of `skills/mcp-server-add/workflow.md`:
- Step 2 (lines 108-118): describes adding a `cp` line to `deploy/deploy.sh` with no completion condition.
- Step 3 (121-134): describes two config additions (`[mcp_servers.<name>]` entry and `tool_definitions` array) with no completion condition.
- Step 4 (137-141): describes a conditional tool-routing update with no completion condition and no explicit statement of when the condition (unique prefix present) does or doesn't apply.
- Step 5 (144-147): delegates to the `deploy` skill's Phase 2, which already has its own "Completed when: `bash deploy/deploy.sh` exits 0" — but Step 5 here doesn't state that this delegation is itself the completion condition, leaving it implicit.

## Reason for Change
Steps 2-4 make config edits that are easy to leave partially applied (e.g. adding the `[mcp_servers.<name>]` entry but forgetting the `tool_definitions` array, or adding a `cp` line with a typo'd path) — a stated completion condition per Step gives a concrete check before moving to the next Step.

## Implementation Intent
Add one "Completed when" line to each of Step 2, 3, 4, and 5, each naming the concrete artifact/state that confirms that Step's edit was actually applied (not just drafted).

## Target Files or Areas
- `skills/mcp-server-add/workflow.md`

## Required Changes
- Step 2: add "Completed when: `deploy/deploy.sh` contains a `cp` line for `config/<name>_mcp_server.toml` and the path matches the file actually created."
- Step 3: add "Completed when: `config/agent.toml` has both the new `[mcp_servers.<name>]` entry and a corresponding `tool_definitions` array entry for each of the new server's tools."
- Step 4: add "Completed when: either the new server's tools already resolve via the existing static prefix fallback (no change needed), or `tool_names` in `config/agent.toml` explicitly lists them."
- Step 5: add "Completed when: the `deploy` skill's Phase 2 reports its own `Completed when` condition met (`bash deploy/deploy.sh` exits 0) — this Step's completion is that delegation's completion, not a separate check."

## Constraints
Do not duplicate the `deploy` skill's own Phase 2 completion logic inside Step 5 — reference it, since Step 5 already delegates to that skill.

## Acceptance Criteria
- Steps 2, 3, 4, and 5 in `skills/mcp-server-add/workflow.md` each have an explicit "Completed when" line.
- Step 5's line references the `deploy` skill's own completion condition rather than restating it.
- `tools/check_skills_references.py` still passes.

## Testing Expectations
Not applicable — prose-only workflow file. Run `tools/check_skills_references.py` per `routing.md`'s relevant row.

## Documentation Impact
This issue's entire scope is `skills/mcp-server-add/workflow.md`.

## Out of Scope
- Steps 1, 6, 7, 8, 9 — already have adequate completion conditions.
- Any other evaluation criterion from the same review — tracked in separate issues.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Add only the four completion-condition lines described in Required Changes; do not restructure the surrounding Steps or duplicate the `deploy` skill's own completion logic.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-115424
- **Related target files**: skills/mcp-server-add/workflow.md
