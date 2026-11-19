## Goal

- Regenerate `registry/manifests/config_ownership.yaml` so it carries envelope version 2 with its 37 entries and its existing truthful `sources` declaration unchanged (`REQ-014`; `AC-011`).

## Scope
**Release unit**: manifest-contract-revision

## Assumptions

- No field or entry of this manifest changes in this plan; it is regenerated because every committed manifest must carry the bumped version.

## Design decisions

- `D-10`: all 11 manifests are regenerated in one commit, so a reader can tell which contract revision each was written under.

## Alternatives considered

- Leave this manifest at version 1: rejected by `AC-011` - a stale envelope fails `--check` and `git diff --exit-code registry/manifests/`.

## Implementation
### Target file
`registry/manifests/config_ownership.yaml`
### Procedure
1. After rows 01, 02, 03 land, run `uv run python tools/generate_reference_table.py --manifests`.
2. Commit the rewritten file and confirm only the `version:` line changed.

### Method
- Generator write only.

### Details
- Committed file today: 37 entries, `sources: [scripts/agent/services/config_field_registry.py]`, `version: 1`.
- Measured 2026-11-19: the builder opens exactly that file, so the declaration already satisfies `REQ-009` and `T-009` passes for it without a change.

## Compatibility considerations

- This manifest is unbound (it stays in `UNBOUND_MANIFESTS`) and has no guarded document block, so nothing else regenerates from it.

## Security considerations

- N/A: config field names and owning module paths only.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed file equals regenerated output (regeneration gate: manifest freshness)
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — declared sources equal the files the builder reads (unit (T-009): source declaration)

## Completion criteria

- The file records `version: 2` and its entries and sources are unchanged.

## Out of Scope

- Any change to config field ownership data.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate and commit | Completed | 20261119-232759 | 20261119-232759 | generator write regenerated with version 2; generate_reference_table --check: No drift found |
| 2 | Run the regeneration gates | Completed | 20261119-232759 | 20261119-232759 | `--manifests` then `git diff --exit-code` regenerated with version 2; generate_reference_table --check: No drift found |

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
- **Requirement ID**: `REQ-014` (the manifest envelope version is bumped once, coordinated with the schema change)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `registry/manifests/config_ownership.yaml`