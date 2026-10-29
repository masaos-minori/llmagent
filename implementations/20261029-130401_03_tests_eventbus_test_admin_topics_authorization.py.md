# Implementation Procedure: tests/eventbus/test_admin_topics_authorization.py

<!-- Generated from plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md row: tests/eventbus/test_admin_topics_authorization.py -->
<!-- Preserve this header comment; it links the procedure back to the Plan target file table row. -->

## Goal

Rewrite the hand-built `admin_client` fixture so the client runs through the production lifespan
instead of a hand-assigned `app.state` and an attached `_cleanup`, following the pattern
eventbus003 establishes in `test_eventbus_health.py` (`REQ-003`; AC-3).

## Scope

`tests/eventbus/test_admin_topics_authorization.py` only: the fixture region (:17-118) is rebuilt
around `with TestClient(eb_app.app) as c:` and the three hand-built helpers
(`_make_admin_test_client` :17-73, `_init_state` :76-96, `_do_cleanup` :99-111) are deleted. No
test body, assertion, token value, or config value changes; no other file.

## Assumptions

- Source claims re-verified this cycle (2026-10-29, HEAD `a00f4517c`): the fixture helper builds
  config with distinct `admin_token="admin-tok"` / `consumer_token="consumer-tok"` and an
  unused `auth_token` (:28-46), patches `load_config`, `_ENVELOPE_SCHEMA_PATH`, and
  `get_schema_path` (:47-52), hand-runs `_init_state` on a private loop (:54-59), returns an
  un-entered `TestClient` with an attached `_cleanup` (:61-73); `admin_client` (:114-118) yields
  it and calls `client._cleanup()`.
- `scripts/eventbus/app.py::lifespan` (:70-92) already performs every step `_init_state` performs
  and more: `open_db`, `_populate_token_maps` (:76), envelope schema load, `storage_dir` mkdir
  (:78), `EventBroker`, `dlq_task` creation (:80), and full teardown via `_shutdown_lifespan`
  (:92, :95-135) which closes broker and db (verified 2026-10-29). Therefore deleting the
  hand-built setup and teardown is behavior-equivalent for every test in the file.
- Predecessors land first: `implementations/20261029-101908_01_tests_eventbus_test_eventbus_health.py.md`
  (the exact lifespan-fixture pattern this procedure copies) and
  `implementations/20261029-101908_02_tests_eventbus_eventbus_helpers.py.md` (helpers keep their
  final shape; this file does not call `make_eventbus_client` -- the distinct-token requirement
  in its own docstring stays). eventbus001/002 are already implemented on `master` (the principal
  map publish order and gauge work), so the lifespan behavior above is the current tree.
- The autouse `conftest.py` resets of the shutdown flag and the principal map stay untouched and
  remain compatible (eventbus003 Compatibility note).
- Other pending procedures touch disjoint regions of this file and need no ordering against this
  one: `implementations/20261029-115727_07_tests_eventbus_test_admin_topics_authorization.py.md`
  (ebaudit005 -- audit-test body assertions only),
  `implementations/20261029-101422_03_tests_eventbus_test_admin_topics_authorization.py.md`
  (appends a test class), and
  `implementations/20261029-102038_12_tests_eventbus_test_admin_topics_authorization.py.md`
  (comment-identifier cleanup only). None edits the fixture region or the imports.
- Line numbers shift once predecessors land; anchor on the function names and the
  `client._cleanup = _cleanup` literal.

## Design decisions

- Fold the config construction and the three `monkeypatch.setattr` calls directly into the
  `admin_client` fixture and delete `_make_admin_test_client`: the helper exists only to serve
  this one fixture, and the health pattern (`101908_01`) puts config+patches inline in the
  fixture (single-user indirection removed).
- Keep all config values and the distinct-token docstring verbatim (the docstring at :20-24
  explains why `make_eventbus_client` cannot be reused; it moves onto the fixture).
- `dlq_task` teardown is not reproduced: the real lifespan creates the task and
  `_shutdown_lifespan` cancels and awaits it -- strictly more complete than the hand-written
  `_do_cleanup` (whose `dlq_task = None` workaround comment at :83-87 disappears with it).

## Alternatives considered

- Reuse `make_eventbus_client` with post-eventbus003 form: rejected in the Plan -- that helper
  builds a shared all-roles `auth_token`, and these tests need a genuinely non-admin caller
  (distinct admin/consumer tokens), which is exactly the helper's docstring constraint.
- Keep `_make_admin_test_client` returning a context-managed client: rejected; a factory returning
  an already-entered `TestClient` inverts fixture ownership of the context and invites the same
  leak the Plan removes.

## Implementation
### Target file

`tests/eventbus/test_admin_topics_authorization.py`

### Procedure

1. Replace the fixture region: delete `_make_admin_test_client` (:17-73), `_init_state` (:76-96),
   `_do_cleanup` (:99-111), and the old `admin_client` body (:114-118).
