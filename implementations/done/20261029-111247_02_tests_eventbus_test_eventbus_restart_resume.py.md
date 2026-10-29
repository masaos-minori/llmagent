# Implementation Procedure: tests/eventbus/test_eventbus_restart_resume.py

<!-- Generated from plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md row: tests/eventbus/test_eventbus_restart_resume.py -->
<!-- Preserve this header comment; it links the procedure back to the Plan target file table row. -->

## Goal

Add true two-lifecycle restart/resume scenario tests driven by the production lifespan,
resolve the skipped probe test, and rename the ambiguous unit test names, so at-least-once
resume semantics are covered through HTTP routes instead of only direct repository calls
(`REQ-001..REQ-006`; AC-1..AC-4).

## Scope

`tests/eventbus/test_eventbus_restart_resume.py` only: one import addition, eight new tests,
one skip resolution, three test renames. The fixture itself lives in `eventbus_helpers.py`
(procedure `20261029-111247_01`). Existing tests keep their assertions; the file-local
`client` fixture and its `_init_state`/`_do_cleanup` (`:21-49`) stay untouched for existing
tests.

## Assumptions

- Source claims re-verified this cycle: file-local `_init_state` (`:21-33`), `_do_cleanup`
  (`:36-48`), `client` fixture (`:51-91`, monkeypatches `load_config`,
  `_ENVELOPE_SCHEMA_PATH`, `get_schema_path` at `:64-69`, enters `TestClient(eb_app.app)`
  as a context manager at `:81`), `_pub` (`:94`), skipped probe
  `test_resume_from_sqlite_offset` (`@pytest.mark.skip` `:196-201`, def `:202`, blocking
  `client.get("/subscribe")` `:257-264`, assertions `:247-270`), class
  `TestOutOfOrderAckNoSkipOnReconnect` (`:273`), unit tests
  `test_out_of_order_ack_no_skip_on_reconnect` (`:313`), `test_ordered_ack_baseline`
  (`:377`), `test_get_resume_position_no_offset` (`:429`), `_reconnect_ids` (`:448-463`,
  sets `sse_idle_timeout` 0.5 via `object.__setattr__` at `:452` with `timeout=5.0`),
  `_ack` (`:466`), single-lifecycle reconnect tests (`:475`, `:486`).
- Fixture contract (Plan Design, corrected 2026-10-29): `eventbus_two_lifecycle_clients` (new)
  yields `(open_client, snapshots)`; `open_client()` enters `TestClient(eb_app.app)` so the
  production lifespan (`scripts/eventbus/app.py:70-137`) builds and tears down `app.state`;
  each entry appends the fresh `app.state.db` handle and broker identity to `snapshots`;
  two lifecycles are sequential `with open_client()` blocks because the app is a
  module-level singleton (`app.state.db = None` at `app.py:135`).
- DB-row assertions open a plain `sqlite3` connection on `tmp_path / "eventbus.sqlite"` with
  `sqlite3.Row` between lifecycle phases, matching the existing unit-test pattern
  (`:320-322`).
- Baseline: `tests/eventbus` 411 passed / 1 skipped; the skip resolution removes that skip.
- Verification corrections (adversarial re-verification on 2026-10-29 against the landed
  implementation from origin commit `c456138f8`):
  - Fixture registration: `eventbus_two_lifecycle_clients` lives in `eventbus_helpers.py`
    as a plain generator (`:181`); the test module registers a local delegating
    `@pytest.fixture` (`:113`) instead of importing the name directly, matching the repo
    pattern (decorating or importing the helper caused ruff F811 shadow errors).
  - T4/T5 expectations were wrong against verified resume semantics
    (`delivery_repo.get_resume_position` `:261-306`): replay has no ack filtering
    (at-least-once redelivery), a consumer that acked a middle seq resumes at the lowest
    unacked seq, and a consumer with no offset resumes from 0. Corrected in the Details
    rows below; T5 renamed `test_restart_new_consumer_starts_from_zero`.
  - Skip resolution landed with the bounded read plus `headers=eventbus_auth_headers(
    "consumer")` on the `/subscribe` call (CONSUMER role required, `app.py`).
- Overlap: procedure `20261029-111247_01` (fixture in `eventbus_helpers.py`) must land
  first. `ebtestdrift007` lists this file too; per both plans, ebresumetest004 lands first.

## Design decisions

- Import the helper fixture by name (`from tests.eventbus.eventbus_helpers import
  eventbus_two_lifecycle_clients`); pytest resolves imported generator fixtures in the
  test module's namespace. The file-local `client` fixture stays for the existing tests.
- Sync `TestClient` + existing `_reconnect_ids` (bounded SSE drain via `sse_idle_timeout`)
  instead of `httpx.AsyncClient`: proven in this file, avoids the ebsse01 blocking issue
  (Plan UNK-02 decision: TestClient pattern) and satisfies `REQ-006` (AC-4).
