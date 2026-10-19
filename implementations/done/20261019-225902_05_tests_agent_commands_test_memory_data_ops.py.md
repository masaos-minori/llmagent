## Goal

Correct the wrongly-shaped mock in `TestEmitPruneEvent` and add real-loader assertions for the prune path (REQ-005), so the prune emit path is exercised against the real flat config instead of the incorrect nested `{"memory": {"memory_jsonl_dir": ...}}` shape that masked the defect.

## Scope

- Modify only `tests/agent/commands/test_memory_data_ops.py`.
- Two changes: (1) fix the existing `test_appends_delete_event_from_config_dir` mock to the flat shape; (2) add a real-loader test asserting the prune event lands under the isolated temporary root.

## Assumptions

- `conftest.py` sets `LLMAGENT_CONFIG_DIR` to a temp copy of `config/` where `memory_jsonl_dir` is rewritten from `/opt/llm/memory` to `{root}/memory` via `_WRITABLE_STATE_RE`, so the real `ConfigLoader().load("agent.toml")` resolves the flat key to a temp path (UNK-02 resolved — no extra fixture needed).
- The autouse `/opt/llm` guard fails any test that opens a production path; the rewritten temp path keeps the real-loader test inside the isolation root.

## Design decisions

- **Fix the mock to the flat shape.** The existing test mocks `ConfigLoader.load()`; change the returned dict from `{"memory": {"memory_jsonl_dir": "/tmp/mem"}}` to the flat `{"memory_jsonl_dir": "/tmp/mem"}` so the assertion `Path("/tmp/mem") / "memories.jsonl"` still holds and the mock now matches the real shape.
- **Add a true real-loader test** that does NOT patch `ConfigLoader` or `JsonlMemoryStore`, calls `_emit_prune_event("id-xyz")`, and asserts the emitted `delete` event line exists in `{root}/memory/memories.jsonl`. This is the regression guard from AC-3: it fails if the nested shape is reintroduced.

## Alternatives considered

- **Keep mocking but only fix the key** — weaker; a real-loader test catches the regression directly rather than trusting another mock. Prefer the real-loader test as the primary guard.

## Implementation

### Target file
`tests/agent/commands/test_memory_data_ops.py`

### Procedure
1. Open `tests/agent/commands/test_memory_data_ops.py`. Locate `TestEmitPruneEvent.test_appends_delete_event_from_config_dir` (lines 402-420).
2. In the mock block, change line 416-418:
   - From:
     ```python
     cl.return_value.load.return_value = {
         "memory": {"memory_jsonl_dir": "/tmp/mem"}
     }
     ```
   - To:
     ```python
     cl.return_value.load.return_value = {
         "memory_jsonl_dir": "/tmp/mem"
     }
     ```
   The rest of the test (assertions on lines 420-421) is unchanged and still passes.
3. Add a new test method to `TestEmitPruneEvent`, e.g. `test_real_loader_writes_prune_event_under_temp_root`:
   - Do NOT patch `ConfigLoader` or `JsonlMemoryStore`.
   - Call `_emit_prune_event("id-xyz")`.
   - Resolve the archive path from the isolated root: read `LLMAGENT_CONFIG_DIR` from `os.environ`, apply the same `memory_jsonl_dir` value the isolated `agent.toml` carries (or read that key back from the copied toml), and assert the file `<memory_dir>/memories.jsonl` exists and contains a line recording the `delete` event for `id-xyz`.
   - Keep the assertion tied to the temp root path, never `/opt/llm`.

### Method
Shape correction on the existing mock plus an additive real-loader test; no existing test is removed.

### Details
- For the real-loader test, obtain the archive dir the same way the resolver does: `from shared.config_loader import ConfigLoader; cfg = ConfigLoader().load("agent.toml"); memory_dir = cfg["memory_jsonl_dir"]`. Because `conftest` rewrote the key to `{root}/memory`, `memory_dir` is the temp path. Then read `memory_dir/memories.jsonl` and assert the prune event line is present.
- Import `os`/`pathlib` as needed (check existing imports at the top of the file).
- Do not modify other test classes in this file beyond what the shape fix requires.

## Compatibility considerations
Test-only change. The shape fix must not break other assertions in the file — run the whole file after editing (Plan Risks).

## Security considerations
N/A: test-only; the real-loader test asserts writes stay under the isolated temp root.

## Rollback considerations
Revert the two edits to this test file.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `TestEmitPruneEvent` (fixed mock) | Unit: mock uses flat shape | `uv run pytest tests/agent/commands/test_memory_data_ops.py::TestEmitPruneEvent` | passes |
| Real-loader prune test | Real config loader; assert event under temp root | `uv run pytest tests/agent/commands/test_memory_data_ops.py` | passes; no `/opt/llm` write |

## Completion criteria

- `test_appends_delete_event_from_config_dir` mocks the flat real shape `{"memory_jsonl_dir": ...}`.
- A real-loader test asserts the prune `delete` event lands under the isolated temporary root and fails if the nested shape returns.
- The whole file passes.

## Out of Scope

- Writer-level delete/pin/unpin tests (separate row, REQ-006).
- Command-level end-to-end tests (separate row, REQ-007).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix `TestEmitPruneEvent` mock shape + real-loader prune test (REQ-005) | Completed | 2026-10-20 | Restored class with corrected flat mock + real-loader guard |
| 2 | Add or update tests per Validation plan | Completed | 2026-10-20 | Flat-shape mock restored; `test_real_loader_writes_prune_event_under_temp_root` added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-20 | ruff clean; full suite 9593 passed, 20 skipped |
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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261019-165345_memcfg001_memory-event-writers-read-a-missing-config-key.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-205032_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-225902
- **Related target files**: `tests/agent/commands/test_memory_data_ops.py`
