## Goal

Extend `validate_tool_schema_v2()` to the required field set and resolve scope keys through the declared key kinds (REQ-002, REQ-008; AC-02, AC-07).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- No field-set version value is asserted here; the value is UNK-01.

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
- The field set named by `TOOL_SCHEMA_V2_FIELDS` is read from the same definition the producers are checked against, so the validator and the contract test cannot disagree.
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
- **Requirement ID**: REQ-002, REQ-008
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/shared/resource_scope.py`, `tests/shared/test_resource_scope.py`
