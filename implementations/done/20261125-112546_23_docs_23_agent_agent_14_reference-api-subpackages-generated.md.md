## Goal
Regenerate the guarded subpackage reference block so the three symbols this Plan adds to `scripts/agent/`
subpackages appear: `TurnControl`, `reconstruct_replay_directives`, and the changed `record_tool_call` signature.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The block is generated, not hand-written (ADR-015 INV-01), and it renders from the committed manifest (row 24).
- The symbols it lists are defined by rows 02 and 07; this document does not define them.

## Design decisions
- Run the generator in manifest mode: the block renders from the committed manifest, which is currently stale, so
  `--type agent_subpackages` would re-render the stale block.

## Alternatives considered
- Hand-edit the three rows — rejected: the drift gate fails whenever the block and the manifest diverge.

## Implementation
### Target file
`docs/23_agent/agent_14_reference-api-subpackages-generated.md`

### Procedure
Refresh the `agent-subpackages-class-function-reference` block through the shared `--manifests` run of row 24, after
rows 02 and 07 have landed.

### Method
`uv run python tools/generate_reference_table.py --manifests`

### Details
- Exactly three table rows change: `record_tool_call` gains `args_hash`, `reconstruct_replay_directives` is added
  (`scripts/agent/workflow/tool_call_state_ops.py` group), and `TurnControl` is added
  (`scripts/agent/workflow/workflow_engine.py` group). The welcome line and the rest of the block are unchanged.
- The document reaches 33,392 B, past its recorded `SIZE_EXCEPTIONS` ceiling of 33,078, so row 25 must be applied
  before the size gate can pass.

## Compatibility considerations
The CI `lint` job runs `--check`, so the regenerated block must be committed with the code change and with rows 20,
24, 25 in the same change set.

## Security considerations
N/A: generated documentation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_14_reference-api-subpackages-generated.md`
- `uv run python tools/check_docs_consistency.py --domain agent`

## Completion criteria
The block lists the three changed rows and the drift check reports nothing.

## Out of Scope
The top-level agent table (row 20), the manifest (row 24), the per-file ceiling (row 25), and the code that defines
the symbols.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the guarded subpackage block through the shared `--manifests` run | Completed | 20261125-131500 | 2026-11-25 | shared run with rows 20 and 24; exactly 3 rows changed as expected |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261125-131600 | 2026-11-25 | size gate pending row 25 blocker resolved by row 25: all docs gates pass at the re-accepted ceiling 33,392 B |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | `check_docs_structure.py` reports agent_14 at 33,392 B against the recorded ceiling 33,078; the ceiling is re-recorded by plan row 25, which must be applied before this gate can pass. | Yes | 2026-11-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-007` (the generated reference block stays in step with the new symbols)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `docs/23_agent/agent_14_reference-api-subpackages-generated.md`