## Goal

Run the jsonl import as a tracked job with a cancellation boundary and a verified post-import count, so a long-running Memory write has a job record and a measured outcome (REQ-006: long-running Memory work as tracked jobs; AC-6).

## Scope
**Release unit**: R5-memory-layering (Phase 5)

- In scope: `import_from_jsonl`.
- Out of scope: the registry, the command handler that invokes the import, the append-only event contract (row 58).

## Assumptions

- The archive replay logic (top-to-bottom reconstruction before any write) is unchanged; only the transaction boundary and the postcondition are added.
- `allow_loss` remains a recorded grant on the job, not the authority that permits the run (plan decision, 2026-11-24).

## Design decisions

- The existing `ValueError` for `backup=True` without `allow_loss=True` (`scripts/agent/memory/import_ops.py:81-83`) stays; the message names the job id when the run was registered.
- The post-import count is measured after the commit, so the reported count is the committed count, not the number of statements attempted.

## Alternatives considered

- Keeping the import untracked because it is usually short — rejected: the plan requires a record for every maintenance run, and the import is the long-running Memory write path.

## Implementation
### Target file
`scripts/agent/memory/import_ops.py`

### Procedure
1. Take the job's cancellation event (`stop: threading.Event | None`) and pass it to `SQLiteHelper.interrupt_when`.
2. Run the inserts inside one transaction boundary owned by the `MemoryStore` accessor (row 12).
3. Return a result object with the verified post-import count and the interrupted flag instead of `tuple[int, int]`.

### Method
- The function signature keeps `jsonl_store`, `dry_run`, `embed_dim`, `backup`, `allow_loss`, `db_config`; only `stop` and the return type change.

### Details
- `skipped` counting behavior is preserved; `dry_run` performs no write and registers no job.

### Companion test files
- `tests/agent/memory/test_import_ops.py`
  - Procedure: assert the import runs under the registry with the cancellation boundary honored and the post-import count verified.
  - Validation: `uv run pytest tests/agent/memory/test_import_ops.py -q` (REQ-006; AC-6).

## Compatibility considerations

- The consumer scan for `import_from_jsonl` records 4 scripts and 42 tests; the return-type change lands with the call-site updates in the same commit.

## Security considerations

- Import is a write against `session.sqlite`; the run is recorded so the one-writer guard sees it.

## Rollback considerations

- N/A: revert the Phase 5 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/memory/import_ops.py` | Unit | `uv run pytest tests/agent/memory/test_import_ops.py tests/agent/memory -q` | Tracked import, cancellation boundary, verified count |
| Same file | Quality gates | `uv run ruff check scripts/agent/memory/import_ops.py`, `uv run mypy scripts/agent/memory/import_ops.py` | No finding |

## Completion criteria

- An import run has a job record, can be cancelled at a transaction boundary, and reports the count that was actually committed; an interrupted run reports `cancelled`, not success.

## Out of Scope

- The registry, the handler, the jsonl append-only contract.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the cancellation event and transaction boundary, return the verified result | Pending | — | — | Phase 5 |
| 2 | Update the companion test per Validation plan | Pending | — | — | Covered by this document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-006 (tracked long-running Memory work with a cancellation boundary)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/memory/import_ops.py`, `tests/agent/memory/test_import_ops.py`
