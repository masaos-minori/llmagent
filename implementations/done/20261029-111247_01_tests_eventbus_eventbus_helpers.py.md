# Implementation Procedure: tests/eventbus/eventbus_helpers.py

<!-- Generated from plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md row: tests/eventbus/eventbus_helpers.py -->
<!-- Preserve this header comment; it links the procedure back to the Plan target file table row. -->

## Goal

Provide the two-lifecycle lifespan fixture `eventbus_two_lifecycle_clients` (new) and its
shared config builder `eventbus_test_config` (new) in `tests/eventbus/eventbus_helpers.py`,
while `make_eventbus_client()` keeps its current signature, default header, token config, and
return contract (`REQ-001`, `REQ-003`; AC-2).

## Scope

`tests/eventbus/eventbus_helpers.py` only: two new functions (`eventbus_test_config` (new),
`eventbus_two_lifecycle_clients` (new)) and a delegation edit inside `make_eventbus_client`.
No changes to `eventbus_test_tokens`, `eventbus_auth_headers`, `principal_map`, or any
caller. No production code.

## Assumptions

- Source claims re-verified this cycle: `eventbus_test_tokens` (`:69`),
  `eventbus_auth_headers` (`:88`), `make_eventbus_client` (`:101-161`: `EventBusConfig`
  built inline at `:118-125`, optional `sse_idle_timeout` assignment `:126-129`,
  monkeypatches `load_config`/`_ENVELOPE_SCHEMA_PATH`/`get_schema_path` at `:130-135`,
  `_init_state` pre-build `:137-143`, unentered `TestClient` `:145`, `_cleanup` attachment
  `:150-160`), `_init_state` (`:164-176`), `_do_cleanup` (`:179-191`), `principal_map`
  (`:194-203`); the builder named _init_eventbus_state from the original plan text does
  not exist in the file (see the Plan's 2026-10-29 correction note).
- Overlap (Plan row 01 Overlap column): `implementations/20261029-101908_02_tests_eventbus_eventbus_helpers.py.md`
  (eventbus003) deletes the `_init_state` call block, `_cleanup` block, `_init_state`,
  `_do_cleanup`, and `import asyncio` from this file. Judgment: compatible and
  complementary — that procedure removes the hand-built state; this procedure adds the
  config builder and the two-lifecycle fixture. Locate code by content, not line number;
  sequencing per the Plan: `101908_02` lands first, then this row.
  `implementations/20261029-102038_18_tests_eventbus_eventbus_helpers.py.md` is
  comment/docstring-only cleanup; compatible.
- "Private config builder" in the Plan means test-local (test directory), not a leading
  underscore: the restart test file imports the fixture and builder across modules,
  matching the existing public test-helper naming (`eventbus_test_tokens`).
- Plan Design correction 2026-10-29: the fixture yields `(open_client, snapshots)`, not two
  concurrently entered clients, because `eb_app.app` is a module-level singleton and each
  `lifespan()` replaces `app.state` wholesale (`scripts/eventbus/app.py:70-137`); sequential
  factory entry preserves the two-independent-lifecycles intent (AC-1, AC-2).

## Design decisions

- Extract, do not duplicate: the `EventBusConfig(...)` construction inside
  `make_eventbus_client` (`:118-129`) moves verbatim into
  `eventbus_test_config(tmp_path, *, max_retry=3, sse_idle_timeout=None, token="test-token")`;
  `make_eventbus_client` calls it, so config values stay single-source (`REQ-003`, AC-1).
- The fixture takes pytest's `tmp_path` and `monkeypatch`, applies the same three
  monkeypatches as `make_eventbus_client` (`:130-135`), and yields a `contextmanager`
  factory; it never calls `_init_state` or `_do_cleanup` — all state comes from the
  production lifespan on `TestClient` entry/exit (REQ-001).
- `snapshots` records the fresh `app.state.db` handle and broker identity at each entry;
  tests assert identity differences and `db._shutting_down` on the retained handle after
  exit (`scripts/eventbus/db_conn.py:15`) — the leak-probe helper role of the Plan row 01
  (REQ-003, AC-2).

## Alternatives considered

- Placing the fixture in `conftest.py`: rejected by the Plan's frozen Assumptions (fixture
  location decision).
