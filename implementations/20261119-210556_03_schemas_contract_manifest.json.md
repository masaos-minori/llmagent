## Goal

- Make the manifest schema the enforcement point for the contract this plan establishes: enumerated gate and check-type vocabularies, a route pattern that accepts registered parameterized paths with their HTTP method, a stamp-less version description, and no `disposition` property (`REQ-002`, `REQ-003`, `REQ-005`, `REQ-008`, `REQ-011`; `AC-001`, `AC-002`, `AC-005`, `AC-010`).

## Scope
**Release unit**: manifest-contract-revision

## Assumptions

- The owner approved this field set on 2026-11-19 (`D-11`, `D-12`, `D-13`), so no approval record is invented for it.
- Gate and Type vocabulars are the values already recorded in `docs/10_adr/adr_01_index.md:177-210`; no classification changes.

## Design decisions

- `D-02`: enforcement lives in the schema, so a wrong value fails in `build_manifest` validation, `--check`, the `manifest-check` pre-commit hook, and the CI `lint` job.
- `D-04`: route identity is the registered path template, so `{event_id}` is a legal segment.
- `D-11`, `D-12`, `D-13`: the approved field set - three gate values, enumerated `check_type` (new), route `method`, removed `health_contracts` `disposition`.

## Alternatives considered

- Two-value gate enum (`Blocking`, `Non-Blocking`): rejected - 6 matrix rows record `Deployment Blocking`, so `--manifests` would fail on current data (UNK-01).
- Keep `disposition` and derive it by parsing ADR-004 prose: rejected by the owner (`D-13`).

## Implementation
### Target file
`schemas/contract_manifest.json`
### Procedure
1. Add `"enum": ["Blocking", "Deployment Blocking", "Non-Blocking"]` to the `invariant_coverage` `gate` property (line 230).
2. Add a `check_type` (new) property to the same entry schema with `"enum": ["Unit Test", "Startup Validation", "Manual Review", "Integration Test", "Static Check", "Unit/Integration Test"]`, and add it to the entry `required` list (line 227).
3. Widen the `eventbus_route_roles` route pattern (line 120) to accept `{...}` parameter segments, keeping the leading slash and the existing character class.
4. Add a `method` (new) property with `"enum": ["GET", "POST"]` to the route entry schema and to its `required` list (line 118).
5. Restate the `db_schema_versions` version description (lines 160-163) as the stamp-less content-hash fingerprint model, naming neither `PRAGMA user_version` nor `WORKFLOW_SCHEMA_VERSION`.
6. Remove the `disposition` property (line 211) from the `health_contracts` entry schema and from its `required` list (line 200).

### Method
- JSON Schema edits only; no generator or manifest file is touched here. Each rejected shape is asserted by `tests/tools/test_generate_reference_table.py` through row 10 (T-003, T-004).

### Details
- Measured 2026-11-19: `gate` has no enum; the route pattern is `^/[A-Za-z0-9/_*]*$`, which rejects `/dlq/{event_id}/requeue`; the version description names `PRAGMA user_version` and `WORKFLOW_SCHEMA_VERSION`; `disposition` is required in every `health_contracts` entry.
- `WORKFLOW_SCHEMA_VERSION` is recorded as confirmed removed by `tools/check_compat_shims.py`, so no plan or schema text may reintroduce the name.
- The envelope `version` property (`minimum: 1`) already accepts 2, so the bump in row 02 needs no envelope edit.

## Compatibility considerations

- The schema is the contract every builder is validated against; row 01 must land in the same commit, otherwise `--manifests` fails validation on the first write.
- `deploy/deploy.sh` copies `schemas/`, so the deployed schema is refreshed with the manifests.

## Security considerations

- N/A for credential handling; the added enums narrow what a generated manifest may claim, which is the point of the check.

## Rollback considerations

- Revert the commit; the manifests and generator revert together.

## Validation plan

- `uv run pytest tests/tools/test_generate_reference_table.py -v` — a Type-column value in `gate` and a malformed route key are rejected (unit (T-003, T-004): schema rejection)
- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — all 11 manifests validate (regeneration gate: manifest validity)

## Completion criteria

- `AC-001`, `AC-002`, `AC-003`: validation rejects a wrong-column gate value, `check_type` (new) is enumerated, and every registered route key with its method validates.
- `AC-008`, `AC-010`: no schema text names a removed version mechanism, and no `disposition` property remains.

## Out of Scope

- Adding matrix-side vocabulary validation to `tools/check_adr_invariant_matrix.py` (out of scope).
- Any tolerant fallback that keeps old manifest shapes valid.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the six schema edits in Procedure | Pending | — | — | one commit with rows 01, 02 |
| 2 | Confirm rejection cases through row 10's tests | Pending | — | — | T-003, T-004 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | regeneration gates pass after rows 18-28 |

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
- **Requirement ID**: `REQ-002` (the gate vocabulary is enumerated in the manifest schema, so a value outside it fails manifest validation and the CI drift gate), `REQ-003` (the matrix Type-column value is recorded in its own enumerated field (check_type), with a name that matches the column's meaning), `REQ-005` (the schema route pattern accepts registered parameterized paths such as /dlq/{event_id}/requeue), `REQ-008` (health_contracts carries no generator-constant disposition), `REQ-011` (db_schema_versions version handling matches the current stamp-less fingerprint model)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `schemas/contract_manifest.json`
