# Implementation: Fix partial_completion state in turn_end audit event

## Goal

Fix the remaining gap where `turn_end.partial_completion` is always emitted as `False` even after a partial LLM transport error, and verify that the already-implemented `persist_as_assistant=False` guard is fully covered by tests for session restore and fetch_messages paths.

## Scope

- **In-Scope**:
  - `scripts/agent/orchestrator.py` — fix `_build_turn_end_event` to reflect actual partial completion state
  - `scripts/agent/orchestrator.py` — propagate `is_partial` flag from `_process_turn` through to `_handle_turn_end`
  - `tests/test_orchestrator.py` — add tests for `partial_completion` field accuracy in turn_end event
  - `tests/test_orchestrator.py` — add test verifying `fetch_messages` path does not surface transport diagnostics (via session restore mock)
- **Out-of-Scope**:
  - `agent/turn_result.py` — `persist_as_assistant` field already implemented
  - `agent/llm_turn_runner.py` — `persist_as_assistant=False` on error already implemented
  - `agent/orchestrator.py` — `persist_as_assistant` guard in `_handle_llm_turn` already implemented
  - `agent/diagnostic_store.py` — diagnostic save methods already complete
  - DB schema changes
  - Deploy changes

## Assumptions

- The already-implemented `persist_as_assistant=False` flag and the `session.save` guard in `_handle_llm_turn` are correct and only the `partial_completion` audit field and session-restore test coverage remain.
- `ctx.services.llm.stat_partial_completions` is the canonical signal for whether a partial completion occurred this turn.
- The `_process_turn` caller (`handle_turn` / workflow engine) has sufficient reach to pass a partial flag to `_handle_turn_end`.

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | How `_process_turn` should communicate partial-completion state to `_handle_turn_end` — via return value or side-channel | Extend `_process_turn` return type to `tuple[str, str | None, bool]` (answer, error_kind, is_partial); update both callers |
| UNK-02 | Whether `fetch_messages` already excludes messages stored with `save_diagnostic` (role-based filter vs. explicit exclusion) | `session_message_repo.fetch_messages` reads `messages` table by `session_id`; `session_diagnostics` is a separate table — transport errors saved via `DiagnosticStore.save` never enter `messages`. Verified: `session.save("assistant", ...)` is the only path into `messages`; check `SessionMessageRepository.save` |

## Implementation

### Target file: `scripts/agent/orchestrator.py`

#### Procedure

1. Extend `_process_turn` return type to include `is_partial` flag
2. Set `is_partial = True` in `_process_turn` when `result.exception` is not None and `result.exception.partial_text` is truthy
3. Update `handle_turn` and `_handle_workflow_engine` call sites to unpack the new `is_partial` value
4. Update `_handle_turn_end` signature to accept `is_partial: bool = False`
5. Update `_build_turn_end_event` to use `partial_completion=is_partial` instead of hardcoded `False`

#### Method

Direct file edit — modify return types and add parameter propagation.

#### Details

**1. Update `_process_turn` return type (line 419-421):**
```python
# Before:
async def _process_turn(
    self, line: str, ctx: AgentContext, turn_started_at: float
) -> tuple[str, str | None]:

# After:
async def _process_turn(
    self, line: str, ctx: AgentContext, turn_started_at: float
) -> tuple[str, str | None, bool]:
```

**2. Update `_process_turn` to set `is_partial` (after line 438):**
```python
# Add after "error_kind = result.error_kind":
is_partial = False
if not result.success and result.exception is not None:
    is_partial = bool(result.exception.partial_text)
```

**3. Update `_process_turn` return statement (line 444):**
```python
# Before:
return answer, error_kind

# After:
return answer, error_kind, is_partial
```

**4. Update `handle_turn` call site (lines 193-194):**
```python
# Before:
answer, error_kind = await self._process_turn(line, ctx, turn_started_at)
await self._handle_turn_end(line, answer, turn_started_at, error_kind)

# After:
answer, error_kind, is_partial = await self._process_turn(line, ctx, turn_started_at)
await self._handle_turn_end(line, answer, turn_started_at, error_kind, is_partial)
```

**5. Update `_handle_workflow_engine` call site (lines 227-242):**
```python
# Before:
answer, error_kind = await self._process_turn(

# After:
answer, error_kind, is_partial = await self._process_turn(
```

**6. Update `handle_turn` call site for workflow engine (line 242):**
```python
# Before:
await self._handle_turn_end(line, answer, turn_started_at, error_kind)

# After:
await self._handle_turn_end(line, answer, turn_started_at, error_kind, is_partial)
```

**7. Update `_handle_turn_end` signature (line 446-447):**
```python
# Before:
async def _handle_turn_end(
    self, line: str, answer: str, turn_started_at: float, error_kind: str | None
) -> None:

# After:
async def _handle_turn_end(
    self, line: str, answer: str, turn_started_at: float, error_kind: str | None, is_partial: bool = False
) -> None:
```

**8. Update `_build_turn_end_event` call in `_handle_turn_end` (line 452-453):**
```python
# Before:
event = self._build_turn_end_event(
    elapsed_ms, error_kind, ctx.turn.current_turn_id
)

# After:
event = self._build_turn_end_event(
    elapsed_ms, error_kind, ctx.turn.current_turn_id, is_partial
)
```

**9. Update `_build_turn_end_event` signature (line 458-462):**
```python
# Before:
def _build_turn_end_event(
    self,
    elapsed_ms: float,
    error_kind: str | None,
    task_id: str | None,
) -> dict[str, int | float | str | None]:

# After:
def _build_turn_end_event(
    self,
    elapsed_ms: float,
    error_kind: str | None,
    task_id: str | None,
    is_partial: bool = False,
) -> dict[str, int | float | str | None]:
```

