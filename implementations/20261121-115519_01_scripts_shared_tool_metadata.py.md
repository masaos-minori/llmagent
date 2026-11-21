## Goal

Define the closed policy vocabulary the runtime contract uses (REQ-001, REQ-003): side-effect class, retry policy, reconciliation policy, resource-key kind, capability flag values, and the single field-set version constant, in the `shared` leaf layer.

## Scope
**Release unit**: contract-and-producers

## Assumptions
- `shared` stays an import-linter leaf, so this module must not import anything from `agent`.
- The owner decision recorded on 2026-11-21 extends the resource-key kind set with a value for keys that no escalation rule reads; the plan's closed set named only `path`, `branch`, `repo`.

## Design decisions
- Values are declared as `Literal` aliases plus the matching `frozenset` of allowed values, so the type checker and `validate_tool_schema_v2()` read the same definition and cannot drift.
- The field-set version is one module-level constant, not a per-tool literal (REQ-003). Its value is UNK-01 and is not chosen by this procedure.
- No per-tool constants are introduced here; per-tool values stay in the producer declarations.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/shared/tool_metadata.py` (new)
### Procedure
- Create the module with one type alias and one closed value set per vocabulary dimension, plus the version constant.
### Method
- `SideEffectClass` (new) with values `read_only` (new), `local_write` (new), `external_write` (new).
- `RetryPolicy` (new) with values `never` (new), `safe_read_retry` (new), `same_logical_call_only` (new), `reconcile_then_retry` (new).
- `ReconciliationPolicy` (new) with values `not_required` (new), `local_state` (new), `external_state` (new).
- `ResourceKeyKind` (new) with values `path`, `branch`, `repo`, and `non_escalating` (new) for keys no escalation rule reads.
- `PreviewCapability` (new): the closed set holds only the values the approval preflight needs now; the preview-display values stay with the preview work item (UNK-02).
- `TOOL_FIELD_SET_VERSION` (new): the single place the version value is written.
### Details
- Verified 2026-11-21: `AgentSafetyTier` is currently defined only in `scripts/shared/runtime_tool.py`, so moving the vocabulary here has no second definition to reconcile.
- Existing verified values of `resource_scope_keys` include keys that the three named kinds cannot classify (`owner`, `run_id`, `workflow`, `source`, `destination`); that is the reason for the `non_escalating` (new) value.
### Companion test files
- `tests/shared/test_tool_metadata.py` (new)
  - Procedure: Add contract tests for each closed value set and for the single version constant; assert the module imports nothing from `agent` (T-01).
  - Validation: `uv run pytest tests/shared/test_tool_metadata.py -v`

## Compatibility considerations
- Producers and Agent consumers both read this module, so it must stay importable from both sides.

## Security considerations
- Closed value sets are the enforcement point for REQ-001: an open value would let a producer declare a value no consumer can interpret.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run pytest tests/shared/test_tool_metadata.py -v`
- `PYTHONPATH=scripts uv run lint-imports` (shared stays a leaf)

## Completion criteria
- Every vocabulary dimension is a closed set with no per-tool constant, and the module imports nothing from `agent`.
- The version value appears in exactly one place in the repository.

## Out of Scope
- The decision rules that use the capability flag (preview work item), and the call-state contract (REQ-010).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 2; release unit: contract-and-producers |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/shared/tool_metadata.py`, `tests/shared/test_tool_metadata.py`
