# test_eventbus_auth.py has 14 failing tests after Principal refactor

## Priority
High

## Summary
14 tests in `tests/eventbus/test_eventbus_auth.py` fail. Root-cause
investigation traced (at least) two distinct, confirmed bugs: (1) a local
test-app route wrapper calls `eb_app.publish_route` with a `_principal`
keyword argument that `publish()` does not accept, and (2) a shared test-app
init helper opens the SQLite DB before creating its parent directory, which
only surfaces when a test passes a literal, not-yet-created `Path` instead of
pytest's `tmp_path` fixture. Fix both, then re-triage the remaining failures
in this file against these two causes.

## Background
This file exercises authorization (`require_role`, `require_consumer_identity`)
across every EventBus route. The eventbus module went through a refactor
(commit `c85362a36`, "replace split token maps with Principal dataclass")
that changed route handlers to receive a `_principal: Principal` parameter
from FastAPI's `Depends(...)`. `tests/eventbus/test_eventbus_auth.py`'s local
`_make_test_app()` helper builds its own thin FastAPI route wrappers that
forward to the real `eventbus/*_route.py` functions, passing `_principal=...`
to each — but `scripts/eventbus/publish_route.py::publish()` was not updated
to accept a `_principal` parameter, unlike the ack/nack/dlq/replay routes.

## Problem
Two confirmed root causes (reproduced directly, not just inferred from the
pytest summary):

1. **`TypeError: publish() got an unexpected keyword argument '_principal'`**
   — reproduced by calling `TestClient.post("/publish", ...)` with
   `raise_server_exceptions=True` against the test app; the local `/publish`
   route wrapper in `test_eventbus_auth.py`'s `_make_test_app()` does:
   ```
   result = await eb_app.publish_route(request, _principal=_principal)
   ```
   but `scripts/eventbus/publish_route.py`'s `publish()` function has no
   `_principal` parameter. Any test that reaches this code path (i.e. passes
   authorization and hits the real publish handler) gets a 500 instead of
   200. Confirmed for `TestPublishAuth::test_publish_with_valid_publisher_token`.

2. **`sqlite3.OperationalError: unable to open database file`** — the shared
   `_init_local_state()` helper in this file calls
   `app.state.db = eb_app.open_db(cfg.db_path)` *before* it calls
   `pathlib.Path(cfg.storage_dir).mkdir(parents=True, exist_ok=True)`. This
   works only because most tests pass pytest's `tmp_path` fixture (which
   pytest pre-creates) or a class-level path that a `setup_class` explicitly
   `.mkdir()`s first. `TestUnified401ResponseFormat::test_missing_authorization_header_returns_unified_format`
   and (by the same pattern) `test_invalid_bearer_token_returns_unified_format`
   pass a literal `Path("/tmp/test-unified-401")` /
   `Path("/tmp/test-unified-401-invalid")` directly into `_make_test_app()`
   with no prior `.mkdir()`, so `open_db()` fails before the directory ever
   gets created.

The remaining ~11 of the 14 failing tests were not individually traced to one
of these two causes — some may share cause 1 or 2 (any test exercising
`/publish` end-to-end, or any test passing a literal not-pre-created `Path`),
and some may have independent causes not yet identified.

## Reason for Change
Uncovered via a full `uv run pytest tests/` run while syncing to
`origin/master` via the `git-commit-and-sync` skill (119 failed / 13 errors
total across the suite; this file accounts for 14 of the 119). These are
authorization-boundary tests — failures here mean auth-path regressions for
`/publish` and the unified-401 response format are currently unverified by
CI.

## Implementation Intent
- For cause 1: either add a `_principal` parameter to
  `scripts/eventbus/publish_route.py::publish()` (if publish is meant to
  participate in Principal-based per-request auditing/authorization like the
  other routes) or remove the `_principal=_principal` forwarding from this
  test file's local `/publish` wrapper (if publish intentionally has no
  Principal-specific behavior beyond the existing role check). Check
  `scripts/eventbus/app.py`'s real `/publish` route registration (not just
  this test file) to see which shape production code actually expects —
  the test harness's local wrapper should mirror production, not diverge
  from it.
