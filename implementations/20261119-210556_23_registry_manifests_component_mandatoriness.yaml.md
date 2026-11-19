## Goal

- Regenerate `registry/manifests/component_mandatoriness.yaml` so it carries envelope version 2 while its 10 entries stay identical, and confirm it is drift-checked once per `--check` run (`REQ-010`, `REQ-014`; `AC-007`, `AC-011`).

## Scope
**Release unit**: manifest-contract-revision

## Assumptions

- Row 01 edits `tools/generate_reference_table.py` in the same commit: it removes this manifest from `UNBOUND_MANIFESTS` (line 491) so the single classification lives in `MANIFESTS_BY_DOMAIN["mandatoriness"]` (line 484).
- The committed `sources: [registry/component_mandatoriness.yaml]` already matches what the builder reads (measured 2026-11-19), so the declaration stays as it is.

## Design decisions

- `D-08`: one classification per manifest, because `_run_check` in `tools/generate_reference_table.py` (lines 985-999) adds both `MANIFESTS_BY_DOMAIN` and `UNBOUND_MANIFESTS` entries and therefore checked this manifest twice.

## Alternatives considered

- Keep the duplicate entry and tolerate two checks: rejected by `REQ-010` - the duplicate is what makes the same drift report twice.

## Implementation
### Target file
`registry/manifests/component_mandatoriness.yaml`
### Procedure
1. After rows 01, 02, 03 land, run `uv run python tools/generate_reference_table.py --manifests`.
2. Commit the rewritten file and confirm the entries are byte-identical to the current ones and only the `version:` line changed.

### Method
- Generator write only; the committed file must equal regenerated output.

### Details
- Committed file today: 10 entries, `sources: [registry/component_mandatoriness.yaml]`, `version: 1`.
- Measured 2026-11-19 by instrumenting `pathlib.Path.read_text` while `build_manifest` ran: the builder opens only `registry/component_mandatoriness.yaml`, so no `sources` change is needed here.
- Row 17 records the envelope revision in ADR-015; the mandatoriness registry and the guarded mandatoriness block are untouched by this plan.

## Compatibility considerations

- The guarded mandatoriness table in `docs/20_mandatoriness/` renders from this manifest, so an unchanged entry set means no doc-block churn.

## Security considerations

- N/A: component names and mandatoriness values only.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed file equals regenerated output (regeneration gate: manifest freshness)
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — mandatoriness is checked once per `--check` run (unit (T-010): single drift check)

## Completion criteria

- `AC-007`: the manifest is drift-checked once; `AC-011`: it records `version: 2`.

## Out of Scope

- Any change to the mandatoriness registry contents or the mandatoriness table wording.

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
- **Requirement ID**: `REQ-010` (component_mandatoriness has one bound-or-unbound classification and its drift check runs once per --check), `REQ-014` (the manifest envelope version is bumped once, coordinated with the schema change)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `registry/manifests/component_mandatoriness.yaml`
