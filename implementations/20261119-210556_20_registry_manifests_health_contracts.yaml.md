## Goal

- Regenerate `registry/manifests/health_contracts.yaml` without the generator-constant `disposition` field (`REQ-008`; `AC-010`).

## Scope
**Release unit**: manifest-contract-revision

## Assumptions

- The owner decided removal (`D-13`): ADR-004 Decisions #14 and #15 stay the authority for the fail-fast behavior.

## Design decisions

- `D-06`: a manifest field must be a derived fact; a constant copied into 10 entries is not one.

## Alternatives considered

- Derive `disposition` by parsing ADR-004 prose: rejected by the owner (`D-13`).

## Implementation
### Target file
`registry/manifests/health_contracts.yaml`
### Procedure
1. After rows 01 and 03 land, run `uv run python tools/generate_reference_table.py --manifests`.
2. Commit the rewritten file and confirm no entry carries `disposition`.

### Method
- Generator write only.

### Details
- Committed file today: 10 entries, each `disposition: fail-fast`, produced by the constant the generator removes (row 01).
- `sources` stays `scripts/shared/security/posture_contract.py`, which is what `_health_contract_entries` reads.

## Compatibility considerations

- Row 03 removes the schema property in the same commit, otherwise validation fails on the first write.

## Security considerations

- The manifest stops asserting a policy value it cannot derive; the posture checks themselves are unchanged.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed file equals regenerated output (regeneration gate: manifest freshness)
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — entries carry no `disposition` (unit (T-014): no constant field)

## Completion criteria

- `AC-010`: no `disposition` key remains in the file and no ADR-004 parser is added.

## Out of Scope

- Any change to posture checks or ADR-004.

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
- **Requirement ID**: `REQ-008` (health_contracts carries no generator-constant disposition)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `registry/manifests/health_contracts.yaml`
