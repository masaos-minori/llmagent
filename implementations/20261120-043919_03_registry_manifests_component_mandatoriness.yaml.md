## Goal

Regenerate `registry/manifests/component_mandatoriness.yaml` from the edited
`registry/component_mandatoriness.yaml` so the committed manifest mirrors the corrected
`rag_pipeline` `safety_role` (REQ-008, AC-07).

## Scope
**Release unit**: mandatoriness-registry-refresh (same unit as the source registry edit,
sibling procedure `implementations/20261120-043919_02_registry_component_mandatoriness.yaml.md`)

## Assumptions

- The manifest is a generated artifact: the only permitted edit is running the generator, never
  hand-editing (generator contract, `tools/generate_reference_table.py:457`).

## Design decisions

- Regeneration runs through the generator CLI (`--manifests --type mandatoriness`), not by
  editing the YAML — the manifest has no hand-edit exemption (unlike the governance_01
  Resolution Matrix row).

## Alternatives considered

- N/A: hand-editing a generated manifest violates the generator contract and would drift on the
  next regeneration.

## Implementation
### Target file
`registry/manifests/component_mandatoriness.yaml`

### Procedure
1. After the sibling registry edit (procedure 02) lands, run
   `uv run python tools/generate_reference_table.py --manifests --type mandatoriness`.
2. Confirm the diff contains only the `rag_pipeline` `safety_role` line (manifest line 97) and
   the manifest header timestamp (`generated:`, line 4).

### Method
- The generator path is `component_mandatoriness` domain → manifest builder
  `_component_mandatoriness_entries()` (`tools/generate_reference_table.py:917`), which copies
  `safety_role`/`failure_category` (`tools/generate_reference_table.py:955-956`) from the registry
  through the shared loader vocabulary (`scripts/shared/component_mandatoriness.py`).

### Details
- `--manifests` also re-renders guarded doc blocks from committed manifests; with `--type
  mandatoriness` the scope stays on the mandatoriness domain (its doc is `agent_08_04`, whose
  visible table shows only Server/Classification/Rationale and stays byte-identical — Plan
  Design decision 4).
- No test file row: the manifest is validated by the drift gate, not unit tests of its own.

## Compatibility considerations

- Must land in the same commit as the source registry edit (release unit rule); a manifest
  regenerated before the registry edit would reintroduce the wrong `safety_role`, and a registry
  edit without regeneration fails `--check`.

## Security considerations

- N/A: generated copy of already-approved values; no classification semantics change.

## Rollback considerations

- Revert together with the source registry edit (same release unit).

## Validation plan

- `uv run python tools/generate_reference_table.py --check` exit 0 (AC-07).
- `rg "ingestion" registry/manifests/component_mandatoriness.yaml` returns nothing after
  regeneration.
- `uv run pytest tests/tools/test_generate_reference_table.py` passes.

## Completion criteria

- The manifest's `rag_pipeline` entry mirrors the corrected registry `safety_role`; the drift
  gate exits 0; the diff touches only the mirrored value and the generated header timestamp
  (Plan AC-07).

## Out of Scope

- Any hand-editing of the manifest.
- The source registry edit itself (procedure 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run generate_reference_table --manifests --type mandatoriness after procedure 02 | Pending | — | — | Same commit as procedure 02 |
| 2 | Run --check drift gate and generate_reference_table tests | Pending | — | — | |

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
- **Requirement ID**: `REQ-008` (regenerate committed manifests so they mirror live sources)
- **Source issue**: issues/20261117-123020_adrchk020_mandatoriness-registry-posture.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-001311_adrchk020_mandatoriness-registry-posture.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-043919
- **Related target files**: `registry/manifests/component_mandatoriness.yaml`
