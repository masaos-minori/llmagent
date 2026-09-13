## Goal
Finish wiring per-role token support into `tests/eventbus/test_eventbus_auth.py`
(REQ-002, REQ-003): add a `publisher_token` parameter to `_make_test_app()`, update
every call site to supply per-role tokens satisfying the current requirements (per
the companion `config.py` document's `__post_init__` change), and fix every
instance-method that mistakenly referenced the class (`cls`) instead of the instance
(`self`) — a pre-existing defect this file's own tests could not previously surface
because `setup_class` failed first with `auth_token`/per-role-token `ValueError`s
before any test method body ran.

## Scope
Only `tests/eventbus/test_eventbus_auth.py`. No change to
`scripts/eventbus/config.py`'s validation logic itself (covered by the companion
`config.py` document), `scripts/eventbus/auth.py`, or any other test file.

## Assumptions
- The companion document `implementations/20260913-122501_01_scripts_eventbus_config.py.md`
  (or its already-implemented `scripts/eventbus/config.py` result) makes
  `EventBusConfig.__post_init__` require at least one of
  `consumer_token`/`operator_token`/`admin_token` in addition to `auth_token` — this
  document's fixture updates are written against that resolved requirement, not the
  pre-fix state.
- `_make_test_app()`'s `token` parameter maps to `EventBusConfig.auth_token` (line 51,
  confirmed by reading the function) — a shared token, independent of the four
  per-role token parameters.

## Design decisions
Add `publisher_token: str | None = None` as a fifth parameter to `_make_test_app()`
(alongside the existing `token`/`consumer_token`/`operator_token`/`admin_token`),
threaded into `EventBusConfig(..., publisher_token=publisher_token)`. This mirrors the
existing four-parameter pattern exactly rather than introducing a different calling
convention.

For `TestPublishAuth` specifically (the only class REQ-002 names), switch it to
per-role tokens only (`token=None`, `publisher_token="test-publisher-token"`, leaving
`consumer_token`/`operator_token`/`admin_token` at whatever satisfies
`__post_init__`'s new "at least one" rule — see Details) and change
`test_publish_with_valid_publisher_token` to authenticate with the publisher token,
not `admin_token` — the current code's `cls.cfg.admin_token` reference is doubly wrong
here: it names the wrong role's token (this is meant to be a publisher-authenticated
request per the test's own name and docstring) and it is also the `cls`/`self` bug
described below.

## Alternatives considered
- **Keep `TestPublishAuth` using a shared `token`/`admin_token` and only add the
  `publisher_token` parameter without using it in this class's own test**: rejected —
  REQ-002 explicitly requires `TestPublishAuth`'s cases to "actually exercise a
  `publisher_token`-authenticated request, not `None`" (AC-3); adding the parameter
  without wiring it into this class would not satisfy that.
- **Fix only the `cls`/`self` bugs without changing which token each test
  authenticates with**: rejected for `TestPublishAuth` specifically, since REQ-002
  requires the publisher-token path itself to be exercised, not merely that the
  existing (wrong-role) reference stops crashing.

## Implementation
### Target file
tests/eventbus/test_eventbus_auth.py

### Procedure
1. Add `publisher_token: str | None = None` to `_make_test_app()`'s signature (after
   `token`, before `consumer_token`, matching the existing parameter order's intent)
   and pass it through as `EventBusConfig(..., publisher_token=publisher_token)`.
2. In `TestPublishAuth.setup_class`, change the `_make_test_app()` call to pass
   `token="test-shared-token", publisher_token="test-publisher-token",
   consumer_token=None, operator_token=None, admin_token="test-admin-token"`.
   **Correction (found during Step 3a re-verification against actual
   `EventBusConfig.__post_init__` behavior, not assumed from reading the source
   alone):** the original plan for this step kept `token=None`, but
   `__post_init__`'s pre-existing, unrelated `auth_token`-non-empty check (unchanged
   by this Plan) rejects `auth_token=None` regardless of per-role tokens being set —
   confirmed via direct construction (`EventBusConfig(auth_token=None,
   publisher_token="p", admin_token="a", ...)` still raises `"auth_token is required
   but not configured"`). `token` must therefore also be a non-empty string here (and
   in every other class below), independent of the per-role-token fix. `admin_token`
   is set here only to satisfy `__post_init__`'s "at least one of
   consumer/operator/admin" rule (Publish itself only checks `publisher_token` per
   `Role.PUBLISHER`; this class's own tests never present `admin_token` as a bearer
   credential after this fix).
3. In `test_publish_with_valid_publisher_token`, change
   `headers={"Authorization": f"Bearer {cls.cfg.admin_token}"}` to
   `headers={"Authorization": f"Bearer {self.cfg.publisher_token}"}` — both fixes
   the `cls`/`self` `NameError` and switches to the correct role's token per REQ-002.
