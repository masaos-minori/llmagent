## Goal

- Regenerate `registry/manifests/agent_api.yaml` from the recursive scan so the four `scripts/agent/` subpackage symbols are covered while `scripts/agent/memory/` stays out (`REQ-012`; `AC-009`).

## Scope
**Release unit**: reference-completeness

## Assumptions

- `ASM-06` and the UNK-05 plan default: memory symbols remain in `memory_api`.

## Design decisions

- `D-09`: completeness with the existing document boundary preserved.

## Alternatives considered

- Include `scripts/agent/memory/`: rejected by the UNK-05 plan default - 65 symbols would be listed twice across two manifests and two documents.

## Implementation
### Target file
`registry/manifests/agent_api.yaml`
### Procedure
1. After row 01 lands, run `uv run python tools/generate_reference_table.py --manifests`.
2. Commit the rewritten file and confirm 371 entries: 171 top level plus `workflow/` 34, `services/` 114, `commands/` 38, `shared/` 14, and no `scripts/agent/memory/` file.

### Method
- Generator write only.

### Details
- Committed file today holds 171 entries from a non-recursive `glob("*.py")` scan.
- Counts measured 2026-11-19 by running `_symbol_entries` per directory; the entry growth is what makes the document split (row 30) necessary.

## Compatibility considerations

- Rows 15 and 30 render the two guarded documents from this manifest; row 28 keeps the memory manifest separate.

## Security considerations

- N/A: signatures and docstring summaries only.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed file equals regenerated output (regeneration gate: manifest freshness)
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — subpackages covered, memory excluded (unit (T-011, T-015): recursive coverage)

## Completion criteria

- `AC-009`: the manifest holds the subpackage symbols, and the two agent documents together hold every entry.

## Out of Scope

- Any change to `scripts/agent/` source symbols.
- Moving memory symbols into this manifest.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate and commit | Completed | 20261119-232759 | 20261119-232759 | generator write regenerated with version 2: 371 entries (171 top-level, 200 subpackage, none under scripts/agent/memory/); generate_reference_table --check: No drift found |
| 2 | Run the regeneration gates | Completed | 20261119-232759 | 20261119-232759 | `--manifests` then `git diff --exit-code` regenerated with version 2: 371 entries (171 top-level, 200 subpackage, none under scripts/agent/memory/); generate_reference_table --check: No drift found |

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
- **Requirement ID**: `REQ-012` (agent_api covers the scripts/agent/ subpackages (workflow/, services/, commands/, shared/) so the generated API reference is complete)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `registry/manifests/agent_api.yaml`