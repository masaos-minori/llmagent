# Implementation: test_agent_session.py — diagnostic persistence isolation tests

Source plan: `plans/20260626-180402_plan.md` — Phase 3

---

## Goal

Add tests that verify `save_diagnostic()` writes to `session_diagnostics` and that `fetch_messages()` returns zero diagnostic rows, confirming the two tables are kept strictly separate.

---

## Scope

**In-Scope**
- `test_diagnostic_not_in_fetch_messages`: call `session.save_diagnostic()` → call `session.fetch_messages()` → assert empty
- `test_partial_completion_saved_to_diagnostics`: call `DiagnosticStore.save_partial_completion()` → `DiagnosticStore.fetch()` → assert row with `kind="partial_completion"`
- `test_session_restore_excludes_diagnostics`: save message + diagnostic → restore session → assert diagnostic not in restored history

**Out-of-Scope**
- Testing all DiagnosticStore event kinds
- Export command behavior

---

## Assumptions

1. Tests follow the same DB fixture pattern used in existing `test_agent_session.py` tests.
2. `AgentSession.save_diagnostic()` delegates to `DiagnosticStore.save()` with `kind="llm_transport_error"`.
3. `DiagnosticStore` can be instantiated independently in tests.

---

## Implementation

### Target file
`tests/test_agent_session.py`

### Procedure
Add three test functions after reading existing fixture setup pattern.

### Method

```python
def test_diagnostic_not_in_fetch_messages(tmp_path, monkeypatch):
    """save_diagnostic does not contaminate fetch_messages."""
    session = make_test_session(tmp_path, monkeypatch)  # existing fixture helper
    session.save_diagnostic("transport error: connection refused")
    messages = session.fetch_messages(session.session_id)
    assert messages == []


def test_partial_completion_saved_to_diagnostics(tmp_path, monkeypatch):
    """save_partial_completion writes kind=partial_completion to session_diagnostics."""
    from agent.diagnostic_store import DiagnosticStore
    session = make_test_session(tmp_path, monkeypatch)
    store = DiagnosticStore()
    store.save_partial_completion(session.session_id, turn=1, reason="stop", content_length=42)
    rows = store.fetch(session.session_id)
    assert len(rows) == 1
    assert rows[0]["kind"] == "partial_completion"
    import orjson
    payload = orjson.loads(rows[0]["content"])
    assert payload["turn"] == 1


def test_session_restore_excludes_diagnostics(tmp_path, monkeypatch):
    """Restoring a session does not include diagnostic rows."""
    session = make_test_session(tmp_path, monkeypatch)
    session.save("user", "hello")
    session.save("assistant", "hi")
    session.save_diagnostic("some error")
    ctx = make_test_ctx(session, tmp_path)
    from agent.services.session_restore import restore_session
    result = restore_session(ctx, session.session_id)
    assert result.n_messages == 2
    assert all(m["role"] != "diagnostic" for m in ctx.conv.history)
```

---

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check tests/test_agent_session.py` | 0 errors |
| Tests | `uv run pytest tests/test_agent_session.py -k "diagnostic" -v` | all pass |
| Full suite | `uv run pytest -v` | all pass |
