# Implementation: test_agent_error_cases.py

## Goal

Add unit tests for all failure scenarios listed in the plan's Step 7, verifying that errors propagate correctly after the fail-fast refactoring.

## Scope

- Target: new file `tests/test_agent_error_cases.py`
- Test scenarios:
  1. Config load error (file missing, type wrong, cross-field invalid)
  2. SQLite failure in `NoteRepository`, `DocumentRepository`, `SessionMessageRepository`
  3. SQLite failure in `AgentSession.start()`, `list_sessions()`, `delete_session()`
  4. HTTP subprocess start failure (`HttpStartupError`)
  5. stdio transport restart failure
  6. Health-check timeout in `http_lifecycle.py`
  7. History compression failure (`_call_compress_llm` raises)
  8. Turn runner failure (exception propagates from `orchestrator.handle_turn`)

## Assumptions

1. `uv run pytest` is the test runner.
2. `unittest.mock.patch` and `pytest.raises` are used; no new test frameworks.
3. SQLite failures are simulated by `sqlite3.OperationalError`.
4. HTTP failures are simulated by `httpx.RequestError`.
5. After fail-fast changes, each test verifies that the exception is raised (not swallowed).

## Implementation

### Target file

`tests/test_agent_error_cases.py`

### Procedure

1. Config load error tests:
   - Patch `ConfigLoader.load_all` to raise `OSError`; assert `ConfigLoadError` is raised from `load_config()`.
   - Patch `ConfigLoader.load_all` to return config with invalid field type; assert `ConfigLoadError` or `ValueError` from `build_agent_config()`.

2. SQLite failure — NoteRepository:
   - Patch `SQLiteHelper.open` context manager to raise `sqlite3.OperationalError` inside `add_note()`.
   - Assert `sqlite3.OperationalError` propagates (not `None`).
   - Same for `list_notes()`, `delete_note()`, `get_all_note_contents()`.

3. SQLite failure — DocumentRepository:
   - Same pattern for `list_documents()` and `delete_document()`.

4. SQLite failure — SessionMessageRepository:
   - Patch `SQLiteHelper.open` to raise in `save()`, `save_many()`, `fetch_messages()`.
   - Assert `sqlite3.OperationalError` propagates.

5. SQLite failure — AgentSession:
   - Patch to raise in `start()`, `list_sessions()`, `delete_session()`.
   - Assert `sqlite3.OperationalError` propagates.

6. HTTP subprocess start failure:
   - Mock `subprocess.Popen` to exit immediately (poll returns non-None).
   - Assert `HttpStartupError` is raised from `HttpServerLifecycleManager.start()`.

7. stdio transport restart failure:
   - Mock `StdioTransport.start` to raise `OSError`.
   - Assert `OSError` propagates from `StdioServerLifecycleManager._start()`.

8. History compression failure:
   - Mock `httpx.AsyncClient.post` to raise `httpx.RequestError`.
   - Assert exception propagates from `HistoryManager._call_compress_llm()`.

9. Turn runner failure:
   - Mock `LLMTurnRunner.run` to raise `RuntimeError("unexpected")`.
   - Assert it propagates from `Orchestrator.handle_turn()`.

### Method

`pytest` fixtures with `unittest.mock.patch` and `pytest.raises`. Each test is self-contained.

### Details

```python
import sqlite3
import pytest
import httpx
from unittest.mock import patch, MagicMock

from agent.note_repo import NoteRepository
from agent.config import load_config, ConfigLoadError


def test_note_repo_add_note_sqlite_error() -> None:
    repo = NoteRepository()
    with patch("agent.note_repo.SQLiteHelper") as mock_helper:
        mock_helper.return_value.open.return_value.__enter__.side_effect = sqlite3.OperationalError("disk full")
        with pytest.raises(sqlite3.OperationalError):
            repo.add_note("test note")


def test_load_config_oserror() -> None:
    with patch("agent.config.ConfigLoader") as mock_loader:
        mock_loader.return_value.load_all.side_effect = OSError("file not found")
        with pytest.raises(ConfigLoadError):
            load_config()
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Tests | `uv run pytest tests/test_agent_error_cases.py -v` | all pass |
| Coverage | `uv run coverage run -m pytest tests/test_agent_error_cases.py` then `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% on changed lines |