- Fresh-state verification per `REQ-003` (AC-2) uses the fixture `snapshots`: after both
  lifecycle blocks, the two recorded db handles and brokers differ, and the first handle
  reports `_shutting_down` True (`scripts/eventbus/db_conn.py:15`). No new
  state-inspection helper in this file.

## Alternatives considered

- `httpx.AsyncClient` + anyio for scenario tests: rejected — `_reconnect_ids` already
  drains SSE within the idle timeout through `TestClient`; async would add a second HTTP
  mechanism to the file.
- Reusing the file-local `client` fixture twice: rejected — a fixture yields one lifecycle;
  the Plan requires two independent lifecycles with verifiable fresh state.
- Deleting `test_resume_from_sqlite_offset` outright (`REQ-005` allows remove-or-replace):
  rejected as first choice — the test body plus a bounded read is cheap coverage; deletion
  stays the fallback if the two-run gate fails.

## Implementation

### Target file

`tests/eventbus/test_eventbus_restart_resume.py`

### Procedure

1. Extend the import at `:15` with `eventbus_two_lifecycle_clients` (new) from
   `tests.eventbus.eventbus_helpers` (lands with procedure `20261029-111247_01`).
2. Add the probe test `test_two_lifecycle_probe_fresh_state` (new) first (Phase 1 gate,
   Details row T8): on failure STOP and file a defect report per the Plan (REQ-001, REQ-003;
   no further scenario tests).
3. Add the seven scenario tests listed in Details rows T1-T7, each using
   `eventbus_two_lifecycle_clients` (new), `_pub`, `_ack`, `_reconnect_ids`, and
   direct-`sqlite3` row checks, following the Method template (`REQ-002`, `REQ-006`).
4. Resolve the skipped test (Plan UNK-01, `REQ-005`): delete the `@pytest.mark.skip`
   decorator (`:196-201`) and replace the blocking read at `:257-264` with the bounded
   pattern from `_reconnect_ids` (`object.__setattr__(eb_app.app.state.config,
   "sse_idle_timeout", 0.5)` before the request, `timeout=5.0` on it); keep every existing
   assertion (`:247-270`). Runtime gate: if the test still fails after two runs, delete it
   per the `REQ-005` remove-or-replace allowance and note the replacement by T1/T2.
5. Rename in place (docstrings and bodies unchanged) (`REQ-004`; AC-3):
   `test_out_of_order_ack_no_skip_on_reconnect` → `test_unit_midsequence_ack_resume_position` (new)
   (`:313`), `test_ordered_ack_baseline` → `test_unit_inorder_ack_resume_position` (new) (`:377`),
   `test_get_resume_position_no_offset` → `test_unit_get_resume_position_defaults_to_zero` (new)
   (`:429`). Class name `TestOutOfOrderAckNoSkipOnReconnect` and `_create_tables` stay.
6. Run `rg -n "_init_state|_do_cleanup" tests/eventbus/test_eventbus_restart_resume.py` and
   confirm no new test calls them (`REQ-003`; the pre-existing local definitions and
   `client` fixture usage remain).

### Method

Scenario test template (every new test follows this shape):

```python
def test_restart_<scenario>(
    eventbus_two_lifecycle_clients: Any, tmp_path: Path
) -> None:
    open_client, snapshots = eventbus_two_lifecycle_clients
    with open_client() as client_1:
        # phase A: publish/ack/read through HTTP (_pub, _ack, _reconnect_ids)
        ...
    with open_client() as client_2:
        # phase B: resume assertions through HTTP on the fresh lifecycle
        ...
    # fresh-state gate (REQ-003, AC-2)
    (db_1, broker_1), (db_2, broker_2) = snapshots
    assert db_1 is not db_2 and broker_1 is not broker_2
    assert db_1._shutting_down is True
```

### Details

