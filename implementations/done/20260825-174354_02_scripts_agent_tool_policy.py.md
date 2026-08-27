## Goal

`REQ-001`/`REQ-002`: switch `classify_operation_type()`'s UNKNOWN/READ decision from the
static `ToolRegistry` (routing-forbidden per ADR-003 INV-04) to `RuntimeToolRegistry`
(the sole Safety Tier/Write-attribute authority per ADR-003 Decision #8), and thread the
same registry through `classify_risk()`.

## Scope

- **In-Scope**: add a `registry: RuntimeToolRegistry | None = None` parameter to both
  `classify_operation_type()` and `classify_risk()` in `scripts/agent/tool_policy.py`;
  change the UNKNOWN/READ branch to consult `registry` instead of
  `get_registry().get_all_tool_names()`.
- **Out-of-Scope**: the WRITE/DELETE/EXECUTE/API_WRITE frozenset checks that precede the
  UNKNOWN/READ branch (lines 61-68) — unchanged; `cfg.approval.tool_safety_tiers` /
  `approval_risk_rules` Priority 1/2 logic in `classify_risk()` — unchanged.

## Assumptions

- Confirmed via Read (`scripts/shared/runtime_tool_registry.py:72-82`) that
  `RuntimeToolRegistry.get(tool_name)` raises `KeyError` for an unregistered tool name,
  distinct from a registered-but-untiered tool (which returns a safe default at
  construction time, not a raise) — `classify_operation_type()` must catch this
  `KeyError` and convert it to `OperationType.UNKNOWN`.
- Confirmed via Read (`scripts/agent/context.py`, `AppServices.__init__`) that
  `ctx.services_required.runtime_tools` is typed `RuntimeToolRegistry | None`, and per
  ADR-003 Decision #6 ("no fallback to the static Registry"), `registry is None` must
  resolve to `OperationType.UNKNOWN` (fail-closed), never fall back to
  `get_registry().get_all_tool_names()`.
- **[UNK-01 investigation, resolves source Plan's open item]** Confirmed via `rg
  "runtime_tools" tests/agent/` that no existing test currently passes a `registry`
  argument to `classify_operation_type()`/`classify_risk()` (the parameter does not yet
  exist). A large number of existing tests call these two functions directly with no
  `registry` argument and assert `OperationType.READ` / risk levels derived from READ
  classification for tools not in `_ALL_WRITE_TOOLS`/`DELETE_TOOLS`/`_EXEC_TOOLS`/
  `_GITHUB_MUTATION_TOOLS` (e.g. `list_directory`, `read_text_file`, `search_web`).
  Under the new signature's default (`registry=None` → fail-closed `UNKNOWN`), these
  specific assertions will fail unless updated to pass an explicit registry. Confirmed
  exact locations (see source Plan's revised Tests section):
  `tests/agent/test_tool_policy_comprehensive.py:227-229`,
  `tests/agent/test_tool_approval_risk.py:357-358,366`. Assertions expecting
  `"unknown"` for a genuinely unregistered tool name (e.g.
  `totally_unregistered_tool_xyz`) are unaffected by this change.

## Design decisions

- `classify_operation_type(tool_name: str, registry: RuntimeToolRegistry | None = None)
  -> OperationType`: after the unchanged WRITE/DELETE/EXECUTE/API_WRITE checks, replace
  `if tool_name not in get_registry().get_all_tool_names(): return OperationType.UNKNOWN`
  with: `if registry is None: return OperationType.UNKNOWN`; `try: registry.get(tool_name)
  except KeyError: return OperationType.UNKNOWN`; `return OperationType.READ`.
- `classify_risk(cfg, tool_name, args, registry: RuntimeToolRegistry | None = None) ->
  RiskLevel`: pass `registry` through unchanged to the Priority 3 call at line 152
  (`classify_operation_type(tool_name, registry)`); Priority 1/2 logic (lines 143-149)
  is untouched.
- Remove the now-unused `get_registry` import (`from shared.tool_registry import
  get_registry`, line 26) from `tool_policy.py` if this was its only use in the file —
  confirm via `rg "get_registry" scripts/agent/tool_policy.py` before removing.
- Add `from shared.runtime_tool_registry import RuntimeToolRegistry` (type-only usage;
  use `TYPE_CHECKING` guard if the existing import style in this file favors it — check
  `scripts/agent/tool_policy.py`'s current import block for the convention already in
  use).

## Alternatives considered

- Falling back to the static `ToolRegistry` when `registry is None`: rejected — directly
  contradicts ADR-003 Decision #6 ("no fallback to the static Registry") and would
  perpetuate the exact drift this Requirement exists to close.
- Making `registry` a required (non-Optional) parameter: rejected — would force every
  test and call site to be updated simultaneously with no incremental path, and the
  source Plan's Design explicitly treats the `None` default as fail-closed semantics
  rather than an optional convenience.

## Implementation

### Target file
`scripts/agent/tool_policy.py`

### Procedure
1. Add `registry: RuntimeToolRegistry | None = None` to `classify_operation_type()`'s
   signature (currently `scripts/agent/tool_policy.py:54`).
2. Replace the body's UNKNOWN/READ branch (lines 69-71) with the `registry`-based
   `KeyError`-catching logic described in Design decisions.
3. Add `registry: RuntimeToolRegistry | None = None` to `classify_risk()`'s signature
   (currently `scripts/agent/tool_policy.py:137`).
4. Update the Priority 3 call site (line 152) to `classify_operation_type(tool_name,
   registry)`.
5. Remove the `get_registry` import if no longer referenced elsewhere in the file;
   add the `RuntimeToolRegistry` import.
6. Update both functions' docstrings to describe the `registry` parameter and the
   fail-closed `None` behavior.

### Method
Signature extension plus a body substitution in the UNKNOWN/READ branch; no change to
the preceding frozenset checks or to `classify_risk()`'s Priority 1/2/4 logic.

### Details
- The `try/except KeyError` pattern must wrap only the `registry.get(tool_name)` call,
  not any other statement, to avoid masking unrelated errors.
- Do not change `RiskLevel` values returned by Priority 1/2/4 branches in `classify_risk()`
  — only the Priority 3 branch's registry source changes.

## Compatibility considerations

- Both parameters default to `None`, so any caller not yet updated in this pass
  (there should be none after REQ-003's four call-site updates land) continues to compile,
  but will now get fail-closed `UNKNOWN` behavior instead of the old static-registry
  lookup — this is the intended behavior change, not an oversight.
- See Assumptions/UNK-01 above: several existing tests directly asserting `"read"` for
  specific tool names must be updated in the same change (tracked in this document's
  Execution Status, not in a separate test-only document, since these are direct unit
  tests of this file's functions).

## Security considerations

- Directly implements ADR-003 Decision #8 (single source of truth for Safety
  Tier/Write attributes) and Decision #6 (no static-registry fallback) for the
  UNKNOWN/READ risk-classification path used by the approval system.

## Rollback considerations

- Revert the two signature changes and the UNKNOWN/READ branch to the static-registry
  lookup; re-add the `get_registry` import if removed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_policy.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_policy_comprehensive.py -v` | RuntimeToolRegistry-registered/READ_ONLY tools classify as READ even when absent from the static ToolRegistry; unregistered/`registry=None` tools classify as UNKNOWN |
| `scripts/agent/tool_policy.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/agent/test_tool_approval_risk.py -v` | Updated `_classify_operation_type`/`_classify_risk` assertions (see Assumptions/UNK-01) pass |
| Repository-wide | Type check | `uv run mypy scripts/` | No new errors |

## Completion criteria

- `classify_operation_type()` and `classify_risk()` both accept `registry:
  RuntimeToolRegistry | None = None`.
- A tool registered in `RuntimeToolRegistry` but absent from the static `ToolRegistry`
  classifies as `OperationType.READ`.
- `registry=None` or a tool absent from `RuntimeToolRegistry` classifies as
  `OperationType.UNKNOWN` (fail-closed, no static-registry fallback).
- The three test locations identified under Assumptions/UNK-01 are updated and pass.

## Out of scope

- The four call-site updates in `tool_audit.py`, `repository_gateway.py`, and
  `tool_approval.py` — covered by their own companion implementation procedure
  documents (REQ-003).
- `scripts/shared/tool_registry.py`/`tool_constants.py` docstrings and
  `docs/04_mcp_03_02_tool-registry.md` — covered by their own companion implementation
  procedure documents (REQ-004).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `registry` parameter and RuntimeToolRegistry-based UNKNOWN/READ logic to `classify_operation_type()` | Pending | — | — | |
| 2 | Add `registry` parameter to `classify_risk()`, thread through to Priority 3 call | Pending | — | — | |
| 3 | Update `tests/agent/test_tool_policy_comprehensive.py:227-229` and `tests/agent/test_tool_approval_risk.py:357-358,366` to pass an explicit registry | Pending | — | — | Per Assumptions/UNK-01 |
| 4 | Add new tests for registry-registered/unregistered/`registry=None` per source Plan AC-01/AC-02 | Pending | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md`) scoped to `scripts/agent/tool_policy.py` and its tests | Pending | — | — | |
| 6 | Documentation update | N/A | — | — | Not in scope for this file — see companion `tool_registry.py`/`tool_constants.py`/`docs/04_mcp_03_02_tool-registry.md` documents for REQ-004 |

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
- **Requirement ID**: `REQ-001`, `REQ-002` — switch UNKNOWN/READ classification to RuntimeToolRegistry
- **Source issue**: `issues/20260822_rt_classify_operation_type_unknown_deviation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-132516_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-174354
- **Related target files**: `scripts/agent/tool_policy.py`