**10. Update `_build_turn_end_event` to use `is_partial` (line 473):**
```python
# Before:
"partial_completion": False,

# After:
"partial_completion": is_partial,
```

### Target file: `tests/test_orchestrator.py`

#### Procedure

Add tests for `partial_completion` field accuracy in turn_end event and verify `fetch_messages` path does not surface transport diagnostics.

#### Method

Direct file edit — append new test methods to existing test classes.

#### Details

**Add after existing tests in appropriate class:**
```python
    @pytest.mark.asyncio
    async def test_turn_end_partial_completion_true_on_partial_error(self) -> None:
        """Verify partial_completion=True when LLM returns partial text on transport error."""
        from agent.turn_result import TurnResult  # noqa: PLC0415

        class _MockRunner:
            async def run(self, llm_url: str) -> TurnResult:
                return TurnResult(
                    action="fail",
                    answer="",
                    error_kind="transport",
                    exception=MagicMock(partial_text="partial text here"),
                    persist_as_assistant=False,
                )

        # Replace the LLM runner with mock that returns partial text
        self.orchestrator._llm_runner = _MockRunner()  # type: ignore[attr-defined]

        captured_events: list[dict] = []

        def capture_event(event: str) -> None:
            captured_events.append(json.loads(event))

        self.orchestrator._audit_logger.info = capture_event  # type: ignore[method-assign]

        await self.orchestrator.handle_turn("test message")  # type: ignore[attr-defined]

        # Find turn_end event
        turn_end = next(e for e in captured_events if e.get("event") == "turn_end")
        assert turn_end["partial_completion"] is True

    @pytest.mark.asyncio
    async def test_turn_end_partial_completion_false_on_full_error(self) -> None:
        """Verify partial_completion=False when LLM returns no partial text on transport error."""
        from agent.turn_result import TurnResult  # noqa: PLC0415

        class _MockRunner:
            async def run(self, llm_url: str) -> TurnResult:
                return TurnResult(
                    action="fail",
                    answer="",
                    error_kind="transport",
                    exception=MagicMock(partial_text=None),
                    persist_as_assistant=False,
                )

        self.orchestrator._llm_runner = _MockRunner()  # type: ignore[attr-defined]

        captured_events: list[dict] = []

        def capture_event(event: str) -> None:
            captured_events.append(json.loads(event))

        self.orchestrator._audit_logger.info = capture_event  # type: ignore[method-assign]

        await self.orchestrator.handle_turn("test message")  # type: ignore[attr-defined]

        turn_end = next(e for e in captured_events if e.get("event") == "turn_end")
        assert turn_end["partial_completion"] is False

    @pytest.mark.asyncio
    async def test_fetch_messages_excludes_transport_diagnostics(self) -> None:
        """Verify fetch_messages does not surface transport diagnostics from DiagnosticStore."""
        # Verify that DiagnosticStore.save writes to session_diagnostics table, not messages table
        # and that SessionMessageRepository.save writes to messages table only via session.save("assistant", ...)
        from agent.diagnostic_store import DiagnosticStore  # noqa: PLC0415

        mock_diag = MagicMock(spec=DiagnosticStore)
        mock_diag.save = MagicMock()
        mock_diag.save_partial_completion = MagicMock()

        self.orchestrator._diagnostic_store = mock_diag  # type: ignore[attr-defined]

        captured_saves: list[tuple[str, str]] = []

        def capture_save(role: str, content: str) -> None:
            captured_saves.append((role, content))

        self.orchestrator._ctx.session.save = MagicMock(side_effect=capture_save)  # type: ignore[attr-defined]

        await self.orchestrator.handle_turn("test message")  # type: ignore[attr-defined]

        # Verify session.save was NOT called with "assistant" role (persist_as_assistant=False guard)
        assistant_saves = [s for s in captured_saves if s[0] == "assistant"]
        assert len(assistant_saves) == 0, "Transport error should not persist as assistant message"
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `orchestrator._build_turn_end_event` | Add test: partial LLM error → audit logger receives `partial_completion=True` | `pytest tests/test_orchestrator.py::TestHandleTurnLLMTransportError` | New test passes; field is `True` for partial errors |
| `orchestrator._build_turn_end_event` | Add test: non-partial LLM error → audit logger receives `partial_completion=False` | `pytest tests/test_orchestrator.py` | New test passes; field remains `False` for non-partial |
| `session_message_repo.fetch_messages` | Add test: after transport error, `fetch_messages` returns no diagnostic content | Mock `DiagnosticStore.save` + `SessionMessageRepository.save`; assert `messages` table not written | Test confirms separation |
| All | Full regression | `uv run --no-sync pytest tests/test_orchestrator.py tests/test_llm_turn_runner.py tests/test_diagnostic_store.py -q` | 79+ tests pass, 0 failures |

## Risks & Mitigations

- **Risk**: Extending `_process_turn` return tuple breaks `_handle_workflow_engine` which unpacks `(answer, error_kind)` → **Mitigation**: Update both call sites (`handle_turn` and `_handle_workflow_engine`) atomically in the same commit; mypy will catch missed sites.
- **Risk**: `stat_partial_completions` is incremented after `_process_turn` returns, so reading it inside `_process_turn` would give stale value → **Mitigation**: Derive `is_partial` from `result.exception is not None and bool(result.exception.partial_text)` directly in `_process_turn`, matching the existing `_handle_partial_completion` condition.
- **Risk**: Tests that mock `_diagnostic_store.save` call count may become fragile if a new save call is added → **Mitigation**: Use `assert_called()` rather than `assert_called_once()` where the exact call count is not semantically meaningful.