- Yielding two simultaneously entered `TestClient`s: rejected; impossible for a module-level
  singleton app (Plan correction note).

## Implementation

### Target file

`tests/eventbus/eventbus_helpers.py`

### Procedure

1. Open `tests/eventbus/eventbus_helpers.py` and locate the `EventBusConfig(` construction
   inside `make_eventbus_client` (`:118-129`).
2. Add `eventbus_test_config(tmp_path: Path, *, max_retry: int = 3, sse_idle_timeout: float | None = None, token: str = "test-token") -> EventBusConfig`
   (new) above `make_eventbus_client`, moving the `EventBusConfig(...)` call and the
   `sse_idle_timeout` assignment block into it verbatim (same field values,
   `**eventbus_test_tokens(token)`).
3. Replace the moved block in `make_eventbus_client` with
   `cfg = eventbus_test_config(tmp_path, max_retry=max_retry, sse_idle_timeout=sse_idle_timeout, token="test-token")`;
   signature, header default, client construction, and return value stay unchanged.
4. Add fixture `eventbus_two_lifecycle_clients(tmp_path, monkeypatch)` (new) per Method code
   below, after `make_eventbus_client`. It must not reference `_init_state` or `_do_cleanup`
   (`REQ-001`, `REQ-003`).
5. Run `rg -n "EventBusConfig\(" tests/eventbus/eventbus_helpers.py` (exactly one
   construction site) and `rg -n "_init_state|_do_cleanup" tests/eventbus/eventbus_helpers.py`
   (no occurrence inside `eventbus_two_lifecycle_clients` (new)).

### Method

Fixture shape:

```python
def eventbus_two_lifecycle_clients(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Any:
    """Yield (open_client, snapshots).

    open_client() enters TestClient(eb_app.app) so the production lifespan builds and
    tears down app.state; each entry appends (app.state.db, app.state.broker) to
    snapshots. Callers open two sequential lifecycles on the same tmp_path database.
    """
    from contextlib import contextmanager

    from eventbus import app as eb_app

    cfg = eventbus_test_config(tmp_path)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    snapshots: list[tuple[Any, Any]] = []

    @contextmanager
    def open_client() -> Any:
        with TestClient(eb_app.app) as client:
            client.headers["Authorization"] = eventbus_auth_headers("publisher")[
                "Authorization"
            ]
            snapshots.append((eb_app.app.state.db, eb_app.app.state.broker))
            yield client

    yield open_client, snapshots
```

### Details

- These are new symbols (no existing symbols with these names); the stale detector treats
  them via the `(new)` template markers.

## Compatibility considerations

- `make_eventbus_client` callers (9 files, 16 references) must compile and pass unchanged;
  only its internal config building changes.
- The fixture is consumed via explicit import in `test_eventbus_restart_resume.py`
  (procedure `20261029-111247_02`); pytest resolves imported generator fixtures.

## Security considerations

- None specific; token config values are unchanged (`eventbus_test_tokens`).

## Rollback considerations

- Revert this file to restore the inline config build; no production or data impact.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_publish.py tests/eventbus/test_eventbus_auth.py -q`
  (caller gate; baseline `tests/eventbus`: 411 passed, 1 skipped).
- Fixture behavior is gated by the probe test in procedure `20261029-111247_02`.
- `uv run ruff check tests/eventbus/eventbus_helpers.py`; `uv run mypy tests/eventbus`
  stays at zero errors.

## Completion criteria

- Exactly one `EventBusConfig(` construction site remains in the file.
- All `make_eventbus_client` callers pass unchanged; the new fixture exists without
  `_init_state`/`_do_cleanup` references.

## Out of Scope

- Scenario and probe tests (procedure `20261029-111247_02`).
- Removal of `_init_state`/`_do_cleanup` (procedure `20261029-101908_02`).
- Comment/docstring identifier cleanup (procedure `20261029-102038_18`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | Added eventbus_test_config + eventbus_two_lifecycle_clients |
| 2 | Add or update tests per Validation plan | Done | — | — | Caller gate passes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | ruff clean, tests green |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20261028-122337_ebresumetest004_subscribe-restart-integration-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-111247
- **Related target files**: tests/eventbus/test_eventbus_restart_resume.py, tests/eventbus/test_eventbus_replay_subscribe.py
