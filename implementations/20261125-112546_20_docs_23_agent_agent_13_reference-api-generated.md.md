## Goal
Regenerate the guarded `AUTO-GENERATED` reference block after the new `ReplayDirective` symbol is added under
`scripts/agent/` (declared by sibling procedure seq 06).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The block is generated, not hand-written: the change is the generator output committed in the same change set
  (ADR-015 INV-01).

## Design decisions
- Run the generator for the agent domain rather than editing the table by hand.

## Alternatives considered
- Hand-editing the block — rejected: the `--check` gate fails whenever the block and the source diverge.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`

### Procedure
Refresh the `agent-class-function-reference` block.

### Method
Run `uv run python tools/generate_reference_table.py --type agent` after sibling procedure seq 06 adds the dataclass,
then commit the regenerated block.

### Details
- The block lists classes under `scripts/agent/`, so only the new dataclass row appears; no other row changes.

## Compatibility considerations
The CI `lint` job runs `uv run python tools/generate_reference_table.py --check`, so the regenerated block must be
committed with the code change, not in a later commit.

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
| 1 | Regenerate the guarded agent reference block | Pending | — | — | |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
