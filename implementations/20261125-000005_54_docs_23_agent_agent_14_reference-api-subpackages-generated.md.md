## Goal

Regenerate the subpackage API reference so the new `db.write_gate` module and its exported symbols appear in the generated block (REQ-004: writes stop when shutdown starts; REQ-010: termination bounded by the shutdown deadline).

## Scope
**Release unit**: R7-reporting-and-docs (Phase 7)

- In scope: the generated block in `docs/23_agent/agent_14_reference-api-subpackages-generated.md`.

## Assumptions

- The file is a guarded generated artifact: its content comes from the manifests row 55 regenerates, so this row runs after the manifest.
- The symbols that appear are the ones rows 2 and 4 define (`WriteGate` (new), `WriteGateClosed` (new), and the package exports); this document does not define them.
- Overlap: this file is also a target row of the frozen cliplc005 Plan (`plans/20261124-110935_cliplc005_staged-reload-transaction.md`) and of the cliplc003 Plan (`plans/done/20261124-001800_cliplc003_maintenance-job-framework.md`). All three regenerate rather than edit, so the block reflects whatever the source holds at regeneration time and no text conflict is possible.

## Design decisions

- Generation only: the generator owns the block, and `--check` is the gate that confirms manifest, block, and source agree.
- Regenerate in the same run as row 53, because both documents are rendered from the same manifest and a run that updates one leaves the other stale.

## Alternatives considered

- Describe the gate symbols in prose here — rejected: this file is generated, and prose added to it is overwritten by the next generation run.

## Implementation
### Target file
`docs/23_agent/agent_14_reference-api-subpackages-generated.md`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --manifests` after row 55 regenerates the manifest.
2. Confirm the regenerated block lists the `db.write_gate` module and the symbols row 4 exports from `scripts/db/__init__.py`.

### Method

- No manual editing; the block is written by the generator.

### Details

- The architecture-level description of the gate lives in `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` (row 52); this file only lists the symbols.

### Companion test files

- None. This is a generated artifact; its validation is the generator's drift check.

## Compatibility considerations

- Runs after rows 2, 3 and 4: a gate that is not yet exported cannot appear in the block.
- The cliplc005 Plan regenerates the same file after its own code rows land; re-run `tools/check_plan_target_overlaps.py` after each landing.

## Security considerations

- N/A: generated documentation.

## Rollback considerations

- N/A: revert the Phase 7 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| This document | Generator | `uv run python tools/generate_reference_table.py --check` | No drift between manifest, block, and source |
| This document | Docs | `uv run python tools/check_docs_structure.py docs/23_agent/agent_14_reference-api-subpackages-generated.md` | No finding |
| This document | Docs | `uv run python tools/check_docs_quality.py` | No finding |

## Completion criteria

- The generated subpackage table lists the gate module and its exports, and the drift check reports nothing.

## Out of Scope

- The agent-level table (row 53), the manifest (row 55), and the gate implementation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate from the manifest | Pending | — | — | Phase 7 |
| 2 | Run the generator drift check and the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (writes stop when shutdown starts), REQ-010 (termination bounded by the shutdown deadline)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `docs/23_agent/agent_14_reference-api-subpackages-generated.md`
