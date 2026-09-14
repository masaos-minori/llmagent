## Goal

Add unit tests for the new `/session rag-rebuild-vec` command in `tests/agent/commands/test_agent_cmd_session.py`, mirroring the existing `rag-rebuild-fts` test pair (`test_rag_rebuild_fts_calls_service_and_prints_success`, `test_rag_rebuild_fts_ignores_extra_args`). Per REQ-003.

## Scope

- Add exactly two test methods to the existing `TestCmdSessionRagRebuildFts` class
- Test the success path (service called, success message printed)
- Test that extra arguments are ignored (same as `rag-rebuild-fts`)
- Out-of-scope: integration test for orphan-removal verification (separate Plan)

## Assumptions

- The existing `TestCmdSessionRagRebuildFts` class (lines 776-805) provides the exact structural template to mirror
- `RagMaintenanceService` is patched via `patch("agent.commands.cmd_session.RagMaintenanceService")` — confirmed via existing test code
- The mock service object's `rebuild_vec()` method should return an `int` (row count) — confirmed via `rag_maintenance_service.py:66-78`

## Design decisions

1. Place new tests in the existing `TestCmdSessionRagRebuildFts` class — consistent with the existing pattern where `rag-rebuild-fts` tests live here
2. Name new tests following the same convention: `test_rag_rebuild_vec_*`
3. Include assertion on the row count in the success message (unlike `rag-rebuild-fts` which only checks for "rebuilt" substring)

## Alternatives considered

1. Creating a separate test class for `rag-rebuild-vec`: rejected — the existing pattern groups RAG rebuild commands together under one class
2. Using `caplog` instead of `capsys` for message verification: rejected — the existing tests use `capsys`; consistency within the class is preferred

## Implementation

### Target file

`tests/agent/commands/test_agent_cmd_session.py`

### Procedure

1. Read the existing `TestCmdSessionRagRebuildFts` class (lines 776-805) to confirm current content
2. Add `test_rag_rebuild_vec_calls_service_and_prints_success` after `test_rag_rebuild_fts_ignores_extra_args` (after line 805)
3. Add `test_rag_rebuild_vec_ignores_extra_args` after the above test
4. Verify both tests follow the same patching/assertion pattern as the existing tests

### Method

1. Read `test_agent_cmd_session.py` lines 776-805 to confirm the exact test structure
2. Insert new test methods after line 805 using the same indentation style
3. Each test follows the same pattern: create cmd, patch `RagMaintenanceService`, call `_cmd_session`, assert on mock calls and output

### Details

**Step 1 — Read existing test structure:**

Current `TestCmdSessionRagRebuildFts` class (lines 776-805):

```python
class TestCmdSessionRagRebuildFts:
    @pytest.mark.asyncio
    async def test_rag_rebuild_fts_calls_service_and_prints_success(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            MockSvc.return_value = mock_svc
            await cmd._cmd_session("rag-rebuild-fts")
            out = capsys.readouterr().out
            mock_svc.rebuild_fts.assert_called_once()
            assert "rebuilt" in out.lower()

    @pytest.mark.asyncio
    async def test_rag_rebuild_fts_ignores_extra_args(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            MockSvc.return_value = mock_svc
            await cmd._cmd_session("rag-rebuild-fts extra_arg")
            out = capsys.readouterr().out
            mock_svc.rebuild_fts.assert_called_once()
            assert "rebuilt" in out.lower()
```

**Step 2 — Add new tests after line 805:**

```python
    @pytest.mark.asyncio
    async def test_rag_rebuild_vec_calls_service_and_prints_success(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.rebuild_vec.return_value = 42
            MockSvc.return_value = mock_svc
            await cmd._cmd_session("rag-rebuild-vec")
            out = capsys.readouterr().out
            mock_svc.rebuild_vec.assert_called_once()
            assert "rebuilt" in out.lower()
            assert "42" in out

    @pytest.mark.asyncio
    async def test_rag_rebuild_vec_ignores_extra_args(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.rebuild_vec.return_value = 10
            MockSvc.return_value = mock_svc
            await cmd._cmd_session("rag-rebuild-vec extra_arg")
            out = capsys.readouterr().out
            mock_svc.rebuild_vec.assert_called_once()
            assert "rebuilt" in out.lower()
            assert "10" in out
```

Rationale: mirrors the existing test structure exactly, but adds assertions on the row count in the success message (since the new command includes it).

Reference files read (must NOT be modified):
- `scripts/agent/services/rag_maintenance_service.py:66-78` — confirms `rebuild_vec()` returns `int`
- `tests/agent/commands/test_agent_cmd_session.py:776-805` — confirms existing test pattern

## Compatibility considerations

- No public API changes; only adds new test methods
- Test isolation preserved: each test patches `RagMaintenanceService` independently
- Existing `rag-rebuild-fts` tests unaffected by the additions

## Security considerations

N/A — test-only change, no security-sensitive operations introduced.

## Rollback considerations

- Revert the two added test methods to restore original state
- No data loss risk — only test code changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/commands/test_agent_cmd_session.py | Unit — verify new tests pass | `uv run pytest tests/agent/commands/test_agent_cmd_session.py -k rag_rebuild_vec -q` | Both new tests pass |
| tests/agent/commands/test_agent_cmd_session.py | Regression — verify existing tests still pass | `uv run pytest tests/agent/commands/test_agent_cmd_session.py -k rag_rebuild_fts -q` | Existing tests unaffected |

## Completion criteria

- [ ] `test_rag_rebuild_vec_calls_service_and_prints_success` added and passes
- [ ] `test_rag_rebuild_vec_ignores_extra_args` added and passes
- [ ] Both tests follow the same structure as the existing `rag-rebuild-fts` test pair
- [ ] Both tests assert on the row count returned by `rebuild_vec()`
- [ ] Existing `rag-rebuild-fts` tests still pass without regression

## Out of scope

- Integration test for orphan-removal verification (separate Plan)
- Modifying the existing `rag-rebuild-fts` tests
- Adding fixtures or shared setup beyond what the existing tests use

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: existing tests cover regression |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | N/A: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docstring already describes delegation |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260914-105248_ragsvc03_orphaned-vector-periodic-cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-145915_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-161952
- **Related target files**: tests/agent/commands/test_agent_cmd_session.py
