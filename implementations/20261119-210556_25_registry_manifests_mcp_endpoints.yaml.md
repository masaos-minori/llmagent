## Goal

- Regenerate `registry/manifests/mcp_endpoints.yaml` with envelope version 2 and a `sources` list that also names `scripts/mcp_servers`, the tree its builder scans (`REQ-009`, `REQ-014`; `AC-006`, `AC-011`).

## Scope
**Release unit**: manifest-contract-revision

## Assumptions

- Row 01 adds the declaration to `_MANIFEST_SOURCES` in the same commit; the 10 entries themselves do not change.

## Design decisions

- `D-07`: `sources` states what is read. The MCP endpoint scan walks the server packages, so declaring only `config/agent.toml` understates the read set.

## Alternatives considered

- Narrow the builder so it reads only `config/agent.toml`: rejected - the endpoint facts come from the server modules, and removing that read would empty the manifest.

## Implementation
### Target file
`registry/manifests/mcp_endpoints.yaml`
### Procedure
1. After rows 01, 02, 03 land, run `uv run python tools/generate_reference_table.py --manifests`.
2. Commit the rewritten file and confirm `sources` lists `config/agent.toml` and `scripts/mcp_servers`, and that the 10 entries are unchanged.

### Method
- Generator write only.

### Details
- Committed file today: 10 entries, `sources: [config/agent.toml]`, `version: 1`.
- Measured 2026-11-19 by instrumenting `pathlib.Path.read_text` while `build_manifest` ran: the `mcp_endpoints` builder also opens `scripts/mcp_servers/**/*.py`, which is the mismatch `T-009` fails today.
- `tool_ownership` (row 26) already declares both paths, which is why the same scan needs no declaration change there.

## Compatibility considerations

- The guarded MCP table renders from this manifest (`_RENDER_MANIFEST`), so unchanged entries mean the MCP docs block stays byte-identical.

## Security considerations

- N/A: server names, ports, and tool names only.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed file equals regenerated output (regeneration gate: manifest freshness)
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — the declared set equals the read set (unit (T-009): source declaration)

## Completion criteria

- `AC-006`: the declared sources match the builder; `AC-011`: the file records `version: 2`.

## Out of Scope

- Any change to MCP server registration or endpoint data.

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
- **Requirement ID**: `REQ-009` (every manifest's sources list names exactly the files and directories its builder reads), `REQ-014` (the manifest envelope version is bumped once, coordinated with the schema change)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `registry/manifests/mcp_endpoints.yaml`
