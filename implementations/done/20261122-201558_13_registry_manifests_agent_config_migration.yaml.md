## Goal

Add the committed contract manifest for the agent-config migration domain (REQ-002), the artifact `tools/generate_reference_table.py --check` compares the generated block against.

## Scope
**Release unit**: RU-1 generator-and-generated-block

One file is created. Its content is written by the tool, not hand-authored; the generator is sibling procedure seq 04 and seq 12, the destination document is seq 06.

## Assumptions
- `check_drift()` verifies a doc-backed domain against its committed manifest (`run_validation_gates`-independent path: `generate_reference_table.py` lines 1118-1131), so `--check` cannot cover the domain without this artifact.
- CI compares the committed manifests against the live sources (`ci.yml` line 37, `git diff --exit-code registry/manifests/`), so the file must be committed as the tool writes it.

## Design decisions
- Generate the file with `uv run python tools/generate_reference_table.py --manifests`; never hand-edit it.

## Alternatives considered
N/A: the manifest path is the only way a doc-backed domain is covered by `--check`.

## Implementation
### Target file
`registry/manifests/agent_config_migration.yaml` (new)
### Procedure
1. Write the manifest with the tool after the generator is implemented.
### Method
The entries come from the mapping read by `tools/_agent_config_migration.py`; the file records the sources it was built from.
### Details
N/A: no content beyond what the tool writes.

## Compatibility considerations
The existing manifest-drift check treats the new name like any other registered manifest; no existing manifest changes.

## Security considerations
N/A: committed artifact, read-only generation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` reports no drift for the domain (with seq 06's block present).

## Completion criteria
The committed manifest equals the tool's rebuild from live sources, and `--check` reports no findings.

## Out of Scope
The generator and its renderer (seq 04, seq 12); the destination document (seq 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the manifest with `--manifests` | Completed | 2026-11-23 | 2026-11-23 | Written by the tool, not hand-edited; the entries are the mapping read from the validator source |
| 2 | Run `generate_reference_table.py --check` | Completed | 2026-11-23 | 2026-11-23 | "No drift found". **Additional target file discovered**: writing this manifest required `schemas/contract_manifest.json` to accept the `agent_config_migration` manifest name and its entry shape; that file is not a row of the frozen table, so the schema branch was added as the minimum change the manifest validation required |

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
- **Requirement ID**: `REQ-002` (the generated table lives in one place and is checked)
- **Source issue**: `issues/done/20261120-114214_agentcfg006_reduction-integration-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-190238_agentcfg006_reduction-integration-verification.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-201558
- **Related target files**: `registry/manifests/agent_config_migration.yaml`
