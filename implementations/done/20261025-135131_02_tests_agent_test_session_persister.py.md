# Implementation Procedure — tests/agent/test_session_persister.py

## Goal

Add a semantic round-trip test proving the orjson-written `session_summary` content
parses back to the same dict the persister built (REQ-004, AC-002), with no other
assertion changes.

## Scope

- Modify only `tests/agent/test_session_persister.py`: append one test method.
- No production file is modified by this procedure (swap:
  `implementations/20261025-135131_01_scripts_agent_session_persister.py.md`).

## Assumptions

- The `db` fixture (line 63, `_MemDb` behind `agent.diagnostic_store.SQLiteHelper`) and
  the `_ctx(session_id)` builder (line 79) are reusable as-is — verified 2026-10-25.
- `test_session_persister.py` contains zero stdlib-`json` references (grep verified),
  so REQ-005 adjustments are expected to be unnecessary.
- The summary dict shape is defined by the persister's own `summary = {...}` build
  (before `session_persister.py:161`); the test asserts against that same key/value
  source rather than hard-coding bytes (semantic contract).

## Design decisions

- Round-trip via the existing in-memory `_MemDb`: read `content` back with a direct
  `db.conn.execute`, parse with `orjson.loads`, compare to the summary the persister
  derived from `_ctx` stats — pins semantics, not serialization bytes (plan Assumption
  3).
- New test appended to the existing gate-class grouping (a small
  `TestPersistSessionDiagnosticsRoundTrip (new)` class) rather than modifying existing
  tests — existing assertions stay byte-identical (target-table contract).

## Alternatives considered

- Byte-for-byte golden content assertion: rejected — the plan's contract is semantic
  compatibility; byte pins would contradict Assumption 3.
- Parsing back through `DiagnosticStore.load`: acceptable alternative if the store's
  read API is simpler at implementation time; the equality assertion is identical
  either way.

## Implementation
### Target file
`tests/agent/test_session_persister.py`

### Procedure

Append after `TestPersistSessionDiagnosticsGate`:

```python
class TestPersistSessionDiagnosticsRoundTrip:                     # (new)
    @pytest.mark.asyncio
    async def test_summary_content_round_trips_to_same_dict(self, db) -> None:  # (new)
        ctx = _ctx(1)
        persister = SessionPersister(ctx, DiagnosticStore(), MagicMock())

        await persister.persist_session_diagnostics()

        (content,) = db.conn.execute(
            "SELECT content FROM session_diagnostics WHERE kind = 'session_summary'"
        ).fetchone()
        parsed = orjson.loads(content)
        assert parsed["turns"] == ctx.stats.stat_turns
        assert parsed["tool_calls"] == ctx.stats.stat_tool_calls
        assert parsed["session_id"] == 1
        assert isinstance(content, str)
```

(`turns`/`tool_calls`/`session_id` key names: confirm against the persister's actual
`summary` dict keys before writing; adjust the three asserts to the real key set.)

### Method
New symbols `(new)`: `TestPersistSessionDiagnosticsRoundTrip (new)` and its one test
method `(new)`. Add `import orjson` to the module's import block (third-party block,
respecting ruff isort ordering).

### Details
- `isinstance(content, str)` also pins the `.decode()` half of REQ-003 (the DB column
  received a str, not bytes).
- All existing tests, fixtures, and `_MemDb` stay untouched.

## Compatibility considerations

- With procedure 01 not yet landed the test still passes (stdlib json.dumps output is
  also valid JSON) — the test locks semantics across the swap, not the swap itself; the
  real REQ-001 gate is AC-001's grep check in procedure 01.
- Reader-set characterization (unmodified): `test_session_restore.py`,
  `test_agent_session.py`, `test_regression_diagnostic_persist.py`,
  `test_diagnostic_store.py` (AC-003).

## Security considerations

N/A: in-memory DB test only.

## Rollback considerations

Delete the appended class; the file is otherwise untouched.

## Validation plan

- Targeted: `uv run pytest tests/agent/test_session_persister.py
  tests/agent/test_diagnostic_store.py tests/agent/test_regression_diagnostic_persist.py -x -q`.
- Reader set: `uv run pytest tests/agent/test_session_restore.py
  tests/agent/test_agent_session.py -x -q`.
- Full: `uv run pytest tests/ -q` (10091 collected at HEAD ad39f04f0) +
  `rules/toolchain.md`; ruff clean on this test file.

## Completion criteria

- AC-002: round-trip test green (`orjson.loads(content)` equals the expected summary
  values) with procedure 01 applied.
- AC-003: reader set green unmodified.

## Out of Scope

- The production swap (procedure 01).
- Byte-exact content assertions (rejected).
- Repo-wide orjson enforcement gate (issue out-of-scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the round-trip test + `import orjson` (confirm summary key names first) | Completed | 2026-10-25 | 2026-10-25 | Deviation: two test methods (adds nested latency-summary float round-trip) — within goal scope; real summary key set (20 keys) pinned |
| 2 | Run targeted + reader-set validation | Completed | 2026-10-25 | 2026-10-25 | targeted + reader set 118 passed; ruff clean; guard-behavior claim (lines 85-87) empirically confirmed: tests also pass with stdlib json restored |

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
- **Requirement ID**: REQ-004, REQ-005
- **Source issue**: `issues/done/20261025-115739_sess004_orjson-session-persister.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123758_sess004_orjson-session-persister.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-135131
- **Related target files**: tests/agent/test_session_persister.py
