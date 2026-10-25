## Goal

Add two real-subprocess startup tests to `tests/eventbus/test_eventbus_startup.py`: a correctly-stamped-but-malformed EventBus database is rejected at startup (`REQ-002`), and a canonical database passes the provisional readiness gate (`db == ok` AND `dlq_task == running`) (`REQ-004`), both mirroring the existing `subprocess.Popen([sys.executable, "-m", "eventbus.app"])` pattern already in the file.

## Scope

- Modify `tests/eventbus/test_eventbus_startup.py` only: append the two startup tests below the existing `test_main_failing_lifespan_exits_without_attributeerror` (line 250).
- Do not modify `scripts/eventbus/app.py`, `scripts/eventbus/schema.py`, `scripts/eventbus/db_conn.py`, or `scripts/eventbus/health_route.py` here — they are the runtime/deployment targets these tests verify (`REQ-002`, `REQ-004`).

## Assumptions

- `open_db()` in `scripts/eventbus/db_conn.py` calls `_init_schema()` (db_conn.py line 43) on every connection, so a malformed stamped database fails the uvicorn lifespan and the subprocess exits non-zero.
- `_init_schema()` in `scripts/eventbus/schema.py` (lines 66-90) returns early once `user_version` matches; after `REQ-002` it additionally validates shape against the shared fingerprint, so a stamped-but-malformed database raises where it previously returned cleanly.
- The subprocess inherits a valid `EVENTBUS_SCHEMA_PATH` (the event envelope schema read at `scripts/eventbus/app.py` line 75) from the pytest environment, exactly as `test_main_post_start_verification_binds_loopback` does.
- `/health` in `scripts/eventbus/health_route.py` requires the `MONITORING` role, which the config `auth_token` holds, so a `Bearer <auth_token>` request succeeds and returns `db`/`dlq_task`/`status`.

## Design decisions

- **Mirror the existing subprocess harness.** Both new tests build a `EventBusConfig`-style TOML, launch `subprocess.Popen([sys.executable, "-m", "eventbus.app"], env={...})` with `EVENTBUS_CONFIG_PATH`, `EVENTBUS_SCHEMA_PATH`, and `PATH`, set `cwd` to the scripts directory, and capture `stdout`/`stderr` — the identical pattern at lines 169-180 and 226-237 — so they exercise the real `_main()`/lifespan path, not a unit stub.
- **Reject case drives the failure at `_init_schema()`.** The malformed test pre-provisions a database that is stamped with the current version but structurally malformed (a schema omitting one required column), so `_init_schema()` reaches its shape check and raises; the test asserts the same `"Application startup failed. Exiting."` output and non-zero return code the failing-lifespan test asserts (line 241).
- **Pass case asserts the provisional readiness signal, not `status == ok`.** The canonical test waits for a loopback connection (as `test_main_post_start_verification_binds_loopback` does at lines 182-196), then reads `/health` and asserts `db == ok` AND `dlq_task == running`, tolerating a non-200 body that carries only capacity-only reasons — matching the deploy gate semantics rather than requiring a fully clean `/health`.

## Alternatives considered

- **Unit-test `_init_schema()` directly.** Rejected: the acceptance criterion is that the failure surfaces through the real startup process; a subprocess test proves the whole lifespan chain fails closed, which a direct call does not.
- **Require `status == ok` for the pass case.** Rejected: `/health` returns 503 on transient capacity degradation, so `status == ok` would be brittle; the provisional `db == ok` AND `dlq_task == running` signal is the intended readiness predicate.

## Implementation

### Target file

`tests/eventbus/test_eventbus_startup.py`

### Procedure

1. Open `tests/eventbus/test_eventbus_startup.py` and locate the existing subprocess harness: the first `subprocess.Popen` block at lines 169-180 (env dict at lines 172-173, `cwd` at line 176) and the cleanup pattern at lines 244-250.
2. Append `test_main_malformed_stamped_db_rejected_at_startup` (new) after line 250: build a config pointing at a pre-provisioned malformed-but-stamped EventBus database, launch the subprocess with the pattern from lines 169-180, `wait`, and assert `"Application startup failed. Exiting."` is present (line 241) and `returncode != 0`.
3. Append `test_main_canonical_db_passes_readiness_gate` (new) after that: build a config pointing at a canonical EventBus database, launch with the same pattern, wait for a loopback connection using the free port from `_free_loopback_port` (lines 144-147), then read `/health` with a `Bearer` auth header and assert the readiness predicate holds.

