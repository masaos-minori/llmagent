## Goal

Extend `validate_tool_schema_v2()` to the required field set and resolve scope keys through the declared key kinds (REQ-002, REQ-008; AC-02, AC-07).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- The field-set version value is `2.1` (UNK-01, owner decision 2026-11-21).

## Design decisions
- The validator reports a missing required field as a problem, which is how the registration path already excludes an incomplete entry; no new failure mode is introduced.
- Kind-based reading replaces tool-name reading: the resolver keeps its composed-kind behaviour and reads the mapping instead of a key list.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/shared/resource_scope.py`
### Procedure
- Add the new required fields to the field set the validator checks, and read `resource_scope_keys` as a key-to-kind mapping.
### Method
- The validator's required-field checks are extended inline in this module; `TOOL_SCHEMA_V2_FIELDS` itself lives in `mcp_servers/server.py` and cannot be imported from the `shared` leaf (correction 2026-11-21, Step 3a — the row said "read from the same definition"). The contract test (row 47) compares the validator's behaviour against `server.py`'s field-name tuple so the two cannot disagree.
- The required entry field set is the four schema-2.0 names plus `agent_safety_tier`, `side_effect_class`, `retry_policy`, `reconciliation_policy`, `idempotency_required`, `preview_capability`, `policy_version`; vocabulary fields are checked against the closed value sets from `shared.tool_metadata`.
- `resolve_resource_scopes()` and `_scope_keys_problems()` resolve kinds from the mapping; keys typed `non_escalating` still resolve a scope string but are never used by an escalation rule.
### Details
- Verified 2026-11-21: `validate_tool_schema_v2()` is the enforcement point named by `docs/22_mcp/mcp_06_11_new-tool-registration-procedure.md`; `_COMPOSED_KIND_SEPARATORS` handles the composed kinds, and an unscoped tool returns an empty tuple.
### Companion test files
- `tests/shared/test_resource_scope.py`
  - Procedure: Extend `TestValidateToolSchemaV2` to the new required field set and change `TestResolveResourceScopes` and `TestScopesConflict` fixtures to the key-to-kind mapping, including a `non_escalating` key that resolves a scope but never escalates (T-02, T-06).
  - Validation: `uv run pytest tests/shared/test_resource_scope.py -v`

## Compatibility considerations
- Changing the value type is a contract change for every producer literal, so it lands with rows 08 and 68 in the same release unit.

## Security considerations
- Fail-closed behaviour for a missing field is preserved; the fallback write scope for an unresolved write tool is unchanged.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- The change described in Implementation is present, and the validation plan passes.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 2; release unit: contract-and-producers Implemented: validator extended to schema-2.1 incl. agent_safety_tier wire field; keys mapping. |
| 2 | Add or update tests per Validation plan | Completed | — | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue test_resource_scope.py updated: 47 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-203300 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue Targeted gates green 2026-11-21; full suite at unit end. unit-end validation: full suite 13314 passed / 7 skipped; ruff format+check clean; mypy 590 files clean; lint-imports 6 kept; diff-cover 97% (fail-under 90) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |

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
- **Requirement ID**: REQ-002, REQ-008
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/shared/resource_scope.py`, `tests/shared/test_resource_scope.py`