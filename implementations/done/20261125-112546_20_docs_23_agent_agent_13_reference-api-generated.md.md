## Goal
Regenerate the guarded `AUTO-GENERATED` reference block after the new `ReplayDirective` symbol is added under
`scripts/agent/` (declared by sibling procedure seq 06).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The block is generated, not hand-written (ADR-015 INV-01).

## Design decisions
- Run the generator in manifest mode: `--type agent` writes only this document and leaves the committed manifest
  stale against the sources rows 02 and 06 change.

## Alternatives considered
- Hand-editing the block — rejected: the `--check` gate fails whenever the block and the source diverge.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`

### Procedure
Refresh the `agent-class-function-reference` block.

### Method
Run `uv run python tools/generate_reference_table.py --manifests` after sibling procedure seq 06 adds the dataclass,
then commit the regenerated block. The same run writes `registry/manifests/agent_api.yaml` (row 24) and re-renders
`agent_14` (row 23), so the three rows are one generator run committed as one change set.

### Details
- Exactly one row is added: `ReplayDirective` in the `scripts/agent/tool_preparation.py` group, before
  `PreparedToolCall`. The subpackage symbols render into row 23, not here.
- This document stays under `MAX_SIZE` (28,948 B against 32,768 B), so no `SIZE_EXCEPTIONS` entry is needed.

## Compatibility considerations
The CI `lint` job runs `--check`, so the regenerated block must be committed with the code change.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_13_reference-api-generated.md`

## Completion criteria
The `--check` gate passes with `ReplayDirective` present in the block.

## Out of Scope
No change to the other guarded blocks in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the guarded agent reference block | Completed | — | 2026-11-25 | shared `--manifests` run with rows 23 and 24 shared --manifests run with rows 23 and 24; agent_13 gains exactly 1 row (ReplayDirective) |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | — | 2026-11-25 |  |

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
- **Requirement ID**: `REQ-007` (the generated reference block stays in step with the new symbol)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`