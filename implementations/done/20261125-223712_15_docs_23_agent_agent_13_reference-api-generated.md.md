## Goal

Refresh the generated Agent API reference document so it reflects the new launch-spec module and the removed `filter_env` method (REQ-010).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The file is generated from `registry/manifests/agent_api.yaml` and must not be hand-edited between the guard comments; the generator is `tools/generate_reference_table.py`.
- The content changes only after rows 1-4 land, because the generator reads live source.

## Design decisions

- Regenerate the manifest and the document in one command, so the committed manifest and the rendered block cannot drift.

## Alternatives considered

N/A: hand-editing is forbidden by the file's generated-from header.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`
### Procedure
Regenerate the guarded Agent block from the refreshed manifest.

### Method
- Run `uv run python tools/generate_reference_table.py --manifests --type agent` after rows 1-4 are in the source.
- Review the diff: the new `scripts/agent/http_lifecycle_launch_spec.py` module and its public symbols (`LaunchSpec`, `build_launch_spec`, `build_child_env`) appear, and the `CommandValidator` entry's summary text changes (its docstring no longer mentions filtering environment variables).

Verification finding (Step 3a, 20261126): the manifest records only top-level classes and functions per file, so the `filter_env` method never appears in it and cannot "disappear"; `validate_server_key` lives in `scripts/shared/mcp_config.py`, which is outside the agent manifest's source scope (`scripts/agent/**` only), so it does not appear in this document either.
- Any unrelated diff means the manifest was already stale: report it, do not absorb it.

## Compatibility considerations

N/A: `agent_14_reference-api-subpackages-generated.md` is rendered by the same command and its diff must stay empty.

## Security considerations

N/A: the artifact lists symbols, not values.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --check --type agent`

## Completion criteria

- `--check` exits 0, and the document lists the new launch-spec module and its public symbols, with the `CommandValidator` summary updated.

## Out of Scope

- Regenerating the committed manifest (row 16) and any hand edit.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run `tools/generate_reference_table.py --manifests --type agent` | Completed | — | 20261126 | Execute after rows 1-4 land Regenerated with generate_reference_table.py --manifests --type agent; diff limited to the launch-spec module and the CommandValidator summary. |
| 2 | Confirm `--check --type agent` exits 0 and the diff holds only the expected symbols | Completed | — | 20261126 | generate_reference_table.py --check --type agent and --check (all domains) report no drift. |

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
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`