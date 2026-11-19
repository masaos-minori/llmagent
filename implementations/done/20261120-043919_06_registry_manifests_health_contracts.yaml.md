## Goal

Regenerate `registry/manifests/health_contracts.yaml` from the edited posture contract so the mdq
entry no longer lists `server.auth_token_configured` (REQ-008, AC-07).

## Scope
**Release unit**: mdq-auth-check-removal (same unit as procedures 04 and 05)

## Assumptions

- The manifest is a generated artifact produced from `scripts/shared/security/posture_contract.py`
  (generator `_MANIFEST_SOURCES["health_contracts"]`, `tools/generate_reference_table.py:497`):
  regeneration only, never hand-editing.

## Design decisions

- Regenerate with the shared `--manifests` gate after both code siblings (04, 05) land, so one
  generator run produces the final manifest state for the unit.

## Alternatives considered

- N/A: hand-editing a generated manifest violates the generator contract.

## Implementation
### Target file
`registry/manifests/health_contracts.yaml`

### Procedure
1. After procedures 04 and 05 land, run
   `uv run python tools/generate_reference_table.py --manifests` (the health_contracts domain has
   no `--type` alias of its own; the shared manifests gate regenerates it).
2. Confirm the diff contains only the mdq entry change (the `server.auth_token_configured` line
   66 removed). The manifest has no timestamp header: its footer `generated_by:` (line 102) is
   static.

### Method
- Builder path: `_health_contract_entries()` (defined `tools/generate_reference_table.py:810`,
  registered in `_MANIFEST_BUILDERS` at line 985) reads `REQUIRED_CHECK_IDS` live from the
  contract module.

### Details
- The mdq entry currently spans lines 60–70 with the auth id at line 66; every other server entry
  must stay byte-identical — any other diff means a source changed unexpectedly: stop and
  investigate.
- `health_contracts` is a fact manifest with no guarded doc block of its own
  (`tools/generate_reference_table.py:470-473` comment), so no doc re-render side effect is expected.

## Compatibility considerations

- Must land in the same commit as procedures 04/05: a manifest regenerated against the unedited
  contract still carries the removed id, and an edited contract without regeneration fails the
  drift gate (Plan release-unit rule).

## Security considerations

- N/A: generated mirror of the contract; no posture semantics beyond procedure 04.

## Rollback considerations

- Revert as part of the whole release unit commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --check` exit 0 (AC-07).
- `rg "server.auth_token_configured" registry/manifests/health_contracts.yaml` returns nothing.
- `uv run pytest tests/tools/test_generate_reference_table.py` passes.

## Completion criteria

- The mdq entry lists exactly the 5 server-scoped check ids from procedure 04 plus the common
  checks as the generator emits them; all other entries byte-identical; the drift gate exits 0
  (Plan AC-07, AC-08).

## Out of Scope

- Any hand-editing of the manifest.
- The contract and MDQ validation edits themselves (procedures 04, 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run generate_reference_table --manifests after procedures 04/05 | Completed | 2026-11-20 | 2026-11-20 | Same commit as the unit diff only auth-id line 66 |
| 2 | Run --check drift gate and generate_reference_table tests | Completed | 2026-11-20 | 2026-11-20 | check exit 0; tests green |

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
- **Requirement ID**: `REQ-008` (regenerate committed manifests so they mirror live sources)
- **Source issue**: issues/20261117-123020_adrchk020_mandatoriness-registry-posture.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-001311_adrchk020_mandatoriness-registry-posture.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-043919
- **Related target files**: `registry/manifests/health_contracts.yaml`