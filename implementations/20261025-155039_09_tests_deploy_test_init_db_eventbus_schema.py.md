## Goal

Add a shell/integration test for `deploy/init_db.sh` (`REQ-003`): the script aborts when the EventBus database is stamped with the current version but structurally malformed, and passes when it is canonical, mirroring the `tests/deploy/test_load_env_gate.py` driver/convention.

## Scope

- Create `tests/deploy/test_init_db_eventbus_schema.py` only: a new deploy shell-test that invokes the real `deploy/init_db.sh` and asserts abort-on-malformed and pass-on-canonical.
- Do not modify `deploy/init_db.sh`, `scripts/db/create_schema.py`, `scripts/shared/eventbus_schema_fingerprint.py`, or any other target here — they are the deployment/runtime targets this test verifies (`REQ-003`).

## Assumptions

- `deploy/init_db.sh` hardcodes its paths: `DEPLOY_SCRIPTS="/opt/llm/scripts"` and `DEPLOY_DB="/opt/llm/db"` (lines 14-15), so the script always reads `create_schema.py` from `/opt/llm/scripts/db` and writes to `/opt/llm/db`. The test therefore provisions the EventBus database at the production path `/opt/llm/db/eventbus.sqlite` and runs the real script, which targets those same absolute paths.
- `init_db.sh` runs `create_schema.py` via `uv run` from the `/opt/llm` cwd at line 31, so the test must run in an environment where `/opt/llm/scripts/db/create_schema.py` exists and `/opt/llm/db` is writable (i.e. a deployed environment).
- After `REQ-003`, `create_eventbus_schema()` validates shape against the shared fingerprint and fails closed on a malformed database already stamped with the current version, so `init_db.sh` aborts at the line 31 step before reaching the EventBus verification.
- The completion banner at line 63 (`=== init_db.sh: 完了 ===`) marks a successful run; its absence plus a non-zero exit marks the abort.

## Design decisions

- **Mirror `test_load_env_gate.py`.** The new module uses `_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]`, a `_write_init_db_driver` (new) helper that writes a `driver.sh` invoking the real `deploy/init_db.sh`, a `_run` helper that runs `bash driver.sh` with `capture_output=True`, `text=True`, `timeout=30`, `check=False`, and per-case assertions on `returncode`/`stdout`/`stderr` — the identical harness shape.
- **Provision the EventBus database in Python, drive the script from the driver.** Provisioning a stamped SQLite database is natural in Python (`sqlite3`), so `_provision_eventbus_db` (new) builds the malformed-or-canonical database at the production path; the `driver.sh` only runs `init_db.sh`, keeping the driver a thin wrapper exactly like the load-env gate.
- **Assert end-to-end behavior, not the internal abort point.** The malformed case asserts a non-zero exit and the missing completion banner; the canonical case asserts exit 0 and the completion banner present. This isolates the test from WHERE the shared validator raises (line 31 via `create_eventbus_schema`) and only checks that `init_db.sh` reports the state correctly.

## Alternatives considered

- **Copy `init_db.sh` into a temp dir with rewritten paths.** Rejected: that tests a modified copy, not the real script; the acceptance criterion is that the shipped `init_db.sh` behaves correctly, so the real script must be spawned.
- **Assert the exact exception text from `create_eventbus_schema`.** Rejected: the shared-validator message is an implementation detail that may change; asserting exit code + banner is stable across the fail-closed implementation.

## Implementation

### Target file

`tests/deploy/test_init_db_eventbus_schema.py` (new)

### Procedure

1. Open `deploy/init_db.sh` and confirm the hardcoded paths at lines 14-15 (`DEPLOY_SCRIPTS`, `DEPLOY_DB`), the `create_schema.py` invocation at line 31, the bare EventBus `.tables` print at lines 60-61, and the completion banner at line 63.
2. Create `tests/deploy/test_init_db_eventbus_schema.py` with `_REPO_ROOT`, the `deploy/init_db.sh` reference, a `_provision_eventbus_db` (new) helper, a `_write_init_db_driver` (new) helper, a `_run` helper matching the load-env gate, and the two tests below.
3. Write `test_init_db_malformed_stamped_aborts` (new): provision a malformed-but-stamped EventBus database, run the driver, and assert the abort signature.
4. Write `test_init_db_canonical_passes` (new): provision a canonical EventBus database, run the driver, and assert the success signature.

