## Goal

Regenerate the config ownership manifest from the modified field registry, so the generated artifact
matches the registry's `hot_reloadable` and validator wiring rather than a hand-edited list (REQ-003,
startup-only fields stay pending; REQ-010, registry completeness; REQ-014, documentation).

## Scope
**Release unit**: R7-docs-and-manifests

## Assumptions
- Verified against current source: `registry/manifests/config_ownership.yaml` is generated from
  `scripts/agent/services/config_field_registry.py` by `tools/generate_reference_table.py`
  (`CONFIG_FIELD_REGISTRY_SRC`); it is never hand-edited.
- The registry gains `field_type` and `allow_empty` in row 4, so the regenerated manifest is the record of
  that change.

## Design decisions
- The manifest is regenerated after the registry lands, so the artifact and the source cannot disagree.
- No manifest field is added by hand; a new column would require changing the generator, which is out of
  scope here.

## Alternatives considered
- Hand-editing the manifest to match the plan — rejected: the generator is the source of truth.

## Implementation
### Target file
`registry/manifests/config_ownership.yaml`

### Procedure

### Method
- Run `uv run python tools/generate_reference_table.py --manifests` after row 4 lands and commit the result.

### Details
- The regenerated file must show every entry with a validator and the hot-reloadable subset unchanged in
  membership except for the fields row 4 declares.

## Compatibility considerations
- N/A: generated artifact; consumers read it as data.

## Security considerations
- N/A: the manifest records field ownership, not values.

## Rollback considerations
- N/A: revert the Phase 7 commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check --manifests`

## Completion criteria
- The check passes against the modified registry, and the committed manifest differs from the previous
  version only by the registry change row 4 made.

## Out of Scope
- The registry itself (row 4).
- The generated API reference (row 46).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | runs after row 4 |
| 2 | Run the generated-artifact check (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (startup-only fields stay pending), REQ-010 (registry completeness), REQ-014 (documentation); AC-6
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `registry/manifests/config_ownership.yaml`
