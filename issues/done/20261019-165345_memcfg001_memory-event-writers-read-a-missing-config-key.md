# Memory change-event writers read a config key that does not exist, so delete, pin, unpin, and prune fail after committing

## Priority
High

## Summary
Fix the three Memory change-event writers that read `cfg["memory"]["memory_jsonl_dir"]` from the raw `agent.toml` dictionary, where no `memory` table exists, so that `/memory delete`, `/memory pin`, `/memory unpin`, and `/memory prune` write their JSONL change events instead of raising `KeyError` after the SQLite change has been committed. Make the tests exercise the real configuration shape.

## Background
- Found on 2026-10-19 while investigating production test pollution (see `plans/done/20261019-131444_plan.md`, testiso001); recorded then as a "latent bug seen" and filed now at the owner's request.
- `agent.toml` defines `memory_jsonl_dir` as a top-level key (`config/agent.toml`, in the "Memory" block). `agent/config_builders.py` reads it as a top-level key (`_get_str_or_default(cfg, "memory_jsonl_dir", "/opt/llm/memory")`), and `agent/factory.py` uses `ctx.cfg.memory.memory_jsonl_dir`.
- Per `docs/23_agent/agent_11_02_memory-gate-data-model-search.md` and `agent_09_01_data-layer-session-db.md`, JSONL is an append-only archive of memory lines and change events (`delete`, `pin`, `unpin`) used for import, export, and recovery; SQLite is authoritative. `docs/90_deployment/deployment_01_deployment.md` says `/memory rebuild` recovers memory from it and reproduces deletes and pins recorded as change events.

## Problem
- Three helpers load the flat configuration with `ConfigLoader().load("agent.toml")` and index `cfg["memory"]["memory_jsonl_dir"]`:
  - `scripts/agent/memory/write_ops.py::_emit_delete_event` (called by `delete`),
  - `scripts/agent/memory/pin_ops.py::_emit_event` (called by pin and unpin),
  - `scripts/agent/commands/memory_data_ops.py::_emit_prune_event` (called by `memory_prune`).
- Reproduced on 2026-10-19 in an isolated temporary database with the real configuration shape (throwaway test, removed afterwards): all three helpers raise `KeyError: 'memory'`. `write_ops.delete` commits the SQLite delete first, then raises: the row is gone (0 rows left) and the exception propagates.
- Effects in the `/memory` commands (Explicit in code): `memory_delete` and the pin and unpin command call the writer without a handler, so the user sees an exception, the success line and the audit record (`_emit_memory_audit`) after it are skipped, and no JSONL event is written. `memory_prune` deletes all matching rows through `prune_old_memories`, then fails on the first `_emit_prune_event`, so none of the pruned ids gets an event and the success message and audit record are skipped.
- Consequence for recovery: because delete and pin events are never written, a later `/memory rebuild` or import from the JSONL archive would bring deleted memories back and lose pins.
- Tests mask it (Explicit evidence): `tests/agent/commands/test_memory_data_ops.py` (the `_emit_prune_event` test) mocks the loaded configuration as `{"memory": {"memory_jsonl_dir": "/tmp/mem"}}`, the wrong shape; the other tests patch the helpers entirely (`tests/agent/memory/test_memory_store.py` patches `agent.memory.write_ops._emit_delete_event` and `agent.memory.pin_ops._emit_event`).
- Not observed in production: `/opt/llm/memory` is empty (no `memories.jsonl`), so the archive has not yet been affected; the production commands were not run.

## Reason for Change
- Correctness: four documented `/memory` commands cannot complete against the real configuration.
- Data integrity: the SQLite state and the JSONL archive diverge, and the divergence changes what a rebuild restores.
- The tests encode the wrong configuration shape, so the defect cannot be seen from the suite.

## Implementation Intent
- Read the directory from the correct, top-level `memory_jsonl_dir` key, with the same default as the configuration builder (`/opt/llm/memory`), in one shared place rather than three copies, so the writers and the factory agree on the archive path.
- Keep the SQLite-first rule: a failed archive append must still propagate so the caller can surface M-07, but a missing key must no longer be the cause.
- Fix the tests to use the real shape and add a test that runs the real configuration loader (under the isolated configuration from `tests/conftest.py`) through each writer and checks that an event line is appended.
- Do not change the commands' output text or the audit contract.

