## Goal

`REQ-004`: correct `tool_registry.py`'s module docstring, which currently records the
static `ToolRegistry` as having an active fail-safe risk-classification role that
REQ-001 removes.

## Scope

- **In-Scope**: edit `scripts/shared/tool_registry.py`'s module docstring (lines 2-16)
  to remove the "(b) fail-safe... risk-classification path" role description and the
  "Both roles are active and maintained" claim, replacing them with a single remaining
  role (drift-detection) plus a note that the fail-safe role was removed by this change.
- **Out-of-Scope**: any other part of `tool_registry.py` (the `ToolRegistry` class body,
  `get_all_tool_names()`, ownership model documentation below the docstring) —
  `get_all_tool_names()` remains in use by the drift-detection role (a), which this
  Requirement does not touch.

## Assumptions

- Confirmed via Read that the current docstring (`scripts/shared/tool_registry.py:2-16`)
  reads:
  ```
  Tool ownership registry and routing seed data. RuntimeToolRegistry
  (shared/runtime_tool_registry.py) is the sole runtime routing authority, populated from
  live /v1/tools discovery. ToolRegistry serves two verified production roles:
    (a) drift-detection input for McpToolDiscoveryService
        (validate_routing_against_live()/validate_routing_against_config() in
        shared/tool_routing_validation.py) and config drift checks
        (production_config_validator.py, agent/repl_health.py).
    (b) fail-safe "is this a known tool at all" membership check consulted by
        agent.tool_policy.classify_operation_type() (scripts/agent/tool_policy.py:69)
        via get_all_tool_names(), to distinguish OperationType.READ from
        OperationType.UNKNOWN on the live risk-classification path.
  Both roles are active and maintained (not abolished) — confirmed by the live wiring in
  repl_health.py, mcp_tool_discovery.py, and production_config_validator.py.
  ```
- This document depends on REQ-001 (`scripts/agent/tool_policy.py`) landing first, since
  it describes role (b) as removed — apply this edit after
  `implementations/20260825-174354_02_scripts_agent_tool_policy.py.md` is implemented and
  validated, not before.
- Confirmed via `rg "get_all_tool_names"` (see the source Plan's own repository evidence)
  that `agent/tool_policy.py:69` is the only risk-classification consumer of this method
  — the drift-detection role (a)'s own use of `ToolRegistry` does not go through
  `get_all_tool_names()` in the same way and is unaffected.

## Design decisions

- Replace "ToolRegistry serves two verified production roles: (a)... (b)..." with
  "ToolRegistry serves one verified production role: (a)..." (renumbering not required
  since (a) keeps its label for continuity with any external cross-references).
- Replace "Both roles are active and maintained (not abolished)" with "This role remains
  active and maintained (not abolished)".
- Add one sentence noting the removal: "As of 2026-08-25, `ToolRegistry` is no longer
  consulted by `agent.tool_policy.classify_operation_type()` for risk classification —
  that function now uses `RuntimeToolRegistry` exclusively (ADR-003 Decision #8); see
  `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`."

## Alternatives considered

- Leaving the docstring's historical claim in place with only a strikethrough-style
  annotation: rejected — the source Plan's Requirement is to correct the record, not
  annotate a now-false claim as still partially true.

## Implementation

### Target file
`scripts/shared/tool_registry.py`

### Procedure
1. Replace the module docstring's role-listing paragraph (currently lines 5-16) per
   Design decisions above.
2. Do not alter any other part of the docstring (ownership model section below it,
   lines 17+) or any code in the file.

### Method
Docstring-only text replacement; no code change.

### Details
- Keep the reference to `repl_health.py`, `mcp_tool_discovery.py`, and
  `production_config_validator.py` for role (a) — these remain accurate and unaffected.

## Compatibility considerations

N/A: docstring-only change, no behavior affected.

## Security considerations

N/A: documentation correction only.

## Rollback considerations

- Revert the docstring paragraph to its prior two-role wording.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/tool_registry.py` | N/A: docstring-only | `rg "fail-safe" scripts/shared/tool_registry.py` | No match (or only the new "removed" note, not a claim of active use) |
| Repository-wide | Doc consistency | `uv run check-mcp-docs` | Passes (no cross-reference to the removed role from other docs, pending the companion `docs/04_mcp_03_02_tool-registry.md` update) |

## Completion criteria

- `scripts/shared/tool_registry.py`'s docstring no longer claims `ToolRegistry` is
  consulted for risk-classification fail-safe purposes.
- The docstring documents exactly one active production role (drift detection).

## Out of scope

- `scripts/shared/tool_constants.py` — removed from this Requirement's scope after
  adversarial review confirmed its docstring contains no fail-safe/risk-classification
  reference to correct (see source Plan's revised In-Scope/Requirements).
- `docs/04_mcp_03_02_tool-registry.md` — covered by its own companion implementation
  procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the module docstring's role-listing paragraph | Pending | — | — | Apply only after REQ-001 (`tool_policy.py`) is implemented and validated |
| 2 | Documentation update | Completed by Step 1 | — | — | This document's entire purpose is the docstring correction itself |

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
- **Requirement ID**: `REQ-004` — correct `tool_registry.py`'s fail-safe role docstring
- **Source issue**: `issues/20260822_rt_classify_operation_type_unknown_deviation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-132516_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-174354
- **Related target files**: `scripts/shared/tool_registry.py`
