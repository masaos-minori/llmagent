# Remove implementation-location mapping from docs/04_mcp_03_03_transport-and-health.md

## Priority
Medium

## Summary
Remove the hand-written "is defined in `{file}`" / "actual implementation ... in
that file" claims from `docs/04_mcp_03_03_transport-and-health.md`'s `HttpTransport`
section (around line 24), per `skills/DESIGN.md` Docs content policy — remove
("Implementation-location mapping"), while preserving the responsibility-boundary
content the note is trying to convey.

## Background
Discovered as `UNK-03` while executing
`implementations/20260909-194838_03_docs_04_mcp_03_03_transport-and-health_md.md`
(part of `plans/done/20260908-211017_plan.md`, which covered literal-port-number
removal only). `uv run python tools/check_docs_content_policy.py` reports 1
`implementation-location mapping` finding for this file (line 24) plus 5 `full file
tree` findings (lines 52-56, tracked separately in `dcp008` — see Dependencies).
`plans/done/20260908-211017_plan.md`'s `REQ-001` covers literal port numbers only, so
neither finding was in that Plan's scope.

## Problem
Line 24 reads:
> **Inconsistency (Record of required fix):** This section header was previously
> `shared/tool_executor.py`, but the actual implementation of the `HttpTransport`
> class is defined in `shared/http_transport.py` (Explicit in code). Instantiation
> and retention are handled by `shared/tool_transport_invoker.py`, while
> `shared/tool_executor.py` only imports the `TransportError` exception type from the
> same module. Although the module docstring of `shared/tool_executor.py` states
> "Provides HttpTransport implementation for POST /v1/call_tool over httpx.", the
> actual implementation does not exist in that file (Explicit in code).

This states which `.py` file each class/behavior "is defined in" or "does not exist
in" — the `Implementation-location mapping` category `skills/DESIGN.md` Docs content
policy — remove prohibits, since it goes stale the moment the code moves again and
duplicates what `grep`/`git blame` already answer authoritatively.

## Reason for Change
Matches the same policy `dcp003`/`dcp004`/`dcp005`/`dcp006` already applied across
other MCP/Agent/RAG/EventBus docs. The paragraph's underlying point (the section
heading previously named the wrong module) is still worth keeping as a design-intent
note, but the module-file-path claims are not.

## Implementation Intent
Rewrite the paragraph to keep the responsibility-boundary fact — which
class/component owns instantiation, retention, and which exception type is
consumed where — using class/symbol names only, without naming or claiming any
specific `.py` file as the location "actual implementation is defined in" or "does
not exist in". Preserve the "Inconsistency (Record of required fix)" framing only if
it still applies once file-path claims are removed; otherwise fold the surviving
responsibility-boundary content into plain prose (no special heading), per
`rules/coding.md` "Documentation notes — Current behavior classification".

## Target Files or Areas
- `docs/04_mcp_03_03_transport-and-health.md`

## Required Changes
1. Rewrite line 24's paragraph to remove "is defined in `{file}`" / "does not exist
   in that file" phrasing, keeping the class/component responsibility content
   (`HttpTransport`, `ToolTransportInvoker`, `TransportError`) intact.
2. Re-run `uv run python tools/check_docs_content_policy.py` and confirm the
   `implementation-location mapping` finding for this file is gone.

## Constraints
- Do not remove the substantive responsibility-boundary information (which
  component instantiates `HttpTransport`, which imports `TransportError`) — only the
  file-path claims.
- Do not touch the `full file tree` findings (lines 52-56) — tracked in `dcp008`.

## Acceptance Criteria
- `uv run python tools/check_docs_content_policy.py` reports zero
  `implementation-location mapping` findings for `docs/04_mcp_03_03_transport-and-health.md`.
- `uv run python tools/check_docs_consistency.py --domain mcp` passes.
- The `HttpTransport` section still conveys which component owns instantiation and
  which exception type is consumed where, without naming a `.py` file.

## Testing Expectations
Documentation-only change. Run `uv run python tools/check_docs_content_policy.py` and
`uv run python tools/check_docs_consistency.py --domain mcp`. No `pytest`/`mypy`/`ruff`
run required.

## Documentation Impact
Yes — this issue's deliverable is the doc edit described above.

## Out of Scope
- The `full file tree` findings in the same file (lines 52-56) — see `dcp008`.
- Any file other than `docs/04_mcp_03_03_transport-and-health.md`.

## Dependencies
N/A: independent of `dcp008` (same file, the `full file tree` findings on lines
52-56) — both findings are in the same file but do not overlap in content or line
range; either can be done without the other. Filed as a Plan Gap (`UNK-03`) from
`plans/done/20260908-211017_plan.md` — see
`implementations/20260909-194838_03_docs_04_mcp_03_03_transport-and-health_md.md`
for the discovery evidence.

## Unresolved Questions
N/A: none — the required rewrite is a straightforward removal of file-path claims.

## AI Implementation Instruction
Edit only line 24's paragraph in `docs/04_mcp_03_03_transport-and-health.md`. Do not
touch the state-transition diagram (lines 50-58) or any other section. Do not invent
a replacement file reference — remove the file-path claim, do not substitute a
different one. Run `tools/check_docs_content_policy.py` after the edit to confirm the
finding is gone.
