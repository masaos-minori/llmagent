## Goal
Update `tests/eventbus/test_eventbus_config.py`'s config-construction fixtures
(REQ-004) so they satisfy the current requirements.

**Correction (found during Step 3e/Step 4 full-suite validation, reversing this
document's original plan below):** UNK-01 was first resolved to "Yes"
(`__post_init__` requires a per-role token), then reverted to **No** after that
change broke 114+22 tests across 20+ files outside this Plan's scope — see
`implementations/20260913-122501_01_scripts_eventbus_config.py.md`'s own
Correction. Consequently, this file's **direct** `EventBusConfig(...)` construction
calls need **no** per-role-token addition at all; only its two `load_config()`-based
TOML fixtures do, because `load_config()`'s own pre-existing per-role-token check
(unrelated to UNK-01, unchanged by this Plan) already applied to the TOML-parsing
path before this Plan existed. The Procedure/Details below describe this document's
original (superseded) plan for historical traceability; the Execution Status Notes
record what was actually done.

## Scope
Only `tests/eventbus/test_eventbus_config.py`. No change to
`scripts/eventbus/config.py` itself (covered by the companion `config.py` document).

## Assumptions
- The companion document
  `implementations/20260913-122501_01_scripts_eventbus_config.py.md` (or its
  already-implemented result) makes `EventBusConfig.__post_init__` raise when no
  per-role token is set, in addition to the existing `auth_token` check — this
  document's fixture updates are written against that resolved requirement.
- `__post_init__`'s validation order is unchanged by the companion document (per-role
  check is added immediately after the existing `auth_token` check, i.e. before the
  `slow_consumer_threshold`/`backlog_health_threshold`/`replay_batch_size`/
  `subscriber_count`/`retained_event_count`/`publish_rate` checks) — confirmed by
  reading that document's Procedure. This matters because two of this file's
  `pytest.raises(match=...)` tests target checks that run *after* the per-role check
  in validation order (see Details).

## Design decisions
Add a single per-role token (`admin_token="test-token"`, matching this file's
existing `auth_token="test-token"` string for consistency) to every direct
`EventBusConfig(...)` construction that does not already have one — rather than
inventing a per-test-specific token value, since none of this file's own tests assert
anything about *which* per-role token is set, only that construction succeeds (or
fails for the specific reason each test targets).

## Alternatives considered
- **Add a shared fixture/helper that supplies default valid kwargs, reducing
  duplication across the file's 13 call sites**: rejected — this Plan's Scope is
  fixture *correctness* (REQ-004), not refactoring; introducing a new shared helper
  here is a larger, unrelated change and risks masking which specific kwargs each
  test intends to exercise. Each call site gets its own minimal, explicit
  `admin_token="test-token"` addition instead.

## Implementation
### Target file
tests/eventbus/test_eventbus_config.py

