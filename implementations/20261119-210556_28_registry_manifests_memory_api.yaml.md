## Goal

- Regenerate `registry/manifests/memory_api.yaml` so it carries envelope version 2, with the 65 memory symbols staying in this manifest and out of `agent_api` (`REQ-012`, `REQ-014`; `AC-009`, `AC-011`).

## Scope
**Release unit**: manifest-contract-revision

## Assumptions

- `ASM-06` and the UNK-05 plan default: `agent_api` excludes `scripts/agent/memory/`.
- Row 16 commits the regenerated memory reference block that renders from this manifest.

## Design decisions

- `D-09`: the existing document boundary is preserved rather than merged into one larger index.

## Alternatives considered

- Let the recursive `agent_api` scan pick up the memory symbols: rejected by the UNK-05 plan default - 65 symbols would be listed in two manifests and two documents.

## Implementation
### Target file
`registry/manifests/memory_api.yaml`
### Procedure
1. After rows 01, 02, 03 land, run `uv run python tools/generate_reference_table.py --manifests`.
2. Commit the rewritten file and confirm the entry count stays 65 and only the `version:` line changed.

### Method
- Generator write only.

### Details
- Committed file today: 65 entries over 24 modules, `sources: [scripts/agent/memory]`, `version: 1`.
- Measured 2026-11-19: the memory scan yields 65 symbols, and the `agent_api` builder will skip this directory through the per-manifest exclusion added in row 01.

## Compatibility considerations

- `docs/23_agent/agent_11_04_memory-module-reference-generated.md` (row 16) renders from this manifest through `_RENDER_MANIFEST["memory"]`.

## Security considerations

- N/A: signatures and docstring summaries only.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed file equals regenerated output (regeneration gate: manifest freshness)
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — `agent_api` holds no `scripts/agent/memory/` entry (unit (T-011): no duplicate symbols)

## Completion criteria

- The file records `version: 2` and remains the single home of the memory symbols.

## Out of Scope

- Any change to `scripts/agent/memory/` symbols.

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
- **Related target files**: `registry/manifests/memory_api.yaml`
