## Goal

Regenerate the ownership manifest from the field-registry source so the two prompt rows disappear (REQ-003, generated artifact).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- This file is generated, never hand-edited: `tools/generate_reference_table.py` line 499 maps `config_ownership` to `scripts/agent/services/config_field_registry.py`, so the only permitted change here is the generator's output.
- The row disappears only after row 07 deletes the registry entries; regeneration must run after that change.
- No test asserts a prompt row in this manifest (`tests/tools/test_generate_reference_table.py`, Plan Reference Files), so no test change is needed.

## Design decisions
- N/A: no design decision; the artifact follows its source.

## Alternatives considered
- Hand-editing the manifest to drop the two rows: rejected, hand-edited generated blocks drift and `--check` would fail at the next run.

## Implementation
### Target file
`registry/manifests/config_ownership.yaml`
### Procedure
Run the generator and commit its output.
### Method
- `uv run python tools/generate_reference_table.py --manifests` (writes every registered manifest, including `config_ownership`), then `uv run python tools/generate_reference_table.py --check` to confirm no drift.
- The resulting diff removes only the two prompt entries; nothing else in the file changes.
### Details
- The generator's doc-block welcome line names this file's source; no guarded docs block contains prompt rows (Plan predictable-fallout check), so no documentation block is re-rendered.

## Compatibility considerations
- `check_docs_consistency.py --domain agent` and the `lint` CI job run the generator's `--check`, so an uncommitted regeneration fails CI; commit the regenerated file with row 07.

## Security considerations
- N/A: no trust boundary is involved.

## Rollback considerations
- N/A: revert the commit; if the registry source is reverted, regenerate rather than restoring the file by hand.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` (exit 0, no drift).
- `uv run python tools/check_docs_consistency.py --domain agent` and the ADR/docs gates listed in `rules/tool-gates.md`, since the ADR row 23 documents this manifest's ownership claims.

## Completion criteria
- The committed manifest contains no prompt rows, matches the registry source, and the drift check passes (AC-2).

## Out of Scope
- Registering `registry/manifests/prompt_source.toml` as a manifest type (Plan UNK-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | run the generator, do not hand-edit |
| 3 | Run the validation sequence (`rules/tool-gates.md`) | Pending | — | — | `generate_reference_table.py --check` |

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
- **Requirement ID**: `REQ-003` (no prompt entries in the regenerated ownership manifest)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `registry/manifests/config_ownership.yaml`