### Method

- Write the TOML config with the same five-line shape used at lines 159-167 (`port`, `db_path`, `storage_dir`, `deadletter_dir`, `max_retry`, `host = "127.0.0.1"`, `auth_token = "test-token"`), reusing `_free_loopback_port()` for an unused port so nothing binds during setup.
- For the malformed database, open a fresh `sqlite3` connection to the configured `db_path`, apply a schema that omits one required column (for example the `events.topic` column from `scripts/eventbus/schema.sql`), and stamp `PRAGMA user_version` to the current expected version, so the database is correctly stamped yet structurally malformed.
- For the canonical database, apply the full `scripts/eventbus/schema.sql` to the configured `db_path` (which stamps `user_version`), so `open_db()` finds a correctly-stamped, shape-valid database.
- Launch via `subprocess.Popen` with `env` carrying `EVENTBUS_CONFIG_PATH` (the written TOML), `EVENTBUS_SCHEMA_PATH` (inherited valid envelope schema), and `PATH`, and `cwd` set to `Path(__file__).resolve().parents[2] / "scripts"` (line 176).
- In the reject test, call `proc.wait(timeout=20.0)`, read `proc.stdout`, and assert the startup-failure string and a non-zero `proc.returncode`, then run the cleanup at lines 244-250.
- In the pass test, poll a loopback connection to the configured port (lines 182-196), then issue an authenticated `GET /health` and parse the JSON body; assert `db == ok` and `dlq_task == running`, treating any HTTP status (200 or a capacity-only 503) as acceptable because the readiness predicate is read from the body fields.

### Details

- The malformed schema deviates from `schema.sql` in exactly one structural way (a missing required column) so the only difference from canonical is the shape, isolating the `_init_schema()` shape rejection from any version-stamp mismatch.
- The pass test reads the readiness fields from the `/health` body rather than asserting HTTP 200, so a healthy start on a transient capacity signal still counts as ready — the same tolerance the deploy gate applies.
- Both tests terminate the child in a `finally` block identical to lines 244-250 (`terminate`, `wait`, `kill` on timeout).

## Compatibility considerations

- The additions are two new module-level test functions appended after line 250; no existing test, import, or fixture changes, so the public-bind suite is unaffected.

## Security considerations

- The tests use throwaway `tmp_path` databases and a random per-test port; no real secrets or production paths are touched. The `auth_token` is a test-only value.

## Rollback considerations

- Delete the two appended test functions (or `git checkout` the parent commit); the existing tests and imports are unchanged.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_eventbus_startup.py` | Subprocess: malformed stamped DB rejected at startup; canonical DB passes the readiness predicate | `uv run pytest tests/eventbus/test_eventbus_startup.py` | malformed DB exits non-zero with "Application startup failed"; canonical DB binds and reports `db == ok` and `dlq_task == running` |

## Completion criteria

- `test_main_malformed_stamped_db_rejected_at_startup` (new) asserts the subprocess fails startup with a correctly-stamped-but-malformed EventBus database.
- `test_main_canonical_db_passes_readiness_gate` (new) asserts a canonical database reaches `db == ok` and `dlq_task == running`.
- `ruff`, `mypy`, `bandit`, `lint-imports`, the `tests/eventbus` suite, and diff-cover pass.

## Out of Scope

- The runtime shape gate in `scripts/eventbus/schema.py` (`REQ-002`), the `init_db.sh` strict gate (`REQ-003`), the deploy readiness gate in `deploy/setup_services.sh` (`REQ-004`), and the config/token preflight (`REQ-005`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append `test_main_malformed_stamped_db_rejected_at_startup` (new) mirroring the subprocess harness (lines 169-180) | Pending | — | — | REQ-002 |
| 2 | Append `test_main_canonical_db_passes_readiness_gate` (new) asserting the readiness predicate | Pending | — | — | REQ-004 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-only |

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
- **Requirement ID**: `REQ-002`, `REQ-004`
- **Source issue**: `issues/20261023-154326_eventbus003_startup-gate-schema-health.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-111552_eventbus003_startup-gate-schema-health.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-155039
- **Related target files**: `tests/eventbus/test_eventbus_startup.py`
