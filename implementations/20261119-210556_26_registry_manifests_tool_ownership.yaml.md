## Goal

- Regenerate `registry/manifests/tool_ownership.yaml` so it carries envelope version 2 with its 64 entries and its existing truthful `sources` declaration unchanged (`REQ-014`; `AC-011`).

## Scope
**Release unit**: manifest-contract-revision

## Assumptions

- No entry or field of this manifest changes in this plan.

## Design decisions

- `D-10`: regeneration is coordinated across all 11 manifests rather than selective.

## Alternatives considered

- Skip this manifest because its content does not change: rejected by `AC-011` - every committed manifest must record the bumped version.

## Implementation
### Target file
`registry/manifests/tool_ownership.yaml`
### Procedure
1. After rows 01, 02, 03 land, run `uv run python tools/generate_reference_table.py --manifests`.
2. Commit the rewritten file and confirm only the `version:` line changed.

### Method
- Generator write only.

### Details
- Committed file today: 64 entries, `sources: [config/agent.toml, scripts/mcp_servers]`, `version: 1`.
- Measured 2026-11-19: the builder reads `config/agent.toml` and the `scripts/mcp_servers` tree, so the declaration already matches and `T-009` needs no change for this manifest.

## Compatibility considerations

- `tool_ownership` is bound to the `mcp` domain in `MANIFESTS_BY_DOMAIN` but is not the render manifest for that domain (`mcp_endpoints` is), so its entries do not feed a guarded block.

## Security considerations

- N/A: tool names and owning server paths only.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed file equals regenerated output (regeneration gate: manifest freshness)
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — declared sources equal the files the builder reads (unit (T-009): source declaration)

## Completion criteria

- The file records `version: 2` with unchanged entries and sources.

## Out of Scope

- Any change to tool ownership data or MCP tool registration.

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
- **Requirement ID**: `REQ-014` (the manifest envelope version is bumped once, coordinated with the schema change)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `registry/manifests/tool_ownership.yaml`
