## Goal

- Regenerate `registry/manifests/invariant_coverage.yaml` so every `gate` value is a Gate-column value and every entry carries `check_type` (`REQ-001`, `REQ-003`; `AC-001`, `AC-002`).

## Scope
**Release unit**: manifest-contract-revision

## Assumptions

- The file is a committed generated artifact: it changes only through `--manifests`.

## Design decisions

- Regeneration is the only permitted write path (`REQ-013`), and `--check` plus `git diff --exit-code registry/manifests/` prove it.

## Alternatives considered

- Patch the 34 entries in place: forbidden - hand-editing a generated file is out of scope.

## Implementation
### Target file
`registry/manifests/invariant_coverage.yaml`
### Procedure
1. After rows 01 and 03 land, run `uv run python tools/generate_reference_table.py --manifests`.
2. Commit the rewritten file with the generator and schema edits.

### Method
- Generator write only; the committed file must be byte-identical to regenerated output.

### Details
- 34 entries today, each with a Type-column `gate` such as `gate: Unit Test`; measured Gate values in the matrix are `Blocking` 24, `Deployment Blocking` 6, `Non-Blocking` 4.
- The four optional fields (`cited`, `cadence`, `expected_evidence`, `exception`) keep their current values because their parsing is unchanged.

## Compatibility considerations

- Sibling issues `adrchk013` and `adrchk015` also regenerate this file; whichever lands first re-runs `tools/check_plan_target_overlaps.py` before editing.

## Security considerations

- N/A.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed file equals regenerated output (regeneration gate: manifest freshness)
- `uv run python tools/generate_reference_table.py --check` — gate values validate against the schema enum; a Type-column value in `gate` fails validation (schema validation: vocabulary)

## Completion criteria

- Every `gate` value is one of the three gate values and every entry carries `check_type`.

## Out of Scope

- Editing the matrix (`docs/10_adr/adr_01_index.md`) or the matrix checker.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate and commit | Pending | — | — | generator write |
| 2 | Run the regeneration gates | Pending | — | — | `--manifests` then `git diff --exit-code` |

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
- **Requirement ID**: `REQ-001` (invariant_coverage.gate carries the Gate-column value of the matrix row), `REQ-003` (the matrix Type-column value is recorded in its own enumerated field (check_type), with a name that matches the column's meaning)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `registry/manifests/invariant_coverage.yaml`