## Target Files or Areas
- `scripts/agent/memory/write_ops.py`
- `scripts/agent/memory/pin_ops.py`
- `scripts/agent/commands/memory_data_ops.py`
- A shared helper for the archive path: location Unknown (a new function in `scripts/agent/memory/`; confirm the layering during planning)
- `tests/agent/commands/test_memory_data_ops.py` (the mocked `{"memory": ...}` shape)
- `tests/agent/memory/test_memory_store.py` and new tests for the three writers (file Unknown)
- Documentation: Unknown (the archive path wording in `docs/23_agent/agent_09_01_data-layer-session-db.md` and `agent_11_02_memory-gate-data-model-search.md` is correct; none is expected to change)

## Required Changes
- Replace the three `cfg["memory"]["memory_jsonl_dir"]` reads with one shared function that returns the JSONL path from the top-level key with the builder's default.
- Correct the mocked configuration shape in `tests/agent/commands/test_memory_data_ops.py`.
- Add tests that call `write_ops.delete`, `pin_ops.pin` and `unpin`, and `_emit_prune_event` with the real loader (isolated configuration) and assert the event lines in `memories.jsonl` under the temporary root.
- Add a test that `memory_prune` writes one event per pruned id and still reports success.
- Verify the whole flow for `/memory delete`, `pin`, `unpin`, and `prune` in a command-level test that does not patch the writers.

## Constraints
- Do not read or write `/opt/llm` in tests or during implementation (the suite is isolated by `tests/conftest.py`; the archive then lands under the temporary root).
- Keep the SQLite-first behavior and the propagation of real append failures (M-07).
- Do not change the JSONL format or the archive file name.

## Acceptance Criteria
- With the real configuration shape, `delete`, pin, unpin, and prune append their change events and the commands print their success lines and write their audit records.
- No code under `scripts/` reads `cfg["memory"]["memory_jsonl_dir"]`; one shared function provides the path.
- A test fails if the nested shape is used again (it runs the real loader, not a mock of the nested dictionary).
- The existing Memory tests and the full suite pass, and the production snapshot (`/opt/llm/db/*.sqlite`, `/opt/llm/logs/*`) is unchanged by the test run.

## Testing Expectations
- Unit tests for each writer with the real loader and a temporary archive directory; a command-level test for `/memory delete`, `pin`, `unpin`, and `prune`.
- The `rules/toolchain.md` sequence, and documentation checkers only if a document changes.

## Documentation Impact
Not expected: the documents already describe the archive path and events correctly. Re-check `docs/23_agent/agent_09_01_data-layer-session-db.md` and `agent_11_02_memory-gate-data-model-search.md` during planning.

## Out of Scope
- Cleaning or backfilling any existing JSONL or SQLite data.
- Changing how `/memory rebuild` replays events, or the archive format.
- Running the commands against production.
- The error handling in the commands beyond what the fix needs.

## Dependencies
- N/A: none. No open issue under `issues/` overlaps; sibling check recorded 2026-10-19.
- Context: `tests/conftest.py` redirects `memory_jsonl_dir` into the temporary root (testiso001), so the new tests write there.

## Unresolved Questions
- Where the shared path function belongs (the memory package, or reuse of the factory's builder) without breaking the import layering.
- Whether any user has run these commands against a real configuration and relies on the current behavior (assumption: none; the failure is an exception).
- Whether other modules read the flat configuration with a nested shape (a search of `scripts/` for `memory_jsonl_dir` found only the three sites above, the builder, the factory, and `memory_rebuild_ops`, which uses `ctx.cfg`).

## AI Implementation Instruction
- Keep the diff minimal and limited to the target files; add one shared function rather than patching each read separately.
- Preserve the SQLite-first order and the exception propagation for real append failures.
- Do not touch `/opt/llm`; use the isolated temporary root in tests.
- Stop and report if the layering does not allow a shared function without a new dependency direction.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261019-165345
- **Related target files**: `scripts/agent/memory/write_ops.py`, `scripts/agent/memory/pin_ops.py`, `scripts/agent/commands/memory_data_ops.py`, `tests/agent/commands/test_memory_data_ops.py`
