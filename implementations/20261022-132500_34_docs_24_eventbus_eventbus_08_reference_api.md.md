## Goal
Remove the `offsets.py` sentence and regenerate the generated reference block (REQ-005).

## Scope
- In: delete the prose sentence about `offsets.py`, remove the `offsets_dir` reference(s), and regenerate the guarded block with `tools/generate_reference_table.py`.
- Out: the other modules' rows (regenerated output may change them only if source changed; keep unrelated diffs out).

## Assumptions
- The block rows for `CorruptOffsetError`, `read_offset`, and `write_offset` (about lines 105-107) come from the generator; do not hand-edit them.
- Run only after seq 01 (module deleted) so the generator no longer emits them.

## Design decisions
- Hand-edit the prose; regenerate the block with the tool, then check with `--check`.

## Alternatives considered
Hand-deleting generated rows was rejected: `--check` would still be the arbiter and a hand edit can drift.

## Implementation
### Target file
`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure
1. Delete the prose sentence naming `offsets.py` and any `offsets_dir` mention.
2. `uv run python tools/generate_reference_table.py --type eventbus`.
3. `uv run python tools/generate_reference_table.py --check`.
4. Inspect `git diff` of the file: only offsets-related lines may change (other plans may add unrelated changes; keep them).

### Method
Text edit plus generator run.

### Details
- The generated block is delimited by guard markers; do not edit inside them manually.

## Compatibility considerations
Documentation of current behavior only.

## Security considerations
N/A: documentation.

## Rollback considerations
N/A: revert the commit and re-run the generator.

## Validation plan
- `generate_reference_table.py --check`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` pass; `rg "offsets\.py|read_offset|write_offset|offsets_dir" docs/24_eventbus/eventbus_08_reference_api.md` returns no match.

## Completion criteria
- No offsets-module text or rows remain and the generated block is current (REQ-005; Plan AC-5).

## Out of Scope
Every other file of the Plan (each has its own procedure document); ADR text (Plan UNK-01); deleting `/opt/llm/offsets` (Plan UNK-03); offset storage, monotonic advancement, ACK-advanced offsets, and resume computation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the prose and regenerate the block | Pending | — | — | |
| 2 | Run the generator check and the documentation checkers | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (reference document of the removed module)
- **Source issue**: `issues/20261022-124119_offhelper_remove-unused-file-offset-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-125806_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-132500
- **Related target files**: `docs/24_eventbus/eventbus_08_reference_api.md`
