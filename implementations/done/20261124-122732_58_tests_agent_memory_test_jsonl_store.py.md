## Goal

Keep the Memory jsonl archive's append-only contract verified while the delete path gains a cancellation boundary, so an interrupted job cannot leave an archive event for a row that is gone (REQ-006: tracked long-running Memory work inside one transaction boundary, archive stays append-only; AC-6).

## Scope
**Release unit**: R5-memory-layering (Phase 5)

- In scope: the append-only contract cases in this file.
- Out of scope: the ordering rule itself, which is implemented in `scripts/agent/memory/write_ops.py` (row 14); the archive writer (`scripts/agent/memory/jsonl_store.py`), which is unchanged.

## Assumptions

- The contract stated in the file preamble (`tests/agent/memory/test_jsonl_store.py:2`) is the normative statement: the archive is append-only and replay-only, never rewritten. It is asserted by `test_write_does_not_destroy_existing_content` (`:182`).
- Row 14 keeps the order commit-then-append; this row asserts that order holds under interruption, it does not define it.

## Design decisions

- Assert the contract through the file's own write path plus the delete path's observable outcome: the archive is never truncated or rewritten, and an interrupted delete appends no event. A test that only counts entries cannot show that the order was kept.

## Alternatives considered

- Asserting the order by inspecting `write_ops.py` source — rejected: the contract is behavioral, and the file already verifies the storage path through `JsonlMemoryStore`.

## Implementation
### Target file
`tests/agent/memory/test_jsonl_store.py`

### Procedure
1. Add one case that runs the delete path with the cancellation event set before the commit and asserts that no event is appended (`append` is not called on the store).
2. Add one case that asserts the event is appended after the commit for a completed delete, so the event set matches the row set.
3. Keep the existing append-only and schema cases unchanged; the preamble line is not rewritten unless the wording no longer matches what the file asserts.

### Method

- Use the existing `tmp_path` store fixture for the archive cases; the delete path needs the session store fixture used by `tests/agent/commands/test_memory_data_ops.py` (row 45), so keep that case in the caller's file and reference the outcome here only when the store accessor is reachable without a second fixture.

### Details

- If both fixtures are needed for the same assertion, the interrupted-delete case belongs with the caller's test file (row 45) and this file keeps only the append-only part: no truncate, no rewrite, append-only mode.

## Compatibility considerations

- Runs in the same phase as rows 14 and 45; the row-level assertions for the delete path are in `tests/agent/commands/test_memory_data_ops.py` (row 45).
- The same contract text is repeated in `docs/23_agent/agent_11_04_memory-module-reference-generated.md:71`, which is a generated file and is not edited by hand (row 40).

## Security considerations

- N/A: test.

## Rollback considerations

- N/A: revert the Phase 5 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/memory/test_jsonl_store.py` | Unit | `uv run pytest tests/agent/memory/test_jsonl_store.py -q` | Append-only contract holds; no event for an interrupted delete |
| Same file | Related path | `uv run pytest tests/agent/commands/test_memory_data_ops.py -q` | Delete and event agree for completed and interrupted runs |

## Completion criteria

- The append-only cases still pass unchanged, and the new cases fail if the event is written before the commit or written for a rolled-back delete.

## Out of Scope

- `scripts/agent/memory/jsonl_store.py`, `scripts/agent/memory/write_ops.py` (row 14), the registry and job records.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the interrupted-delete and post-commit-order cases | Completed | — | 20261124-234217 | Phase 5 interrupted-delete case asserted in row 45's file per Details (needs the session-store fixture); this file keeps the append-only cases |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-234217 |  |

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
- **Requirement ID**: REQ-006 (long-running Memory maintenance as a tracked job with a transaction boundary; jsonl archive stays append-only)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `tests/agent/memory/test_jsonl_store.py`