- For cause 2: reorder `_init_local_state()` so the storage/offsets/deadletter
  directories (and the db path's parent) are created before `open_db()` is
  called, OR require every caller of `_make_test_app()` to pass a
  pre-existing directory (pytest `tmp_path`, or a `setup_class` that
  `.mkdir()`s first) and fix the two `TestUnified401ResponseFormat` call
  sites to do so instead of passing a literal un-created `Path`. Prefer
  fixing `_init_local_state()`'s ordering — it is a test-helper bug that can
  bite any future test written the "obvious" way.
- After both fixes, re-run the full file and re-triage any tests still
  failing; file follow-up issues for causes not covered by 1 or 2 rather
  than expanding this issue's scope.

## Target Files or Areas
- `tests/eventbus/test_eventbus_auth.py` (`_make_test_app()`'s local
  `/publish` route wrapper; `_init_local_state()`; the two
  `TestUnified401ResponseFormat` call sites at lines ~1022 and ~1047)
- `scripts/eventbus/publish_route.py` (`publish()` signature — read to
  determine if `_principal` should be added, per Implementation Intent)
- `scripts/eventbus/app.py` (real `/publish` route registration, for
  comparison against this test file's local wrapper)

## Required Changes
- Resolve the `_principal` keyword-argument mismatch between the test
  harness's `/publish` wrapper and `scripts/eventbus/publish_route.py::publish()`.
- Reorder or otherwise fix `_init_local_state()` so `open_db()` never runs
  before its target directory exists.
- Fix the two `TestUnified401ResponseFormat` tests' `_make_test_app()` calls
  if they are still relying on manual directory creation after the
  `_init_local_state()` fix.
- Re-run the full file; for any of the 14 originally-failing tests still
  failing after these two fixes, record the new failure reason (file as a
  follow-up issue rather than fixing inline here, to keep this issue's scope
  bounded to the two confirmed causes).

## Constraints
N/A: none identified

## Acceptance Criteria
- [ ] `uv run pytest tests/eventbus/test_eventbus_auth.py -v` — the count of
  failing tests is documented (ideally 0, but at minimum: every remaining
  failure has a newly identified, distinct root cause noted in a follow-up)
- [ ] `TestPublishAuth::test_publish_with_valid_publisher_token` passes
- [ ] `TestUnified401ResponseFormat::test_missing_authorization_header_returns_unified_format`
  and `test_invalid_bearer_token_returns_unified_format` pass
- [ ] No other `tests/eventbus/*.py` file regresses
  (`uv run pytest tests/eventbus/ -q`)

## Testing Expectations
`uv run pytest tests/eventbus/test_eventbus_auth.py -v` (targeted) and
`uv run pytest tests/eventbus/ -q` (regression check for the rest of the
eventbus suite). `uv run mypy scripts/` should stay green if
`publish_route.py`'s signature changes.

## Documentation Impact
N/A: test-only or internal-signature fix; no `docs/eventbus/*.md` currently
documents `publish_route.py`'s parameter list in a way that would need
updating (verify against `docs/eventbus/index.md` before closing if the
`publish()` signature changes).

## Out of Scope
- Do not fix the `_TOKEN_CONSUMER_MAP` `ImportError`s in the other four
  eventbus test files (filed separately, see Dependencies).
- Do not fix `test_partial_ack_replay` or the concurrent/DLQ pagination test
  failures (filed separately).
- Do not change `require_role`/`require_consumer_identity` authorization
  logic itself — only the `_principal` plumbing into `publish()` and the
  directory-creation ordering.

## Dependencies
N/A: none (independent of the `_TOKEN_CONSUMER_MAP` issue, though both were
discovered in the same sync session)

## Unresolved Questions
- Should `publish_route.py::publish()` gain a `_principal` parameter (to
  match ack/nack/dlq/replay), or should the test harness's wrapper stop
  passing one? This depends on whether publish is intended to participate in
  Principal-based per-request auditing — needs confirmation from whoever
  owns the Principal-refactor design (see `c85362a36` and any related ADR).
- Do any of the remaining ~11 untraced failing tests share cause 1 or 2, or
  do they have independent root causes? Needs a full re-triage after the two
  confirmed fixes land.

## AI Implementation Instruction
Fix only the two confirmed causes described above. After applying both
fixes, re-run `tests/eventbus/test_eventbus_auth.py -v` and report the exact
list of any tests still failing with their new failure reasons — do not
silently mark this issue done if failures remain; file a follow-up issue for
whatever is left instead of expanding this one's scope. Do not modify
`require_role`, `require_consumer_identity`, or any other eventbus
authorization logic beyond what's needed for the `_principal` plumbing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260917-110320
- **Related target files**: tests/eventbus/test_eventbus_auth.py, scripts/eventbus/publish_route.py, scripts/eventbus/app.py
