## Goal

Regenerate the subpackage API table so the new service module and the new `MemoryStore` accessors appear in the generated block (REQ-010: generated artifacts reflect the implementation; AC-10).

## Scope
**Release unit**: R7-docs-generated (Phase 7)

- In scope: the generated block in `docs/23_agent/agent_14_reference-api-subpackages-generated.md`.

## Assumptions

- The file is never hand-edited between the guard comments; it is rendered from `registry/manifests/agent_api.yaml` (row 38), so this row runs after the manifest is regenerated.
- The symbols listed come from rows 1 and 12; this document does not define them.
- Step 2 overlap: this file is also a target row of `plans/20261124-095950_cliplc004_bounded-shutdown-machine.md` and `plans/20261124-110935_cliplc005_staged-reload-transaction.md`. All three plans regenerate it rather than edit it, so the changes are compatible; the regeneration must run after every plan's code rows have landed.

## Design decisions

- Generation only, as in the top-level table.

## Alternatives considered

- Hand-editing the table — rejected: a hand edit fails `tools/generate_reference_table.py --check` at the next run.

## Implementation
### Target file
`docs/23_agent/agent_14_reference-api-subpackages-generated.md`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --manifests` after row 38 regenerates the manifest.
2. Confirm the regenerated block lists the new service module (`scripts/agent/services/maintenance_jobs.py`, row 1) and the new `MemoryStore` accessors (row 12).

### Method

- No manual editing; the block is written by the generator.

### Details

- The `memory` symbols are rendered from `registry/manifests/memory_api.yaml` (row 39); both manifests must be regenerated in the same run before the block is re-rendered.

### Companion test files

- None. This is a generated artifact; its validation is the generator's drift check.

## Compatibility considerations

- Runs after every code row that adds public symbols.

## Security considerations

- N/A: generated documentation.

## Rollback considerations

- N/A: revert the Phase 7 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| This document | Generator | `uv run python tools/generate_reference_table.py --check` | No drift between manifest, block, and source |
| This document | Checkers | `uv run python tools/check_docs_structure.py docs/23_agent/agent_14_reference-api-subpackages-generated.md` | No finding |

## Completion criteria

- The generated subpackage table matches the source, and the drift check reports nothing.

## Out of Scope

- The top-level table (row 36), the manifests, the code that defines the symbols.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate from the manifests | Completed | 20261125-065134 | 20261125-065134 | Phase 7 Phase 4 part: the same generator run rendered the RagFtsRebuildResult row in the subpackage table; no hand editing. Phase 7 (R7) done: the generator run rendered the RagVecPruneResult row in the subpackage table; no hand editing. Deviation: the rendered RagVecPruneResult row landed in the Phase 6 commit with the manifest, for the same gate reason. |
| 2 | Run the generator drift check and the structure checker (`rules/tool-gates.md`) | Completed | 20261125-003636 | 20261125-003636 | generate_reference_table.py --check reports no drift. Deviation: check_docs_structure reports the file at 33078 B against the 32768 B limit; it was already over the limit at HEAD (32952 B), so the finding is pre-existing and the generated output cannot be shortened by hand. |

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
- **Requirement ID**: REQ-010 (generated artifacts reflect the implementation)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `docs/23_agent/agent_14_reference-api-subpackages-generated.md`