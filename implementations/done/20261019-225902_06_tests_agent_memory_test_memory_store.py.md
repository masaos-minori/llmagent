## Goal

Add writer-level tests that exercise the real config-load-and-append path for `write_ops.delete`, `pin_ops.pin`/`unpin`, and `memory_data_ops._emit_prune_event` (REQ-006), asserting the emitted event line lands under the isolated temporary root. These replace the mock-based coverage that currently hides the nested-shape defect.

## Scope

- Modify only `tests/agent/memory/test_memory_store.py`.
- Add new writer-level tests that call the real writers WITHOUT patching `_emit_delete_event`/`_emit_event`/`_emit_prune_event`.

## Assumptions

- `conftest.py` sets `LLMAGENT_CONFIG_DIR` to a temp copy of `config/` where `memory_jsonl_dir` is rewritten to `{root}/memory`, so the real writers append to a temp-path `memories.jsonl` (UNK-02 resolved).
- The autouse `/opt/llm` guard fails any test that opens a production path; the rewritten temp path keeps these tests inside the isolation root.
- Existing `TestDelete` has an autouse fixture that patches `agent.memory.write_ops._emit_delete_event` (line 252-254); a real-loader delete test must live in a different class so that patch does not apply.

## Design decisions

- **New dedicated test class** (e.g. `TestRealWriterArchive`) with NO emit-patching autouse fixture, so the writers run end-to-end against the real config.
- **Assert on the archive file**, not on a mock: resolve the archive dir from the isolated config (`ConfigLoader().load("agent.toml")["memory_jsonl_dir"]`) and assert the expected event line is present in `<memory_dir>/memories.jsonl`.
- **Cover all three writers**: one delete (via `write_ops.delete`), one pin and one unpin (via `pin_ops.pin`/`unpin`), and one prune (via `memory_data_ops._emit_prune_event`).

## Alternatives considered

- **Reuse `TestDelete`/`TestPin` with the patch removed** — risk of disturbing existing characterization tests; additive new class is safer and keeps the intent explicit.

## Implementation

### Target file
`tests/agent/memory/test_memory_store.py`

### Procedure
1. Open `tests/agent/memory/test_memory_store.py`. Confirm the existing `TestDelete` autouse emit-patch (lines 252-254) and the pin emit patch (around line 533) — do NOT remove them; they belong to their characterization tests.
2. Add a new class `TestRealWriterArchive` at the end of the file (or after `TestDelete`):
   - No autouse emit patch.
   - Helper to resolve the archive path: `from shared.config_loader import ConfigLoader; memory_dir = ConfigLoader().load("agent.toml")["memory_jsonl_dir"]; archive = Path(memory_dir) / "memories.jsonl"`.
   - `test_delete_emits_real_event`: provision an entry, call `delete(entry.memory_id)`, assert `archive` contains a `delete` event line for `entry.memory_id`.
   - `test_pin_emits_real_event` / `test_unpin_emits_real_event`: provision an entry, call `pin(...)`/`unpin(...)`, assert the corresponding `pin`/`unpin` event line is present.
   - `test_prune_emit_writes_real_event`: call `memory_data_ops._emit_prune_event("id-xyz")` directly and assert the `delete` event line is present in `archive`.
3. Each assertion reads `archive` text and checks for the id/event; keep assertions tied to the temp-root path.

### Method
Additive real-loader tests; the writers run unmocked and write to the temp archive, which the tests read back.

### Details
- To avoid cross-test contamination on the shared `memories.jsonl`, either use distinct ids per test or clear/reopen the archive between assertions as the file's existing conventions require (check how `memories.jsonl` is managed elsewhere in this file).
- Ensure the session DB exists for `delete()`/`pin()` (the isolation root provisions it; existing `TestDelete` relies on the same).
- Do not modify existing test classes or fixtures beyond adding the new class.

## Compatibility considerations
Test-only addition. The new class must not inherit the `TestDelete` autouse patch — place it outside that class.

## Security considerations
N/A: test-only; assertions stay under the isolated temp root.

## Rollback considerations
Revert the added class from this test file.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `TestRealWriterArchive` | Real loaders: delete/pin/unpin/prune append events to temp archive | `uv run pytest tests/agent/memory/test_memory_store.py` | all pass; event lines present; no `/opt/llm` write |
| Existing `TestDelete`/pin characterization tests | Regression: emit mocks still work | `uv run pytest tests/agent/memory/test_memory_store.py` | unchanged, pass |

## Completion criteria

- New writer-level tests call `delete`/`pin`/`unpin`/`_emit_prune_event` against the real config loader and assert the emitted event line under the temp root.
- Existing mock-based characterization tests still pass.
- No test writes under `/opt/llm`.

## Out of Scope

- Fixing the prune mock shape (separate row, REQ-005).
- Command-level end-to-end tests (separate row, REQ-007).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add writer-level real-loader tests in `test_memory_store.py` (REQ-006) | Completed | 2026-10-20 | delete/pin/unpin real-archive tests already present (TestDeleteArchiveRealLoader); added prune writer test |
| 2 | Add or update tests per Validation plan | Completed | 2026-10-20 | Added `test_prune_emit_writes_real_event` to `TestDeleteArchiveRealLoader` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-20 | ruff clean; full suite 9594 passed, 20 skipped |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-20 | N/A (test-only change) |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/20261019-165345_memcfg001_memory-event-writers-read-a-missing-config-key.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-205032_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-225902
- **Related target files**: `tests/agent/memory/test_memory_store.py`