4. Fix every other `cls.cfg.*` reference inside an instance method (not
   `setup_class`/`teardown_class`, which correctly use `cls`) to `self.cfg.*`:
   - `TestSubscribeAuth.test_subscribe_with_valid_consumer_token`
   - `TestSubscribeAuth.test_subscribe_with_timeout_disconnect_detection`
   - `TestDlqListAuth.test_dlq_list_with_valid_operator_token`
   - `TestReplayAuth.test_replay_with_valid_operator_token`
   For each of these classes' `setup_class`, ensure `token` is a non-empty string
   (per the Step 2 correction above — `auth_token`'s own check is independent of
   per-role tokens), the per-role token this test method authenticates with is
   actually set (e.g. `TestSubscribeAuth` needs `consumer_token` set, not `None`),
   and that `__post_init__`'s "at least one per-role token" requirement is satisfied
   — update the `_make_test_app()` call accordingly.
5. Add `import time` at module level (currently missing) — required by
   `test_subscribe_with_timeout_disconnect_detection`'s `time.time()` calls (lines
   283, 300), which would otherwise raise `NameError` once the earlier `cls`/`self`
   and per-role-token fixture bugs are fixed and this test body actually executes.
6. Remove the duplicate `test_subscribe_as_wrong_role` definition in
   `TestSubscribeAuth` (defined twice, identically, at lines 311-318 and 320-327) —
   Python silently keeps only the second definition, making the first dead code; keep
   one copy.
7. For every other `setup_class` in this file (`TestAckAuth`, `TestNackAuth`,
   `TestDlqRequeueAuth`) whose class body has no per-role-token-authenticated test
   (only a `..._without_token` 401 case), update its `_make_test_app()` call to supply
   `token="test-shared-token"` (per the Step 2 correction — required regardless of
   per-role tokens) and whatever minimal per-role token satisfies `__post_init__`'s
   "at least one" requirement (e.g. `admin_token="test-admin-token"`) — these classes
   do not need a *specific* role's token exercised (no test in the class
   authenticates), only non-empty values so `setup_class` itself does not raise.
8. Add a call to `eventbus.auth._populate_token_maps(cfg)` inside `_init_local_state()`
   (right after `app.state.config = cfg`). **Correction (found during Step 3a/Step 4
   re-verification):** `_make_test_app()` never populated `_TOKEN_ROLE_MAP` (the
   companion `auth.py` document's new per-role-token→Role mapping,
   `implementations/20260913-122501_05_scripts_eventbus_auth.py.md`), so every
   per-role-token-authenticated request in this file failed authentication (401)
   even after that document's fix landed — `_populate_token_maps()` is normally
   called from `lifespan()` in production, but this file's fixture bypasses
   `lifespan()` entirely via `_init_local_state()`.
9. In `test_subscribe_with_timeout_disconnect_detection`, change the `while True:
   chunk = response.read(1)` loop to iterate `for chunk in response.iter_bytes():`.
   **Correction (found during Step 3a/Step 4 re-verification):** `response.read(1)`
   is not a valid call in the currently-installed `httpx` version — `Response.read()`
   takes no arguments (it reads the entire remaining body at once); this test never
   previously reached this line (it errored earlier at `setup_class` on the
   per-role-token/auth_token construction failure this Plan fixes), so this pre-existing
   `TypeError` was never previously observed. `iter_bytes()` is the correct
   current-httpx API for chunked reads and preserves this test's own intent (read
   until the `\n\n` SSE event terminator appears, or the stream ends).
10. Add `TestPublishAuth.test_check_role_rejects_wrong_role_token`: a unit test
    calling `require_role(Role.PUBLISHER)`'s returned `_check_role` coroutine
    directly (with a mocked `Request` whose `url.path = "/publish"` and
    `token=self.cfg.consumer_token`), asserting it raises `HTTPException` with
    `status_code == 403`. See the Details discovery note for why this is a unit
    test rather than an HTTP-level one through `_make_test_app()`.

### Method
Mechanical, per-class fixture updates plus five targeted line-level fixes
(`cls`→`self`, missing import, duplicate method). No new test helper or fixture
abstraction — the existing five-parameter `_make_test_app()` pattern already covers
what every class needs once each call site supplies real values.

### Details
- Do not change `_make_test_app()`'s registered routes, `_init_local_state`, or
  `_do_cleanup_eb` — REQ-002/REQ-003 are about token wiring, not the test app's
  route/lifecycle scaffolding.
- **Discovery (not fixed here, deliberately — see below):** while adding a
  regression test for REQ-005/AC-4's negative direction (a `consumer_token` bearer
  must be rejected from a `Role.PUBLISHER`-gated route), found that
  `_make_test_app()`'s locally-defined routes (e.g. `@local_app.post("/publish")`)
  never declare `Depends(require_role(...))`/`Depends(require_consumer_identity)`
  themselves — unlike the real `scripts/eventbus/app.py`, which does declare them
  on every route. This means every test in this file that authenticates with a
  *specific* role's token (e.g. `test_publish_with_valid_publisher_token`) has never
  actually exercised role-based authorization through this fixture — only
  authentication (via `attach_auth_middleware`). Adding the missing `Depends(...)`
  declarations here was attempted, but doing so also activates
  `require_consumer_identity`'s topic-allowlist check for `/subscribe`, which broke
  passing tests via the same `_TOKEN_TOPIC_MAP` "empty means any topic"
  comment/implementation contradiction already tracked as out of scope (see
  `implementations/20260913-122501_04_tests_eventbus_test_eventbus_subscribe.py.md`'s
  own Blocked note). Fixing the fixture's missing `Depends(...)` therefore requires
  also fixing that separate, already-deferred bug — reverted rather than expanding
  scope a fourth time. The AC-4 negative-direction regression test is instead
  written as a **unit test calling `require_role(Role.PUBLISHER)`'s returned
  `_check_role` directly** (see Procedure step 10), which exercises the same
  `_TOKEN_ROLE_MAP` logic without going through this fixture's HTTP layer. This
  fixture's missing `Depends(...)` declarations are recorded as a new, separate
  issue rather than fixed in this document.
