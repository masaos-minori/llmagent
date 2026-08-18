# Confirm and hoist `_to_call_tool_response`'s local `CallToolResponse` import to module level

## Priority
Low

## Summary
`scripts/mcp_servers/dispatch.py`'s `_to_call_tool_response` function imports
`CallToolResponse` locally inside the function body, even though a `TYPE_CHECKING`-only
module-level import of the same symbol already exists for the type annotation. Static tracing
found no currently-live import cycle that would require the local import, but the local import
was added deliberately (in commit `89b26343a`, at the same time as the `TYPE_CHECKING` import),
not left over from before it — suggesting possible intent that should be confirmed before
removing it.

## Reason for Change
Found during a `prompts/04_refactor.md` cycle on `dispatch.py` (2026-08-14). Not implemented
there because moving the import touches import-ordering behavior in a low-level, high-blast-
-radius shared module (`dispatch.py` is imported by every MCP server), and the deliberate nature
of the local import (not obviously a leftover) means removing it without confirming intent
carries a non-zero risk of reintroducing a real `ImportError` at import time under some load
order not visible from static analysis alone.

## Implementation Intent
Add a test that imports `mcp_servers.dispatch` before `mcp_servers.models` has been imported
anywhere else in the process (fresh subprocess), to prove no import-time cycle exists. If the
test passes, move the import to module level and remove the redundant `TYPE_CHECKING` guard (or
keep both if there's a reason not visible today — confirm with `git log -p` on commit
`89b26343a` for the original rationale before proceeding).

## Target Files or Areas
- `scripts/mcp_servers/dispatch.py` (`_to_call_tool_response`)
- `scripts/mcp_servers/models.py` (imported symbol's source module)

## Required Changes
- Read `git show 89b26343a` (or equivalent) to understand why the local import was added
  alongside the `TYPE_CHECKING` import, rather than assuming it was accidental.
- Add a fresh-subprocess import-order test proving `import mcp_servers.dispatch` alone (without
  `mcp_servers.models` already loaded) does not raise `ImportError`.
- If the test passes, hoist the import to module level; if it fails, document why the local
  import is required and close this issue as "confirmed intentional, no change."

## Acceptance Criteria
- Either: the import is hoisted to module level and the new import-order test passes, or
- The local import is confirmed intentional (documented in a code comment referencing this
  issue) and no change is made.

## Testing Expectations
New fresh-subprocess import-order test (see Required Changes); full `tests/mcp_servers/`
regression run if the import is moved.

## Documentation Impact
None expected.

## Out of Scope
- Do not change `_to_call_tool_response`'s logic, only the import location.
- Do not touch any other function in `dispatch.py`.

## AI Implementation Instruction
Read the original commit's message/diff context before deciding to move the import — if the
commit message or surrounding code suggests the local import was deliberate (e.g. to avoid a
specific known cycle), stop and report rather than moving it anyway.
