# DOC-001: ToolRouteResolver design doc retains a pre-ADR-003 constructor example

## Priority
Medium

## Summary
`docs/04_mcp_03_01_dispatch-and-routing.md`'s `ToolRouteResolver` code example
(`ToolRouteResolver(server_configs)`) does not match the current implementation. Since
`RuntimeToolRegistry` became the sole routing authority (ADR-003), `ToolRouteResolver` takes no
`server_configs` argument at all. The design doc must be reviewed for this and any other
remaining pre-ADR-003 compatibility arguments or fallback-path wording, and aligned with the
current implementation.

## Background
ADR-003 ("RuntimeToolRegistryを唯一のルーティング権威とする") formalizes `RuntimeToolRegistry` as
the sole routing authority and states that `ToolRouteResolver` must reference only
`RuntimeToolRegistry`, with no fallback to a static registry (INV-02, INV-04). ADR-003's
Migration Steps explicitly call for existing documents' registry descriptions to be aligned with
the ADR ("既存文書のRegistry説明をADRと整合させる"), and its Related Documents list
`04_mcp_03_01_dispatch-and-routing.md` and `04_mcp_03_02_tool-registry.md` as the specifications
this decision governs.

## Problem
`docs/04_mcp_03_01_dispatch-and-routing.md` shows:

    resolver = ToolRouteResolver(server_configs)
    server_key = resolver.resolve("read_text_file")  # -> "file_read"

`scripts/shared/route_resolver.py::ToolRouteResolver.__init__` is keyword-only
(`warn_on_missing`, `strict_mode`, `runtime_registry`) and has no `server_configs` parameter.
The confirmed production call site (`scripts/shared/tool_executor.py`) constructs
`ToolRouteResolver()` with no arguments, then wires the registry in afterward via
`ToolExecutor.set_runtime_registry()` -> `self._resolver.set_runtime_registry(registry)`. The
doc's example reflects neither the current constructor shape nor the actual production wiring
pattern. The rest of `04_mcp_03_01_dispatch-and-routing.md` and `04_mcp_03_02_tool-registry.md`
was spot-checked and otherwise appears consistent with ADR-003, but has not been read
line-by-line for every remaining example.

## Reason for Change
A stale constructor example for the routing-authority component can mislead a developer or an
AI coding agent into instantiating `ToolRouteResolver` with an argument shape that no longer
exists, or into believing a `server_configs`/static-registry input is still part of routing when
ADR-003 explicitly forbids it. Given ADR-003's fail-closed security rationale for unregistered
tools, keeping this specification accurate is worth prioritizing over general documentation
polish.

## Implementation Intent
Documentation-only change. Replace the stale example with one that matches the confirmed current
pattern: construct `ToolRouteResolver()` with no arguments and wire the registry in via
`set_runtime_registry()` (or reference `ToolExecutor.set_runtime_registry()` as the real
integration point, whichever reads more clearly in context). While updating, scan the remainder
of both `04_mcp_03_01_dispatch-and-routing.md` and `04_mcp_03_02_tool-registry.md` for any other
pre-ADR-003 compatibility-argument or fallback-path wording that was not caught during this
review. Preserve all surrounding prose already consistent with ADR-003 — most of both documents
already correctly describes `RuntimeToolRegistry` as sole authority.

## Target Files or Areas
- `docs/04_mcp_03_01_dispatch-and-routing.md` (confirmed: `ToolRouteResolver` code example, "ToolRouteResolver (`shared/route_resolver.py`)" section)
- `docs/04_mcp_03_02_tool-registry.md` (same routing-authority narrative; verify for similar staleness — not yet fully confirmed)
- Reference for correct current behavior: `scripts/shared/route_resolver.py`, `scripts/shared/tool_executor.py`, `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`

## Required Changes
- Replace the `ToolRouteResolver(server_configs)` example in `docs/04_mcp_03_01_dispatch-and-routing.md` with one matching the confirmed current constructor and wiring pattern (`ToolRouteResolver()` + `set_runtime_registry()`).
- Review the same document and `04_mcp_03_02_tool-registry.md` for any other remaining references to a static-registry fallback, removed constructor arguments, or other pre-ADR-003 wording.
- Where a document claim cannot be confirmed against current code during this pass, mark it `Needs Confirmation` rather than silently rewriting or leaving it as an unverified assertion.

## Constraints
Documentation-only: do not modify `scripts/shared/route_resolver.py`, `scripts/shared/tool_executor.py`, `scripts/shared/runtime_tool_registry.py`, or any other implementation file as part of this issue.

## Acceptance Criteria
- The `ToolRouteResolver` code example in `docs/04_mcp_03_01_dispatch-and-routing.md` matches `scripts/shared/route_resolver.py`'s current constructor signature and the confirmed production wiring pattern in `scripts/shared/tool_executor.py`.
- No remaining passage in `04_mcp_03_01_dispatch-and-routing.md` or `04_mcp_03_02_tool-registry.md` implies a static-registry fallback for routing, other than as explicitly labeled historical or Known-Issue context.
- Any claim in the updated sections that cannot be verified against current code is recorded under `Needs Confirmation` rather than left as an unverified assertion.

## Testing Expectations
Not required — documentation-only change with no behavior impact. Manual verification: re-read the updated example against `scripts/shared/route_resolver.py::ToolRouteResolver.__init__` and `scripts/shared/tool_executor.py`'s construction/wiring of `ToolRouteResolver`.

## Documentation Impact
Yes. `docs/04_mcp_03_01_dispatch-and-routing.md`, and `docs/04_mcp_03_02_tool-registry.md` if similar staleness is confirmed there, must be corrected to reflect only the current `RuntimeToolRegistry`-as-sole-authority design (ADR-003), removing or correcting any remaining pre-ADR-003 compatibility-argument or fallback-path wording. Keep the change to design intent, responsibility boundaries, and the corrected example — do not add complete API signatures or additional detail beyond what is needed to fix the identified mismatch.

## Out of Scope
- Do not change `ToolRouteResolver`, `RuntimeToolRegistry`, `ToolExecutor`, or any other implementation behavior.
- Do not modify ADR-003 itself. If a genuine deviation between ADR-003's Decision and the current implementation (as opposed to a stale spec-doc example) is found, record it as a separate issue rather than editing the ADR here.
- Do not perform a general rewrite of either document beyond correcting the identified mismatch(es).

## Dependencies
N/A: none

## Unresolved Questions
- Whether `04_mcp_03_02_tool-registry.md` contains additional stale `ToolRouteResolver`-related content beyond the routing-authority narrative already spot-checked — needs a full read during implementation.

## AI Implementation Instruction
Before editing, re-confirm `scripts/shared/route_resolver.py::ToolRouteResolver.__init__`'s current signature and `scripts/shared/tool_executor.py`'s construction/wiring of `ToolRouteResolver` (`grep -rn "ToolRouteResolver(" scripts/`), since this issue's evidence may go stale if either changes before implementation. Keep the edit minimal: fix the stale example and any other confirmed pre-ADR-003 wording only; do not rewrite unrelated sections of either document. Do not modify any file under `scripts/`. If a doc claim cannot be verified against current code, stop and record it under `Needs Confirmation` instead of guessing.
