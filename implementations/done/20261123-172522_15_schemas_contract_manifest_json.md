## Goal

Register the `agent_config_migration` manifest identity in the contract-manifest schema so the agent-config migration domain's committed manifest can be validated and drift-checked (REQ-002 - the single-source mapping has a schema-validated artifact).

## Scope
**Release unit**: RU-1 generator-and-generated-block

One file is modified: the contract-manifest JSON Schema. The generator is sibling procedure seq 04 and seq 12, the committed artifact is seq 13, the destination document is seq 06.

## Assumptions
- `tools/_contract_manifests.py` `validate_manifest()` validates every manifest against this schema, and the schema's `manifest` property `enum` is the only list of allowed identities, so a domain with no enum entry cannot be written or drift-checked.
- The row was added after execution (owner approval, 2026-11-23) as the additional-target-file discovery recorded in procedure seq 13; the change was already landed as the minimum the validation required, so this document records the confirmed scope rather than authorising new work.

## Design decisions
- Entry shape `key` + `replacement` only, matching what seq 12's builder emits, with `additionalProperties: false` like the other per-manifest branches.
- Natural key `key` is the removed key read from the validator mapping, so the sorted, byte-stable committed YAML is keyed by the mapping itself.

## Alternatives considered
Leaving the schema unchanged (entries fall back to the generic `items: object` branch) was rejected: the per-manifest branch is the only place an entry shape is enforced, and the generic branch enforces nothing.

## Implementation
### Target file
`schemas/contract_manifest.json`
### Procedure
1. Add `agent_config_migration` to the `manifest` enum.
2. Add the `allOf` branch for that name with the `key` + `replacement` entry shape.
### Method
The schema is the single source of manifest identities; the tool reads no name list from elsewhere, so the enum entry is what makes the domain valid.
### Details
- No test file is added for the schema itself: the manifest write path validates against it, and the companion test file already exercises that path for the domain.

## Compatibility considerations
No existing manifest identity or entry shape changes; the added branch applies only to the new name.

## Security considerations
N/A: static schema definition, no execution of parsed content.

## Rollback considerations
N/A: revert the commit; `--check` then reports the domain's manifest as invalid until seq 12 and seq 13 are reverted with it.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` reports no drift for the domain.
- `uv run pytest tests/tools/test_generate_reference_table.py`

## Completion criteria
The committed manifest validates through the tool's write path, and the shape the schema enforces is the shape the generator emits.

## Out of Scope
The generator and its renderer (seq 04, seq 12); the committed manifest content (seq 13); the destination document (seq 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the enum name and the entry-shape branch per Procedure/Method | Completed | 2026-11-23 | 2026-11-23 | Landed during seq 13 execution; confirmed against live source at row creation (2026-11-23) |
| 2 | Run the validation named in Validation plan | Completed | 2026-11-23 | 2026-11-23 | `--check` reports "No drift found"; `tests/tools/test_generate_reference_table.py` 33 passed |

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
- **Requirement ID**: `REQ-002` (single-source migration mapping with a schema-validated artifact)
- **Source issue**: `issues/done/20261120-114214_agentcfg006_reduction-integration-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261122-190238_agentcfg006_reduction-integration-verification.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-172522
- **Related target files**: `schemas/contract_manifest.json`
