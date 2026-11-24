## Goal

Regenerate the agent API table so the new public symbols in the job registry appear in the generated block (REQ-010: generated artifacts reflect the implementation; AC-10).

## Scope
**Release unit**: R7-docs-generated (Phase 7)

- In scope: the generated block in `docs/23_agent/agent_13_reference-api-generated.md`.

## Assumptions

- The file is never hand-edited between the guard comments; the content comes from `registry/manifests/agent_api.yaml` (row 38), so this row runs after the manifest is regenerated.
- The symbols that appear are the ones row 1 adds; this document does not define them.
- Step 2 overlap: this file is also a target row of `plans/20261124-095950_cliplc004_bounded-shutdown-machine.md`. Both plans regenerate it rather than edit it, so the content is whatever the manifests hold at regeneration time and no text conflicts: compatible, and the regeneration must run after both plans' code rows have landed.

## Design decisions

- Generation only. No prose is added to the file: the generator owns the whole block, and `--check` is the gate that confirms the manifest, the block, and the source agree.

## Alternatives considered

- Hand-editing the table — rejected: the file is a guarded generated artifact; a hand edit fails the drift check at the next run.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --manifests` after row 38 regenerates the manifest.
2. Confirm the regenerated block lists the new public symbols from `scripts/agent/services/maintenance_jobs.py` (row 1).

### Method

- No manual editing; the block is written by the generator.

### Details

- The subpackage symbols are rendered in `docs/23_agent/agent_14_reference-api-subpackages-generated.md` (row 37); the two documents are generated from the same manifest and must be regenerated in the same run.

### Companion test files

- None. This is a generated artifact; its validation is the generator's drift check.

## Compatibility considerations

- Runs after every code row that adds public symbols; running it earlier produces a block that does not match the source.

## Security considerations

- N/A: generated documentation.

## Rollback considerations

- N/A: revert the Phase 7 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| This document | Generator | `uv run python tools/generate_reference_table.py --check` | No drift between manifest, block, and source |
| This document | Checkers | `uv run python tools/check_docs_structure.py docs/23_agent/agent_13_reference-api-generated.md` | No finding |

## Completion criteria

- The generated table matches the source, and the drift check reports nothing.

## Out of Scope

- The subpackage table (row 37), the manifests (rows 38, 39), the code that defines the symbols.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate from the manifest | Pending | — | — | Phase 7 |
| 2 | Run the generator drift check and the structure checker (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`
