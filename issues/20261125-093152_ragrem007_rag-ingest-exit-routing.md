# Make ingestion results, CLI exit status, and post-commit routing accurate and recoverable

## Priority
High

## Summary
Return a structured ingestion summary, exit non-zero for rejected groups or unverifiable consistency, and make routing of artifacts after a DB commit explicit and retryable.

## Background
Verified against master on 2026-11-25 (source: `memo-issue.md` H-07):
- Confirmed: the ingestion `main()` returns `None` and calls `ingester.ingest_all(args.force)` without using the result (`scripts/rag/ingestion/ingester.py:461-477`); `ingest_all` returns the consistency report or `None` (`:139-198`).
- Confirmed: `FileRouter.route` catches `OSError` on file moves and logs it (`scripts/rag/ingestion/file_routing.py:56-101`), so a routing failure after commit is not part of any result.
- Not verified: that failure counters miss chunks rejected by group-level atomicity; the per-URL result has `n_failed` (`ingester.py:44-76`) but the aggregation was not traced.
- Not verified: how `deploy/deploy.sh`, `deploy/setup_services.sh`, systemd, or cron invoke ingestion (they mention the ingester; their use of the exit code was not read).

## Problem
Automation sees exit code 0 for failed groups or unverified consistency, and a committed-but-unrouted artifact has no recorded state or retry path.

## Reason for Change
Schedulers and operators cannot trust the process status, and recovery from a partial routing failure is manual.

## Implementation Intent
`ingest_all()` returns a summary (successful and failed groups and chunks, embedding failures, rolled-back chunks, routing failures); `main()` returns an integer exit code derived from it; `FileRouter.route()` returns structured results including `db_committed_routing_pending`, backed by a journal that makes retry idempotent.

## Target Files or Areas
- `scripts/rag/ingestion/ingester.py`, `document_manager.py`, `transaction_commit.py`, `file_routing.py`
- `tests/rag/ingestion/`, deployment callers under `deploy/` (read-only check)

## Required Changes
- Structured summary from `ingest_all()`; count every chunk of a rejected generation as failed while keeping the original cause.
- `main()` returns an int, `sys.exit(main())`; non-zero for any rejected group and for unavailable, timed-out, or failed required consistency verification; define the code for a confirmed inconsistency.
- Structured routing results, a recoverable routing journal, idempotent retry (no duplicate DB rows, deterministic destination conflict rule).
- Remove unused transaction parameters once the boundary is final.

## Constraints
- Keep group-level atomicity.
- Exit codes must be documented and stable for schedulers.

## Acceptance Criteria
- Full success exits 0; any rejected group exits non-zero; unverifiable or inconsistent completion does not exit 0.
- Summary counts match committed rows and routed files; a file-move failure is visible in the run result.
- A retry completes routing without duplicate DB rows; destination conflicts follow the documented rule.

## Testing Expectations
Failure-injection tests for move failures, rejected groups, and consistency states; retry idempotency tests; whole-suite run and changed-path gates.

## Documentation Impact
Document the ingestion exit codes and the routing recovery procedure in the ingestion operations documents.

## Out of Scope
- Artifact envelope and generations (issues/20261125-093151_ragrem006_rag-artifact-generations.md).

## Dependencies
- Depends on issues/20261125-093151_ragrem006_rag-artifact-generations.md.
- Related: the consistency verification states in issues/20261125-093148_ragrem003_rag-consistency-structured-probes.md.

## Unresolved Questions
- `不明`: how production schedulers call ingestion and whether they honor the exit code.
- `不明`: the exit code value for a confirmed post-ingestion inconsistency.

## AI Implementation Instruction
Read the deployment callers before fixing exit-code semantics; keep changes inside the listed modules.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-093152
- **Related target files**: `scripts/rag/ingestion/ingester.py`, `scripts/rag/ingestion/file_routing.py`, `scripts/rag/ingestion/transaction_commit.py`
