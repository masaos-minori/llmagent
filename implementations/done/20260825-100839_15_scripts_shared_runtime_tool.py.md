## Goal
- Remove `RuntimeTool.requires_approval`, which is constructed but never read
  anywhere outside `runtime_tool.py`/`runtime_tool_registry.py` themselves
  (REQ-007, part 2).

## Scope
- In scope: `RuntimeTool`'s `requires_approval` field, `build_runtime_tool()`'s
  `requires_approval` argument/resolution logic/docstring.
- Companion removal in `scripts/shared/runtime_tool_registry.py::apply_policy()` is
  covered by that file's own document, but must land in the same commit (see
  Details).

## Assumptions
- Pending UNK-02 sign-off; this document assumes the Plan's default (remove). Do not
  implement before sign-off is recorded, same as the companion
  `runtime_tool_registry.py` document.
- Re-grepped `.requires_approval` across `scripts/` (including
  `agent/tool_policy.py`, `shared/tool_executor.py`): no read site exists outside
  `runtime_tool.py` (field definition/default resolution) and
  `runtime_tool_registry.py::apply_policy()` (write-only, via `dataclasses.replace()`).

## Design decisions
- `build_runtime_tool()` always constructs `requires_approval` with a default or
  caller-supplied value, but actual approval-requirement decisions are made
  independently by `agent/tool_policy.py::classify_risk()` from
  `cfg.approval.approval_risk_rules`/`tool_safety_tiers` — `classify_risk()` never
  reads `RuntimeTool.requires_approval`. Keeping two independent, potentially
  divergent sources of truth for the same concept is removed rather than preserved.
- `docs/adr/ADR-013-mcp-tool-availability-model.md` already documents this field as
  "written but never read" as a known gap; removal resolves the gap this ADR
  describes (the ADR text itself is not edited here).

## Alternatives considered
- Wiring `classify_risk()` or the approval flow to actually consult
  `requires_approval` (UNK-02's other option) — deferred; this would require new
  design work to reconcile it with `approval_risk_rules`/`tool_safety_tiers`'
  existing priority order, which a simple wiring change cannot resolve safely.

## Implementation
### Target file
`scripts/shared/runtime_tool.py`

### Procedure
1. Remove the `requires_approval: bool` field from the `RuntimeTool` dataclass, and
   its class-docstring line.
2. Remove the `requires_approval: bool | None = None` argument from
   `build_runtime_tool()`'s signature.
3. Remove the `resolved_requires_approval = _or_default(requires_approval, True)`
   line.
4. Remove `requires_approval=resolved_requires_approval` from `build_runtime_tool()`'s
   `RuntimeTool(...)` construction.
5. Remove the docstring line describing `requires_approval`'s default.

### Method
- Pure field deletion. `RuntimeTool` is `frozen=True`; deleting a field is a breaking
  change for any positional (non-keyword) construction. Confirm before deleting that
  every construction site uses `build_runtime_tool()` or explicit keyword arguments
  (confirmed during investigation — no positional construction found).

### Details
- This change and `scripts/shared/runtime_tool_registry.py::apply_policy()`'s
  companion removal must land in the same commit/PR: removing only one side leaves
  `dataclasses.replace(...)` raising `TypeError: unexpected keyword argument 'requires_approval'` immediately.

## Compatibility considerations
- `tests/shared/test_runtime_tool.py`: two cases asserting
  `tool.requires_approval is True` must have that assertion removed.
- `tests/agent/services/test_runtime_tool_routing_integration.py`,
  `tests/agent/commands/test_cmd_mcp.py`, `tests/shared/test_tool_executor.py`,
  `tests/shared/test_route_resolver.py`, `tests/shared/test_rag_tools_consistency.py`,
  `tests/shared/test_tool_executor_routing.py`: these pass
  `requires_approval=...` as a keyword to `build_runtime_tool()` without asserting on
  it — the `requires_approval=...` argument itself must be removed from these calls
  (they would otherwise raise `TypeError` on an unknown keyword), not their
  assertions (they have none to remove).
- `docs/adr/ADR-013-mcp-tool-availability-model.md`'s Decision Details #6 (reload
  updates `agent_safety_tier`/`requires_approval`/`enabled_for_llm`) and Invariant
  INV-04 will no longer match reality after this removal — flag as a documentation
  follow-up (not this document's scope).

## Security considerations
- N/A: the actual approval-requirement authority has always been
  `agent/tool_policy.py::classify_risk()` alone; removing this unread field does not
  weaken any approval gate (it was never consulted).

## Rollback considerations
- Restoring the field/argument/docstring from the commit reverts this change. Test
  call sites that had `requires_approval=...` removed would need to be restored too.

## Validation plan
- `uv run pytest tests/shared/test_runtime_tool.py tests/shared/test_runtime_tool_registry.py -v` — full suite passes (with the noted
  test-side updates) after field removal, per REQ-007's Acceptance criterion.
- `uv run mypy scripts/shared/runtime_tool.py scripts/shared/runtime_tool_registry.py`
  — confirms no type errors from the removal.

## Out of scope
- `RuntimeToolRegistry.degraded_servers`'s removal — companion document.
- Editing `docs/adr/ADR-013-mcp-tool-availability-model.md` itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260825-144000 | 20260825-144500 | UNK-02 sign-off obtained: remove. Landed together with `scripts/shared/runtime_tool_registry.py` and `scripts/agent/startup.py` in one pass (same cycle as doc 14) |
| 2 | Add or update tests per Validation plan | Completed | 20260825-144500 | 20260825-145500 | Removed 2 `requires_approval` assertions in `test_runtime_tool.py`; removed the standalone `requires_approval=...` construction kwarg from 6 other test files across the repo (`test_runtime_tool_routing_integration.py`, `test_cmd_mcp.py`, `test_route_resolver.py`, `test_rag_tools_consistency.py`, `test_tool_executor_routing.py`, `test_tool_executor.py`) — all found via a repo-wide grep before finalizing the field removal |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260825-145500 | 20260825-150000 | mypy clean across `runtime_tool.py`/`runtime_tool_registry.py`; 216 tests pass across all affected files |
| 4 | Update documentation | Completed | 20260825-150000 | 20260825-150300 | Updated CI-003 in `docs/90_shared_90_inconsistencies_and_known_issues.md` (see doc 14 for the routing.md mapping rationale — same doc, same cycle) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-02 (Plan `plans/20260825-095817_plan.md`): maintainer sign-off needed on wiring vs. removing `degraded_servers`/`requires_approval` | Yes — remove | 20260825-144000 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `scripts/shared/runtime_tool.py` change | 1 | Code Change | Completed | — | — |
| `tests/shared/test_runtime_tool.py` update | 2 | Test | Completed | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/shared/runtime_tool.py
