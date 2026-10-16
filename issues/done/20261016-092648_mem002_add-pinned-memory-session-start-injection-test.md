# Add pinned memory session-start injection test and verify the pin-bypass claim

## Priority
Medium

## Summary
Add a test proving that a pinned memory is injected at the next session start, and verify the documented claim that pinned memories are injected regardless of the importance threshold. If the claim is false in code, resolve the code/docs mismatch.

## Background
`memo1.md` (task M-1) asked to confirm and complete `/memory` pin, unpin, and list support. Verified against the repository on 2026-10-16:
- `/memory list`, `delete`, `pin`, `unpin`, and `prune` are dispatched in `scripts/agent/commands/cmd_memory.py`; `pin`/`unpin` call `pin_ops.pin()`/`unpin()` through `scripts/agent/commands/memory_data_ops.py`, with a `memory_max_pinned` limit.
- `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md` already documents `pin`/`unpin`/`list`, and `agent_11_01` to `agent_11_03` already describe JSONL change events replayed by `rebuild`.
- The remaining parts of M-1 (rebuild replay of pins, `/memory` spec alignment, docs) are tracked by the open issue `issues/20261014-155503_mem001_implement-memory-command-spec.md` and are intentionally not duplicated here.
- The one M-1 item not covered by that issue is M-1-4: a test that a pinned memory is injected at the next session start.

## Problem
- `tests/agent/memory/test_memory_layer.py` `TestOnSessionStart` mocks the retriever and never sets `pinned=True`; no test in `tests/` exercises pinned injection (checked by searching for pinned usage in the memory and startup tests).
- `docs/23_agent/agent_11_01_memory-overview-and-modes.md` states that pinned entries are always injected at every session start regardless of the importance threshold. `FtsRetriever.top_semantic()` in `scripts/agent/memory/retriever.py` applies `importance >= min_importance` and `memory_type = 'semantic'` to every row, and only orders by `pinned DESC`. Under this code a pinned memory below the threshold, or a pinned episodic memory, appears not to be injected. This is a reading of the SQL, not yet confirmed by a test run.

## Reason for Change
Pin is only meaningful if a pinned memory reliably reaches the next session. Without a test, a regression in this path is invisible, and the documented behavior may already differ from the code.

## Implementation Intent
- Add a test at the real retriever/SQLite boundary (temporary DB, not a mocked retriever) that pins a memory and checks that `on_session_start()` returns it.
- Use the test result to decide: if a below-threshold pinned memory is not injected, that is a code/docs mismatch to settle (fix the code to match the docs, or correct the docs) once the intended behavior is confirmed.
- Keep the change minimal; do not rework retrieval scoring.

## Target Files or Areas
- `tests/agent/memory/test_memory_layer.py` or a new test module under `tests/agent/memory/`
- `scripts/agent/memory/retriever.py` (`top_semantic`), `scripts/agent/memory/injection.py` (`on_session_start`) — only if the mismatch is resolved in code
- `docs/23_agent/agent_11_01_memory-overview-and-modes.md` — only if the mismatch is resolved in docs

## Required Changes
- Add a test: a pinned memory with importance above the threshold is returned by session-start injection.
- Add a test: a pinned memory with importance below `min_importance` — assert the behavior chosen for the Unresolved Question below.
- Add a test: an unpinned memory below the threshold is not injected.
- If the tests show a code/docs mismatch, resolve it in the one place the confirmed intent points to.

## Constraints
- Tests must not open production DBs; use the sandbox config and patched DB helpers.
- Do not change the `/memory` command set or JSONL handling (covered by mem001).
- No compatibility shims.

## Acceptance Criteria
- A test fails if a pinned memory is dropped at session start under the intended rule.
- Documented behavior in `agent_11_01` and the code behavior of `top_semantic()` agree, verified by the added tests.
- `uv run pytest tests/agent/memory/` passes.

## Testing Expectations
- New unit/integration tests as above using a temporary SQLite DB.
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` if `scripts/` changes.
- If `docs/` changes: `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py`.
- If code under a generated-reference domain changes: `tools/generate_reference_table.py --check`.

## Documentation Impact
Update `agent_11_01` only if the confirmed intent differs from its current sentence about pinned injection regardless of the importance threshold. Otherwise no documentation change.

## Out of Scope
- `/memory` subcommand changes, pin limit, `rebuild` replay, JSONL change events (mem001).
- Changes to retrieval scoring or non-session-start injection.
- Production deployment.

## Dependencies
- Related to `issues/20261014-155503_mem001_implement-memory-command-spec.md` (same files area: `scripts/agent/memory/`). No fix order is required, but if mem001 changes `top_semantic()` or pin handling, re-verify this issue's Problem against current source first.

## Unresolved Questions
- Should a pinned memory below `min_importance` be injected (as `agent_11_01` states)? Assumed yes, per the docs.
- Should a pinned episodic memory be injected at session start, or only semantic ones? Unknown; the docs do not say.

## AI Implementation Instruction
Write the tests first and use their result to decide whether code or docs change. Ask the user if the intended pin behavior is unclear after the tests. Do not touch unrelated files, do not implement mem001 items, and never touch `/opt/llm`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261016-092648
- **Related target files**: tests/agent/memory/test_memory_layer.py, scripts/agent/memory/retriever.py, scripts/agent/memory/injection.py, docs/23_agent/agent_11_01_memory-overview-and-modes.md