### Method

- `_provision_eventbus_db` (new) opens a fresh `sqlite3` connection at `/opt/llm/db/eventbus.sqlite` (creating `/opt/llm/db` if needed) and either applies the full `scripts/eventbus/schema.sql` plus the current version stamp for the canonical case, or applies a schema that omits one required column (for example the `events.topic` column from `schema.sql`) and stamps the current version for the malformed case, so the only deviation from canonical is the shape.
- `_write_init_db_driver` (new) writes `driver.sh` containing `set -euo pipefail`, the absolute `deploy/init_db.sh` path, and a single `bash "${INIT_DB}"` line that captures the script's stdout/stderr for the caller.
- `_run` mirrors the load-env gate: it builds a minimal `PATH` env, runs `bash driver.sh` with `capture_output=True`, `text=True`, `timeout=30`, `check=False`, and returns the `CompletedProcess`.
- In the malformed test, call `_provision_eventbus_db(malformed=True)`, then `_run(_write_init_db_driver(tmp_path))`, and assert `result.returncode != 0`, that the completion banner is absent from stdout, and that stderr carries a failure indicator.
- In the canonical test, call `_provision_eventbus_db(malformed=False)`, then `_run(...)`, and assert `result.returncode == 0`, that the completion banner is present in stdout, and that the EventBus `.tables` output was produced.

### Details

- The malformed database is stamped with the current expected version so the failure is purely a shape rejection, not a version-stamp mismatch — this isolates the `REQ-003` shape gate from any version logic.
- Provisioning writes to the production path `/opt/llm/db/eventbus.sqlite`; the test must run where that path is writable, consistent with `init_db.sh` itself requiring the deployed environment.
- `init_db.sh` runs `create_schema.py` for all four databases before the EventBus step, so the canonical run also creates the rag, session, and workflow databases; the assertion focuses on the completion banner and the EventBus tables output rather than on every database.
- No new shell function is introduced; the driver reuses the `uv run` flags already used by `init_db.sh` because it spawns the real script unchanged.

## Compatibility considerations

- The new module is a standalone test file appended under `tests/deploy/`; it shares no imports with `test_load_env_gate.py` beyond the mirrored helper shape, so neither suite affects the other.

## Security considerations

- The test provisions throwaway databases under the deployment DB directory and spawns the real deploy script; it touches no secrets. The only values it writes are schema DDL and a version stamp.

## Rollback considerations

- Delete the new test file (or `git checkout` the parent commit); no existing file is modified.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/deploy/test_init_db_eventbus_schema.py` | Integration: `init_db.sh` aborts on a malformed-stamped EventBus DB, passes on a canonical one | `uv run pytest tests/deploy/test_init_db_eventbus_schema.py` | malformed DB exits non-zero with the completion banner absent; canonical DB exits 0 with the completion banner present and EventBus tables printed |

## Completion criteria

- `test_init_db_malformed_stamped_aborts` (new) asserts `init_db.sh` exits non-zero when the EventBus database is stamped but structurally malformed.
- `test_init_db_canonical_passes` (new) asserts `init_db.sh` exits 0 with the completion banner present when the EventBus database is canonical.
- `shellcheck`, `ruff`, `mypy`, `bandit`, and `lint-imports` pass.

## Out of Scope

- The runtime startup gate (`REQ-002`), the deploy readiness gate in `deploy/setup_services.sh` (`REQ-004`), the config/token preflight (`REQ-005`), and the patched-shape test fixes (`REQ-006`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/deploy/test_init_db_eventbus_schema.py` (new) mirroring the load-env gate harness | Pending | — | — | REQ-003 |
| 2 | Add `test_init_db_malformed_stamped_aborts` (new) asserting abort on a malformed-stamped EventBus DB | Pending | — | — | REQ-003 |
| 3 | Add `test_init_db_canonical_passes` (new) asserting success on a canonical EventBus DB | Pending | — | — | REQ-003 |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-only |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261023-154326_eventbus003_startup-gate-schema-health.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-111552_eventbus003_startup-gate-schema-health.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-155039
- **Related target files**: `tests/deploy/test_init_db_eventbus_schema.py`
