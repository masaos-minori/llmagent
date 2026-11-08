# Crawl loop abandons running tasks when the page budget is reached

## Priority
Medium

## Summary
`crawl_site` leaves its BFS loop with `break` when the persisted or scheduled budget is reached while `pending` still holds running tasks; nothing cancels or awaits them before the HTTP client context exits and the session database connection is closed.

## Background
Review finding F-013. Evidence (Explicit in code): in `scripts/rag/ingestion/orchestrator.py` `crawl_site`, the two budget checks execute `break` inside `while not queue.empty() or pending`; the `finally` block closes `session_db` and the enclosing `async with httpx.AsyncClient` exits right after. Tasks still in `pending` use the client and `session_db` (`get_conditional_headers`, `save_http`). The loop only logs task exceptions for tasks that finished through `asyncio.wait`.

## Problem
Orphaned tasks can fail with a closed client or connection, raise "Task exception was never retrieved", or write one more document after the crawl was declared finished.

## Reason for Change
A crawl that reaches `max_pages` is the normal way a bounded crawl ends, so the race is hit routinely.

## Implementation Intent
On every exit from the loop, cancel the remaining tasks and await them (collecting exceptions) before closing the client and the database connection.

## Target Files or Areas
- `scripts/rag/ingestion/orchestrator.py` (`crawl_site`)
- `tests/rag/ingestion/`

## Required Changes
- Cancel and gather pending tasks in the exit path (inside `finally`).
- Log task errors once, without raising during cleanup.
- Add a test where the budget is reached while tasks are in flight.

## Constraints
- Do not change the budget semantics.
- Cancellation must not leave a partially written document.

## Acceptance Criteria
- After `crawl_site` returns, no task created by it is still running.
- No "never retrieved" warning is produced by a budget-limited crawl.
- Documents written before the budget stop are intact.

## Testing Expectations
- Async test using a mock transport with slow responses and a small `max_pages`.
- ruff and mypy on touched files.

## Documentation Impact
No documentation change expected.

## Out of Scope
- Changing concurrency settings.

## Dependencies
N/A: none

## Unresolved Questions
Whether a task cancelled in the middle of `save_http` can leave a partial file is `Needs confirmation` (check the atomicity of the write).

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131231
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`, `tests/rag/ingestion/`