| Row | Name (new unless stated) | Phase A (client_1) | Phase B (client_2) / assertions | Ref |
|-----|--------------------------|--------------------|---------------------------------|-----|
| T1 | `test_restart_unacked_redelivery_single_consumer` (new) | publish 2 on topic `t`; `_reconnect_ids` drains `[1,2]`; `_ack` first event only | `_reconnect_ids` returns `[2]` only | REQ-002 |
| T2 | `test_restart_resume_position_skips_acked` (new) | publish 3; `_ack` events 1-2 | `_reconnect_ids` returns `[3]`; `consumer_offsets` row equals seq 2 via direct sqlite read | REQ-002 |
| T3 | `test_restart_midsequence_ack_resume_position` (new) | publish 3; `_ack` events 2 and 3 (offset high-water = seq 3) | `_reconnect_ids` starts at the lowest unacked seq → `[1,2,3]` delivery of the unacked set; DB offset equals seq 3 | REQ-002 |
| T4 | `test_restart_two_consumers_independent_resume` (new) | publish 3; `_ack` event 1 with `A`; `_ack` event 2 with `B` | `_reconnect_ids(c2, "A")` returns `[2,3]` (excludes acked event 1); `_reconnect_ids(c2, "B")` returns `[1,2,3]` (seq 1 unacked below offset 2 → resume restarts at 1, no ack filtering); two independent `consumer_offsets` rows | REQ-002 |
| T5 | `test_restart_new_consumer_starts_from_zero` (new; renamed from `test_restart_new_consumer_sees_only_new` after semantics verification) | publish 2; `_ack` both with `svc-old` | publish event 3 on client_2, then `_reconnect_ids(c2, "svc-new")` returns `[1,2,3]`: no offset row → resume position 0 → all events redelivered | REQ-002 |
| T6 | `test_restart_reconnect_consumer_id_reuse` (new) | publish 2; `_ack` event 1 with `svc-reuse`; direct sqlite read of `consumer_offsets.offset` equals event 1's seq | `_reconnect_ids(c2, "svc-reuse")` returns `[2]` | REQ-002 |
| T7 | `test_restart_offset_gap_no_silent_skip` (new) | publish and `_ack` 3 events (offset = 3); delete the `consumer_delivery` row of seq 2 via direct sqlite between lifecycles | `_reconnect_ids` returns `[2]` (gap event replayed, no silent skip to 3); `consumer_offsets.offset` still 3 | REQ-002, REQ-006 |
| T8 | `test_two_lifecycle_probe_fresh_state` (new) (REQ-001 probe; runs first in file order) | one `_reconnect_ids` read on topic `t` | after re-entry and both exits: db handles and brokers differ, first handle `_shutting_down` is True | REQ-001, REQ-003, AC-2 |
| S1 | skip resolution of `test_resume_from_sqlite_offset` | remove decorator; bounded read (`sse_idle_timeout` 0.5 + `timeout=5.0`) | all existing assertions kept (`:247-270`) | REQ-005, UNK-01 |
| R1-R3 | renames `test_unit_midsequence_ack_resume_position` (new), `test_unit_inorder_ack_resume_position` (new), `test_unit_get_resume_position_defaults_to_zero` (new) | name-only edits at `:313`, `:377`, `:429` | assertion bodies unchanged | REQ-004, AC-3 |

Every new test also carries the Method-template fresh-state gate (`REQ-003`) and finite
idle-timeout termination (`REQ-006`; AC-4).

## Compatibility considerations

- Existing single-lifecycle tests and the file-local `client` fixture keep working
  unchanged; renames are collect-only-identical apart from the three names.
- New tests run against the same module-level `eb_app.app`; sequential lifecycle entry
  avoids cross-test state leakage already bounded by `tests/eventbus/conftest.py` autouse
  resets (Plan Affected areas).

## Security considerations

- None specific; token usage follows `eventbus_test_tokens`.

## Rollback considerations

- Remove the added tests and restore the skip decorator/old names; no production or data
  impact.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -q` (file skip count drops
  from 1 to 0, or the documented fallback applies).
- Run the same file twice in one session, then `uv run pytest tests/eventbus` (Plan Phase 3;
  baseline 411 passed / 1 skipped becomes 420 passed / 0 skipped once all three procedures
  land; renames count-neutral).
- `uv run pytest --collect-only tests/eventbus/test_eventbus_restart_resume.py` diff shows
  exactly the 8 new names and 3 renames (`REQ-004`; AC-3).
- `uv run ruff check tests/eventbus/test_eventbus_restart_resume.py`; `uv run mypy
  tests/eventbus` stays at zero errors.

## Completion criteria

- Probe test passes (or the Plan STOP path is filed); seven scenario tests plus renames land;
  no skipped test remains in the file without a current citation (`REQ-005`; AC-3).
- Suite is deterministic across double runs (`REQ-006`; AC-4).

## Out of Scope

- Fixture and config builder code (procedure `20261029-111247_01`).
- `test_eventbus_replay_subscribe.py` rename (procedure `20261029-111247_03`).
- Production fixes if the probe exposes a lifecycle leak (Plan: stop and report).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-10-29 | 2026-10-29 | landed via origin c456138f8 (fixture + probe + T1-T7 + skip resolution + 3 renames); T4/T5 expectations corrected post-landing to verified resume semantics, T5 renamed test_restart_new_consumer_starts_from_zero |
| 2 | Add or update tests per Validation plan | Completed | 2026-10-29 | 2026-10-29 | file: 17 collected, 17 passed, 0 skipped, deterministic across double runs; collect diff 8 new + 3 renames vs baseline |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-29 | 2026-10-29 | tests/eventbus 439 passed / 0 skipped; ruff check + format clean; mypy tests/eventbus clean (34 files) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-29 | 2026-10-29 | no docs in scope per Out of Scope |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004, REQ-005, REQ-006
- **Source issue**: issues/20261028-122337_ebresumetest004_subscribe-restart-integration-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-111247
- **Related target files**: tests/eventbus/test_eventbus_restart_resume.py