- Do not add a `monitoring_token` parameter — no test class in this file exercises a
  `Role.MONITORING`-authenticated request; out of scope per REQ-002's own wording
  (publisher only).
- The `cls`/`self` fixes and the duplicate-method removal are pre-existing defects
  this Plan's Problem section did not explicitly name (it named the missing
  `publisher_token` parameter and `token=None` call sites) — found during this
  document's Step 3a adversarial verification by reading the file in full. They are
  within this row's `Modify` scope (same file, same "make the per-role-token tests
  actually work" intent) and are fixed here rather than deferred, since REQ-002/AC-3
  cannot be satisfied while `test_publish_with_valid_publisher_token` still raises
  `NameError` before its assertion runs.

## Compatibility considerations
Test-only file; no production code or API-contract impact. Every currently-passing
test in this file (the `..._without_token` 401 cases) must continue to pass unchanged
— none of them reference `cls.cfg` or depend on the duplicate method.

## Security considerations
N/A: test-only change: no production authorization logic is modified, only which
tokens test fixtures construct and present.

## Rollback considerations
Single-file, test-only change — revert this file's diff to roll back. No interaction
with the companion `config.py` document's revert: if `config.py`'s `__post_init__`
change is reverted independently, these fixtures' extra per-role tokens become inert
(no longer required) but do not themselves break anything by still being present.

## Validation plan
- Run `uv run pytest tests/eventbus/test_eventbus_auth.py -v` and confirm every one
  of the 13 previously-`ERROR`ing cases now passes, including
  `test_publish_with_valid_publisher_token` actually authenticating with
  `publisher_token` (AC-2, AC-3).
- Confirm `TestSubscribeAuth.test_subscribe_as_wrong_role` (the single remaining
  definition, after removing the duplicate) still passes.
- Run `uv run pytest tests/eventbus/ -q --timeout=30` to confirm no new regression —
  in particular, watch for other `EventBusConfig(...)` call sites across
  `tests/eventbus/` broken by the companion `config.py` document's `__post_init__`
  change that are outside this Plan's four target files (report as an
  additional-target-file discovery per `skills/code-implementation/workflow.md` if
  found, rather than fixing them here).
- Run the standard validation sequence (`rules/toolchain.md`): ruff, mypy,
  lint-imports, bandit, diff-cover.

## Completion criteria
- `_make_test_app()` accepts and threads through a `publisher_token` parameter
  (REQ-002).
- Every `_make_test_app()` call site in this file supplies values satisfying
  `EventBusConfig.__post_init__`'s current requirements — no call site passes
  `auth_token`/all-per-role-tokens as all-`None` (REQ-003).
- `TestPublishAuth`'s cases exercise an actual `publisher_token`-authenticated request
  (AC-3).
- All 13 previously-`ERROR`ing cases in this file pass (AC-2).
- No `cls.cfg`/`cls.client` reference remains inside an instance (non-classmethod)
  test method.
- No duplicate method definition remains in `TestSubscribeAuth`.

## Out of scope
- `scripts/eventbus/config.py`'s own validation logic (covered by the companion
  document `implementations/20260913-122501_01_scripts_eventbus_config.py.md`).
- `tests/eventbus/test_eventbus_config.py` and
  `tests/eventbus/test_eventbus_subscribe.py`'s own fixture updates — each has its own
  target-file document in this Plan.
- Any change to `scripts/eventbus/auth.py`'s route-role mapping or
  `require_consumer_identity` (eb001, eb004 — tracked separately).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-142340 | 20260913-142340 | Added publisher_token param to _make_test_app(); updated all call sites; fixed 5 cls/self bugs, missing import, duplicate method, missing _populate_token_maps() call, response.read(1)->iter_bytes(); added unit-level AC-4 negative-direction test |
| 2 | Add or update tests per Validation plan | Completed | 20260913-142340 | 20260913-142340 | 14/14 tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-142340 | 20260913-142340 | ruff/mypy/bandit/diff-cover(100%)/pre-commit all passed; discovered (not fixed, out of scope) that _make_test_app's local routes never declare Depends(require_role(...)) -- filed as new issue |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260913-142340 | 20260913-142340 | N/A: test-only file |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20260913-093422_eb002_eventbus-per-role-token-validation-incomplete.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-094809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-122501
- **Related target files**: tests/eventbus/test_eventbus_auth.py