2. Write a single fixture in their place:

   ```python
   @pytest.fixture()
   def admin_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
       """Build an Event Bus TestClient through the production lifespan with distinct
       admin_token/consumer_token (unlike `eventbus_helpers.make_eventbus_client`'s
       shared, all-roles `auth_token`), so ADMIN-gating can be tested against a
       genuinely non-admin caller.
       """
       from eventbus import app as eb_app
       from eventbus.config import EventBusConfig

       cfg = EventBusConfig(... exact current values from :28-46 ...)
       monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
       schema_path = (
           Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
       )
       monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
       monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

       with TestClient(eb_app.app) as c:
           yield c
   ```

3. Delete `import asyncio` (:7) -- nothing else in the file uses it (verified 2026-10-29: the
   only other `asyncio` uses were inside the deleted helpers). Keep `Path`, `Any`, `pytest`,
   `TestClient`, and `principal_map` imports (still used by the fixture and test bodies).
4. Do not touch any test class or test body.

### Method

Direct edit: one contiguous region replacement (:17-118 collapsed to the single fixture), then the
one import deletion.

### Details

- `TestPublishOrder.test_failed_principal_build_keeps_previous_generation` builds a second
  `TestClient(admin_client.app, raise_server_exceptions=False)` without entering it (:280); it
  keeps working because `admin_client`'s lifespan has already populated `app.state` for the shared
  `eb_app.app` -- same as today, where state was hand-built. No change to that test.
- `_boom(cfg: Any)` and the `-> Any` fixture return keep the `Any` import alive (ruff check
  confirms no unused import after the edit).
- After the edit, `rg "_init_state|_do_cleanup|_cleanup" tests/eventbus/test_admin_topics_authorization.py`
  must return nothing.

## Compatibility considerations

Test-visible behavior is unchanged: the lifespan produces the same `app.state` fields
(config/db/token maps/envelope schema/storage dir/broker) the tests assert against, plus the real
`dlq_task`. Two sequential lifecycles in one process are supported by `clear_shutdown_flag()` at
lifespan startup (app.py:72) and the conftest resets. The only removed capability is the private
loop plumbing, which existed solely to serve the hand-built state.

## Security considerations

N/A: fixture-local fixture tokens only (`admin-tok`, `consumer-tok`, unused superuser token), no
real credentials.

## Rollback considerations

Reverting the commit restores the three helpers and the attached-`_cleanup` fixture; no other
file references any of the deleted functions (they are module-private; grep 2026-10-29 confirms no
importers).

## Validation plan

1. `uv run pytest tests/eventbus/test_admin_topics_authorization.py -v` (same pass count).
2. Run the same file a second time in the same session (issue Testing Expectations: no state leak)
   -- `uv run pytest tests/eventbus/test_admin_topics_authorization.py tests/eventbus/test_admin_topics_authorization.py`
   is invalid collection; instead run the file twice in one pytest invocation via
   `uv run pytest tests/eventbus/test_admin_topics_authorization.py` twice within the same process
   is not possible, so use the eventbus003 pattern: `uv run pytest tests/eventbus/test_admin_topics_authorization.py && uv run pytest tests/eventbus/test_admin_topics_authorization.py`
   plus the two-sequential-lifecycles coverage in `101908_03`'s shutdown test.
3. `uv run pytest tests/eventbus` (package gate; confirms no cross-file state leak).
4. `uv run ruff check tests/eventbus/test_admin_topics_authorization.py`; `uv run ruff format
   --check`; `uv run mypy --no-namespace-packages tests/eventbus/test_admin_topics_authorization.py`.

## Completion criteria

- The file contains no `_init_state`, `_do_cleanup`, `_make_admin_test_client`, `client._cleanup`,
  or `app.state.` assignment; the fixture is `with TestClient(eb_app.app) as c: yield c`.
- All tests pass with unchanged assertions, run twice (fresh process each run) plus the package
  suite green.
- ruff, format check, and mypy are clean on the file (no unused imports).

## Out of Scope

- `test_eventbus_auth.py` class-level fixtures and other hand-built fixtures (Plan UNK-01 /
  eventbus003 UNK-02 follow-up).
- The `UNK-02`/`REQ-003`/`REQ-004` comment labels in this file (eventbus004 procedure
  `102038_12`).
- `eventbus_helpers.py` itself (eventbus003 procedure `101908_02`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the fixture region with the lifespan fixture and delete the three helpers and the unused import (Implementation > Procedure/Method/Details) | Pending | — | — | After `101908_01`/`02` land |
| 2 | Run the file twice and the package suite (Validation plan 1-3) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Tests-only row |

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
- **Requirement ID**: `REQ-003`, `REQ-004`
- **Source issue**: `issues/done/20261028-122523_ebtestdrift007_test-lifecycle-terminology.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-130401
- **Related target files**: tests/eventbus/test_admin_topics_authorization.py
