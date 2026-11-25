## Goal

Regenerate the agent API reference table so the new shutdown module and the changed lifecycle signatures appear in the generated block (REQ-001: one owner and sequence; REQ-010: termination bounded by the shutdown deadline; REQ-012: every step reported).

## Scope
**Release unit**: R7-reporting-and-docs (Phase 7)

- In scope: the generated block in `docs/23_agent/agent_13_reference-api-generated.md`.

## Assumptions

- The file is never hand-edited between the guard comments: its content comes from `registry/manifests/agent_api.yaml` (row 55), so this row runs after the manifest is regenerated.
- The symbols that appear are the ones rows 1, 5, 11, 13, 14 and 15 define; this document does not define them.
- Overlap: this file is also a target row of the cliplc003 Plan (`plans/done/20261124-001800_cliplc003_maintenance-job-framework.md`), whose procedures under `implementations/20261124-122732_` land first, and of the frozen cliplc005 Plan (`plans/20261124-110935_cliplc005_staged-reload-transaction.md`). Both regenerate rather than edit, so the content is whatever the manifests hold at regeneration time and no text conflict is possible.

## Step 3b verification against the current source (20261125-122600)

- The regeneration ran (`tools/generate_reference_table.py --manifests`) and produced no diff: the manifest and both generated blocks were already current at HEAD, and `--check --manifests` reports no drift.
- Procedure step 2 is corrected against the generator's scope: the `agent_api` manifest records top-level public classes and functions of `scripts/agent` (`_MANIFEST_SOURCES`, `tools/generate_reference_table.py:527`), not method signatures, so no `shutdown_all()` signature appears in the block. What the block does record is the shutdown surface as class entries — `ShutdownBudget` and its members from `scripts/agent/shutdown_budget.py` (`registry/manifests/agent_api.yaml:1487-1511`, rendered at `docs/23_agent/agent_13_reference-api-generated.md:142`), plus `ResourceShutdownCoordinator`, `ShutdownCoordinator`, `ProcessTerminator`, `ReplInputLoop`, and `SignalHandler` entries.

## Design decisions

- Generation only: no prose is added, because the generator owns the whole block and `--check` is the gate that confirms manifest, block, and source agree.
- Run the regeneration once for the whole Plan, after every code row has landed, rather than once per row: a partial regeneration would produce a block that matches only part of the source.

## Alternatives considered

- Hand-edit the table to add the new signatures — rejected: the file is a guarded generated artifact, and a hand edit fails the drift check at the next run.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --manifests` after row 55 regenerates the manifest.
2. Confirm the regenerated block lists `scripts/agent/shutdown_budget.py` and the `shutdown_all()` signatures that accept the remaining deadline.

### Method

- No manual editing; the block is written by the generator.

### Details

- The subpackage symbols are rendered in `docs/23_agent/agent_14_reference-api-subpackages-generated.md` (row 54) from the same manifest, so both documents are regenerated in the same run.

### Companion test files

- None. This is a generated artifact; its validation is the generator's drift check.

## Compatibility considerations

- Runs after every code row that adds or changes a public symbol; running it earlier produces a block that does not match the source.
- The cliplc005 Plan regenerates the same file after its own code rows land; re-run `tools/check_plan_target_overlaps.py` after each landing.

## Security considerations

- N/A: generated documentation.

## Rollback considerations

- N/A: revert the Phase 7 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| This document | Generator | `uv run python tools/generate_reference_table.py --check` | No drift between manifest, block, and source |
| This document | Docs | `uv run python tools/check_docs_structure.py docs/23_agent/agent_13_reference-api-generated.md` | No finding |
| This document | Docs | `uv run python tools/check_docs_quality.py` | No finding |

## Completion criteria

- The generated table matches the source, and the drift check reports nothing.

## Out of Scope

- The subpackage table (row 54), the manifest (row 55), and the code that defines the symbols.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate from the manifest | Completed | 20261125-130118 | 20261125-130118 | Phase 7 Regenerated with row 55's command; no diff, blocks already current; Step 3b note added |
| 2 | Run the generator drift check and the documentation checkers (`rules/tool-gates.md`) | Completed | 20261125-130118 | 20261125-130118 | --check --manifests: no drift; structure and quality clean |

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
- **Requirement ID**: REQ-001 (one owner and sequence), REQ-010 (termination bounded by the shutdown deadline), REQ-012 (every step reported)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`