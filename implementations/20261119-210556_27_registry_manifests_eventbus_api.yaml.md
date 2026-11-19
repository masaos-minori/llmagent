## Goal

- Regenerate `registry/manifests/eventbus_api.yaml` so it carries envelope version 2, with its 92 entries unchanged because `scripts/eventbus/` has no subpackages (`REQ-012`, `REQ-014`; `AC-009`, `AC-011`).

## Scope
**Release unit**: manifest-contract-revision

## Assumptions

- `scripts/eventbus/` contains no Python subpackage (measured: only `__pycache__/`), so the recursive scan in row 01 adds no entries here.

## Design decisions

- `D-09`: the recursive scan changes only the trees that actually have subpackages.

## Alternatives considered

- Restructure `scripts/eventbus/` into subpackages to make the scan meaningful: out of scope - the plan changes what the generator reads, not the module layout.

## Implementation
### Target file
`registry/manifests/eventbus_api.yaml`
### Procedure
1. After rows 01, 02, 03 land, run `uv run python tools/generate_reference_table.py --manifests`.
2. Commit the rewritten file and confirm the entry count stays 92 and only the `version:` line changed.

### Method
- Generator write only.

### Details
- Committed file today: 92 entries, `sources: [scripts/eventbus]`, `version: 1`.
- Measured 2026-11-19: the scan opens 22 modules directly under `scripts/eventbus/`, and `find scripts/eventbus -maxdepth 1 -type d` returns only `__pycache__/`.

## Compatibility considerations

- The guarded EventBus API block in `docs/24_eventbus/` renders from this manifest, so unchanged entries mean no block churn there.

## Security considerations

- N/A: signatures and docstring summaries only.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed file equals regenerated output (regeneration gate: manifest freshness)
- `uv run python tools/generate_reference_table.py --check` — No drift found between the manifest and the guarded block (drift gate: entry stability)

## Completion criteria

- The file records `version: 2` and holds the same 92 entries.

## Out of Scope

- Any change to `scripts/eventbus/` module layout or symbols.

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
- **Requirement ID**: `REQ-012` (agent_api covers the scripts/agent/ subpackages (workflow/, services/, commands/, shared/) so the generated API reference is complete), `REQ-014` (the manifest envelope version is bumped once, coordinated with the schema change)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `registry/manifests/eventbus_api.yaml`