### Procedure
Add `admin_token="test-token"` to every direct `EventBusConfig(...)` call in this
file that currently has no per-role token, in these functions (line numbers as of
this document's generation):
1. `test_valid_config_with_host_field` (line 53) — normal-path construction, would
   now fail its own `assert cfg.port == 8015` line with a per-role-token
   `ValueError` instead.
2. `test_valid_threshold_configuration` (line 273) — same reason.
3. `test_slow_consumer_threshold_equal_to_maxsize_raises` (line 293) — **order
   matters here**: `__post_init__`'s per-role check runs before the
   `slow_consumer_threshold` check per this document's Assumptions, so without
   `admin_token` this test's `pytest.raises(match="slow_consumer_threshold")` would
   instead see the per-role-token `ValueError` and fail on the `match` regex, not
   pass for the wrong reason silently — confirm this is what actually happens (or
   already happens pre-fix) during Step 3a re-verification, not assumed here.
4. `test_backlog_health_threshold_exceeds_maxsize_raises` (line 310) — same ordering
   concern as #3.
5. `test_replay_batch_size_default_is_1000` (line 326) — normal-path construction.
6. `test_subscriber_count_default_is_10` (line 340) — same.
7. `test_retained_event_count_default_is_10000` (line 354) — same.
8. `test_publish_rate_default_is_100_0` (line 368) — same.

Do **not** add a per-role token to:
- `test_invalid_port_too_low` / `test_invalid_port_too_high` /
  `test_invalid_max_retry_zero` — these target checks (`port`, `max_retry`) that run
  *before* the `auth_token`/per-role-token checks in `__post_init__`'s order, so they
  already raise for their intended reason first and remain unaffected.
- `test_non_loopback_host_raises_value_error` (both cases) — the `host` check also
  runs before the per-role-token check; unaffected for the same reason.
- The `load_config()`-based tests (`test_load_config_rejects_stray_poll_interval_ms`,
  `test_load_config_rejects_unknown_key`, `test_load_config_rejects_wrong_type`,
  `test_load_config_rejects_empty_auth_token`, and any other TOML-fixture test whose
  TOML text has no per-role-token key) — these exercise `load_config()`'s own
  pre-existing per-role-token check (already present before this Plan, only its
  *indentation* changes per the companion `config.py` document, not its logic or
  which TOML inputs it rejects), which is `load_config()`'s own required-key
  validation happening in the TOML-parsing path, not `__post_init__`'s new check;
  each such rejection test's specific `match=` target is unaffected by this file's
  changes. Re-verify each individually against actual pre/post-fix behavior in Step
  3e — do not assume this categorization without running the tests.
- `test_load_config_call_sites_pass_get_config_path` — does not construct
  `EventBusConfig` directly at all (inspects `eventbus/app.py` source); unaffected.

### Method
Uniform, mechanical addition of one kwarg (`admin_token="test-token"`) to each
affected call site — no structural change to any test's assertions or `pytest.raises`
target.

### Details
- After adding `admin_token` to the 8 call sites above, run this file alone and
  triage any still-failing case individually — the ordering analysis above is this
  document's best understanding from reading `__post_init__`'s structure, not a
  substitute for actually running the tests (Step 3a/Step 4 will confirm or correct
  it).
- Any `load_config()`-based test not explicitly listed above that turns out to also
  need a per-role TOML key (discovered during Step 4, not predicted here) gets one
  added to its TOML fixture text the same way (`admin_token = "test-token"` line),
  scoped to that specific test only.

## Compatibility considerations
Test-only file; no production code or API-contract impact. Every test not listed
above as needing a change must continue to pass unchanged.

## Security considerations
N/A: test-only change; no production authorization logic modified.

## Rollback considerations
Single-file, test-only change — revert this file's diff to roll back. Independent of
the companion `config.py` document's own revert (see that document's Rollback
considerations).

## Validation plan
- Run `uv run pytest tests/eventbus/test_eventbus_config.py -v` and confirm every
  case passes, including the two currently-`ERROR`ing cases the source Plan names
  (AC-2) and the two `pytest.raises(match=...)` cases flagged above as
  order-sensitive.
- Run `uv run pytest tests/eventbus/ -q --timeout=30` to confirm no new regression.
- Run the standard validation sequence (`rules/toolchain.md`): ruff, mypy,
  lint-imports, bandit, diff-cover.

## Completion criteria
- Every test in this file passes, including the previously-`ERROR`ing cases (AC-2).
- No test's `pytest.raises(match=...)` target changed from what the source Plan/Issue
  intended for that test (i.e. no test now passes only because it happens to also
  match an unrelated per-role-token error).

## Out of scope
- `scripts/eventbus/config.py`'s own validation logic (companion document).
- `tests/eventbus/test_eventbus_auth.py` and
  `tests/eventbus/test_eventbus_subscribe.py`'s own fixtures — each has its own
  target-file document in this Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-142350 | 20260913-142350 | Added admin_token to load_config()-based TOML fixtures only (2 tests); direct-construction fixtures unaffected after UNK-01 was revised to No |
| 2 | Add or update tests per Validation plan | Completed | 20260913-142350 | 20260913-142350 | 22/22 tests pass (including new test_load_config_rejects_missing_per_role_token) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-142350 | 20260913-142350 | ruff/mypy/pre-commit all passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260913-142350 | 20260913-142350 | N/A: test-only file |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260913-093422_eb002_eventbus-per-role-token-validation-incomplete.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-094809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-122501
- **Related target files**: tests/eventbus/test_eventbus_config.py