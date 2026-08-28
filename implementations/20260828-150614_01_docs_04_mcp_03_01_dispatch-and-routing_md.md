## Goal

Replace the stale `ToolRouteResolver(server_configs)` code example in `docs/04_mcp_03_01_dispatch-and-routing.md` with one matching the confirmed current production wiring pattern: construct `ToolRouteResolver()` with no arguments and wire the registry via `set_runtime_registry()`. Remove or correct any other pre-ADR-003 compatibility-argument or fallback-path wording found during scan.

## Scope

- **In-Scope**: Update `docs/04_mcp_03_01_dispatch-and-routing.md`; review `docs/04_mcp_03_02_tool-registry.md` for similar staleness.
- **Out-of-Scope**: Modify `scripts/shared/route_resolver.py`, `scripts/shared/tool_executor.py`, `scripts/shared/runtime_tool_registry.py`, or any implementation file. Change ADR-003 itself. General rewrite of either document beyond correcting identified mismatches.

## Assumptions

- Both `04_mcp_03_01_dispatch-and-routing.md` and `04_mcp_03_02_tool-registry.md` are the only documents that contain stale `ToolRouteResolver` examples; no other docs reference this constructor.
- The production wiring pattern in `tool_executor.py` (construct with no args, then `set_runtime_registry()`) is the canonical pattern and should be referenced in the corrected example.

## Design decisions

- Use the confirmed production wiring pattern (`ToolRouteResolver()` + `set_runtime_registry()`) as the canonical example rather than inventing a new pattern.
- Preserve all surrounding prose already consistent with ADR-003; only remove/correct passages that directly conflict with evidence from `route_resolver.py` and `tool_executor.py`.

## Alternatives considered

- Referencing `ToolExecutor.set_runtime_registry()` as the real integration point instead of `set_runtime_registry()` directly. Chose direct `set_runtime_registry()` for clarity unless context demands otherwise.
- Adding a note explaining why `server_configs` was removed. Not needed if the replacement example is self-explanatory.

## Implementation

### Target file

`docs/04_mcp_03_01_dispatch-and-routing.md`

### Procedure

1. Read `docs/04_mcp_03_01_dispatch-and-routing.md` fully and identify the stale `ToolRouteResolver(server_configs)` example.
2. Replace the stale example with one matching the confirmed current pattern: `ToolRouteResolver()` + `set_runtime_registry()`.
3. Scan the remainder of the document for any other pre-ADR-003 compatibility-argument or fallback-path wording; remove or correct those passages.
4. Re-read the updated example against `scripts/shared/route_resolver.py::ToolRouteResolver.__init__` and `scripts/shared/tool_executor.py` construction/wiring.

### Method

Direct edit of the code example block and any conflicting prose passages. No structural changes to headings, lists, or cross-references.

### Details

- Current stale line: `resolver = ToolRouteResolver(server_configs)`
- Replacement: `resolver = ToolRouteResolver()` followed by wiring step showing `set_runtime_registry(registry)` or referencing `ToolExecutor.set_runtime_registry()` as appropriate for the surrounding context.
- Remove any remaining passage implying static-registry fallback for routing, except where explicitly labeled historical or Known-Issue context.

## Compatibility considerations

- The change is documentation-only; no runtime behavior impact.
- Verify that the replacement example does not introduce claims that cannot be verified against current code; record such claims under `Needs Confirmation`.

## Security considerations

- ADR-003's fail-closed security rationale for unregistered tools requires this specification to remain accurate. Stale constructor examples could mislead developers or AI agents into passing arguments that no longer exist.

## Rollback considerations

- Simple revert: restore the previous version of `docs/04_mcp_03_01_dispatch-and-routing.md`. No data migration or schema rollback needed.

## Validation plan

| Target File | Testing Strategy | Expected Outcome |
|---|---|---|
| `docs/04_mcp_03_01_dispatch-and-routing.md` | Manual verification against `route_resolver.py` and `tool_executor.py` | Example matches current constructor and wiring pattern |
| `docs/04_mcp_03_02_tool-registry.md` | Manual review for stale references | No stale pre-ADR-003 references remain |

## Completion criteria

- AC-001: The `ToolRouteResolver` code example matches `scripts/shared/route_resolver.py`'s current constructor signature and the confirmed production wiring pattern in `scripts/shared/tool_executor.py`.
- AC-002: No remaining passage implies static-registry fallback for routing, other than as explicitly labeled historical or Known-Issue context.
- AC-003: Any claim in the updated sections that cannot be verified against current code is recorded under `Needs Confirmation`.
- AC-004: If `04_mcp_03_02_tool-registry.md` contains additional stale content, it is corrected.

## Out of scope

- Modifying any source files under `scripts/shared/`.
- Changing ADR-003 or its Migration Steps.
- Rewriting documents beyond correcting identified mismatches.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read `docs/04_mcp_03_01_dispatch-and-routing.md` and identify stale example | Pending | — | — | |
| 2 | Replace stale `ToolRouteResolver(server_configs)` example | Pending | — | — | |
| 3 | Remove/correct other pre-ADR-003 wording | Pending | — | — | |
| 4 | Review `docs/04_mcp_03_02_tool-registry.md` for similar staleness | Pending | — | — | |
| 5 | Verification: re-read against source code | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: `issues/20260828-130451_doc001_tool_route_resolver_stale_spec.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260828-141055_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260828-150614
- **Related target files**: `docs/04_mcp_03_01_dispatch-and-routing.md`
