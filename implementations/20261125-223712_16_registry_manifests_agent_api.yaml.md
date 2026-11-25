## Goal

Refresh the committed Agent API manifest so the recorded public symbols match the source after the launch-spec module is added and `filter_env` is removed (REQ-010 generated-artifact consistency).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The manifest is written by `tools/generate_reference_table.py --manifests` and is the source of the rendered doc blocks (row 15); it must never be hand-edited.
- The manifest changes only after rows 1-4 land, because it is generated from live `scripts/agent/*.py` sources.

## Design decisions

- Regenerate with the same command that renders the documents, so the manifest and `docs/23_agent/agent_13_reference-api-generated.md` are refreshed in one step and cannot drift.
- Treat an unexpected diff as a finding to report, not something to accept: the manifest is the contract record other gates compare against.

## Alternatives considered

N/A: hand-editing is forbidden by the generator's guard contract.

## Implementation
### Target file
`registry/manifests/agent_api.yaml`
### Procedure
Regenerate the manifest from live source and confirm the drift check passes.

### Method
- After rows 1-4 are in the source, run `uv run python tools/generate_reference_table.py --manifests --type agent`.
- Review the diff: the `CommandValidator` entry loses `filter_env`, the new `scripts/agent/http_lifecycle_launch_spec.py` module and its public symbols are added, and `scripts/shared/mcp_config.py` gains `validate_server_key`.
- Run `uv run python tools/generate_reference_table.py --check --type agent` to confirm the committed manifest matches the live sources and the rendered doc block matches the manifest.

### Details
- The `agent` manifest covers top-level `scripts/agent/*.py` symbols; `scripts/shared/` symbols appear through the manifest's registered source list, which the generator owns. Do not change the registered source list.

## Compatibility considerations

`CommandValidator` appears twice in the current manifest; the entry count changes only through the generator's own rules.

## Security considerations

N/A: the manifest records symbol names.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --check --type agent`
- the generated-artifact gates in `rules/tool-gates.md` "When to run which tool"

## Completion criteria

- `--check` exits 0 with the manifest committed.
- The manifest no longer records `filter_env` and does record the launch-spec module's public symbols.

## Out of Scope

- Rendering the documentation block (row 15).
- Any other domain manifest (`rag`, `mcp`, `deployment`, `eventbus`, `memory`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the manifest with `tools/generate_reference_table.py --manifests --type agent` | Pending | — | — | Execute after rows 1-4 land |
| 2 | Confirm `--check --type agent` exits 0 | Pending | — | — | |

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
- **Requirement ID**: REQ-010 (generated reference artifacts stay consistent)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `registry/manifests/agent_api.yaml`
