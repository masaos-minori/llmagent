## Goal

Expose the MDQ server's auth and health inputs for self-validation, add the validation results, and
publish the resulting Security Posture from mdq-mcp's own `/health` implementation (`REQ-011`,
`REQ-002`, `AC-005`).

## Scope

- One modified module `scripts/mcp_servers/mdq/health_check.py`:
  - add `validate_mdq_security()` (new) producing `SecurityCheckResult` values;
  - extend `check_health()` (`scripts/mcp_servers/mdq/health_check.py:100-137`) to build the posture
    and pass it to `make_health_response()` (row `06`).
- No change to `scripts/mcp_servers/mdq/mdq_server.py` is required: its `/health` handler at
  `mdq_server.py:408-411` delegates entirely to `check_health()`, so this row is mdq's wiring point.

## Assumptions

- Current module verified: `_degraded_response()` at
  `scripts/mcp_servers/mdq/health_check.py:24-28`, `_check_stale_documents()` at `:30-41`,
  `_check_schema_health()` and `_collect_index_stats()` (stats dict returned at `:88-97`),
  `check_health()` at `:100-137`: config load at `:106`, `db_path` default
  `"/opt/llm/db/mdq.sqlite"` at `:107`, `details["database"] = db_path` at `:108`, `allowed_dirs` and
  the `deny_all` detail at `:110-112`, missing-db-file dependency entry at `:115-117`, schema failure
  short-circuit at `:122-127`, final `make_health_response(deps, details)` at `:135-136`.
- MDQ auth is already fail-closed at import: `_load_auth_token()` at
  `scripts/mcp_servers/mdq/mdq_server.py:69-75`, `_AUTH_TOKEN` at `:78`, and the module refuses to
  start with an empty token (`mdq_server.py:445-450`). `config/mdq_mcp_server.toml:8` resolves
  `auth_token` from `MCP_MDQ_AUTH_TOKEN`.
- Existing `/health` body assertions must keep passing: `tests/mcp_servers/mdq/test_mdq_health.py:3`
  documents the `allowed_dirs_count` and `deny_all` fields, and
  `tests/mcp_servers/mdq/test_mdq_health_endpoint.py:325` asserts `"database" in details`.
- Plan `UNK-03`: the precise MDQ check granularity is derived here from `REQ-011` because `memo2.md`
  is unrecoverable. **Needs confirmation**.

## Design decisions

- Add `validate_mdq_security(mdq_cfg, *, db_file_present, schema_error, schema_checked, index_stats)`
  (new module-level function) that takes the config dict `check_health()` already loads at `:106` plus
  the verdicts it already computed, so no second config read, no second database probe, and no new
  import of another server's model is introduced. The verdicts are required keyword arguments rather
  than defaults: a default would let a caller report `OK` for a check that never ran.
- Add `build_mdq_posture()` (new) that runs `run_startup_validation()` (row `04`) with the common stage
  plus these checks. Row `17`'s `validate_posture()` requires every id in `REQUIRED_CHECK_IDS`, which
  includes the three `COMMON_CHECK_IDS`, so a posture built from the `posture_contract` helper alone
  would be rejected as `check_set_mismatch`.
- Add `_mdq_config_view()` (new private) that builds the fingerprint input. It carries presence
  booleans, counts, and scalar limits, never a path or token value, because
  `compute_config_fingerprint()` rejects an absolute path (the same rule row `15` records).
- Check ids (finalized here, Needs confirmation):
  - `server.auth_token_configured` — a missing or empty `auth_token` value is `FAILED` with reason
    `auth_token_missing`. Only presence is tested; the value is never read into a result. This is
    defense-in-depth: `mdq_server.py:445-450` already refuses to start without a token, so the check
    normally reports `OK` and its value is that the posture states the control explicitly.
  - `server.allowed_dirs_configured` — empty `allowed_dirs` is `FAILED` with reason `allowlist_empty`.
    Today the same fact is only a diagnostic flag (`details["deny_all"]` at `:112`), so a deny-all
    mdq-mcp still reports `ready=true`.
  - `server.allowed_dirs_exist` — a configured entry that is not an existing directory is `FAILED`
    with reason `allowed_dir_invalid`, matching the shared file-server rule (row `12`).
  - `server.db_path_valid` — empty `db_path`, or a path that is not an existing file, is `FAILED` with
    reason `db_path_invalid`, mirroring the existing dependency entry at `:115-117`.
  - `server.schema_valid` — the existing `_check_schema_health()` verdict (`:122-127`) maps to
    `FAILED` with reason `dependency_unreachable`; today it only degrades `deps`.
  - `server.index_available` — `fts_row_count == 0` while documents exist is `WARNING` with reason
    `dependency_unreachable`; it is a data-consistency finding, not a policy violation, so it must
    not block Ready. Otherwise `OK`.
- `check_health()` builds the posture from the same values it already reads and passes it to
  `make_health_response()` (row `06`), which adds the `security` key and ANDs `posture.validated`
  into `ready`. `check_health()`'s signature and return type are unchanged, so `mdq_server.py:408-411`
  needs no edit.
- The existing `details` keys (`service`, `database`, `allowed_dirs_count`, `deny_all`, index stats)
  are kept exactly as they are, because tests assert them. **Needs confirmation** as a follow-up:
  `details["database"]` (`:108`) and `deps["db_file"] = f"not found: {db_path}"` (`:116`) already
  publish an absolute path in the health body; this row must not repeat that path inside the posture,
  and whether to redact the existing entries is a separate decision with test impact.

## Alternatives considered

- Add a separate `/health` wiring row for `mdq_server.py` — rejected: its handler is a one-line
  delegation to `check_health()`, so the posture can be published without touching it.
- Validate MDQ from the Agent by reading `mdq_mcp_server.toml` — rejected: that is the cross-config
  read `REQ-017` removes, and `REQ-011` assigns the validation to mdq-mcp.
- Report empty `allowed_dirs` as `WARNING` because mdq-mcp still answers safely in deny-all mode —
  rejected: the Plan's fail-closed-empty-allowlist assumption treats a server that can serve nothing
  as not Ready, and `deny_all` is already visible today without being a readiness failure.
- Fold the posture into `details` — rejected: row `03` rejects it, and `details` shape is asserted by
  existing tests.

## Implementation
### Target file

`scripts/mcp_servers/mdq/health_check.py` (modify) and
`scripts/mcp_servers/mdq/mdq_security_validation.py` (new sibling, Plan row `56` appended by
amendment)

### Procedure

1. Create `scripts/mcp_servers/mdq/mdq_security_validation.py` (Plan row `56`) holding the check ids,
   `_mdq_config_view()`, `configured_allowed_dirs()`, `validate_mdq_security()`, the six private check
   helpers, and `build_mdq_posture()`. The split is the `skills/DESIGN.md` File Split Rule: adding the
   validator in place made `health_check.py` 405 lines with two independent responsibilities.
2. In `health_check.py`, import `MDQ_OWN_CONFIG_FILE`, `configured_allowed_dirs`, and
   `build_mdq_posture` from the sibling, and give `_degraded_response()` a `posture` parameter.
3. Inside `check_health()`, collect the db-file, schema, and index verdicts into local variables
   instead of returning early, call `build_mdq_posture()` after the existing `try` / `except`, and pass
   the posture to `_degraded_response()` and to `make_health_response()`.
4. Keep `_check_stale_documents()`, `_check_schema_health()`, `_collect_index_stats()`, and the
   existing `deps` / `details` keys unchanged.
5. Extend `_mock_config()` in `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` (Plan row `57`) with
   `allowed_dirs` and `auth_token`, because a deny-all or token-less config is now a readiness failure.

### Method

- Fixed check order: `server.auth_token_configured`, `server.allowed_dirs_configured`,
  `server.allowed_dirs_exist`, `server.db_path_valid`, `server.schema_valid`,
  `server.index_available`.
- The validator reuses the verdicts `check_health()` already computes (schema check, db-file check)
  instead of re-deriving them, so one fact has one source and the two channels cannot disagree.
- `check_health()`'s early returns at `:116-117` and `:126-127` are replaced by local verdict variables
  and one response choice at the end, so every path, including the config-failure path, publishes a
  posture. The `deps` keys and their messages are unchanged.
- Messages report counts and state only (`allowed_dirs is empty`, `db file not found`,
  `schema check failed: <schema key>`). The database path and allowed-directory paths are sensitive
  paths under `REQ-002` and are not copied into posture messages.

### Details

- `health_check.py` is 160 lines and `mdq_security_validation.py` is 287 lines. The new test module is
  435 lines: it exceeds 400 but holds one responsibility (MDQ self-validation), so the File Split Rule
  trigger is not met.
- `check_health()` catches `FileNotFoundError, PermissionError, KeyError, TypeError` around the config
  and database work (`:131-132`) and records `deps["config"] = "check failed: {e}"`. The validator
  must be called outside that `try` or its own failures must not be swallowed, otherwise a validation
  error would produce no posture.
- `_degraded_response()` (`:24-28`) is the single place that builds a degraded response; adding the
  posture parameter there covers both early returns and the normal return.
- mdq-mcp reads its own config through `ConfigLoader()` at `:106` while restricted to
  `mdq_mcp_server.toml`, which is the pattern rows `42`-`46` follow for the other servers.

## Compatibility considerations

- `check_health()`'s signature and response shape stay compatible: the `security` key is additive, and
  `tests/mcp_servers/mdq/test_mdq_health*.py` assertions on `allowed_dirs_count`, `deny_all`, and
  `database` keep passing.
- Two tests in `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` asserted a ready response from a
  config with no `allowed_dirs` and no `auth_token`, which is now a readiness failure. Plan row `57` was
  appended by amendment to make that test file a target, and `_mock_config()` now supplies both keys with
  the allowed directory taken from the test tmp directory, so no test depends on a host path.
- Behavior change: mdq-mcp with an empty `allowed_dirs`, an invalid `db_path`, or a failing schema
  check now reports `ready=false` (HTTP 503 through the existing contract). Today those states degrade
  `deps` but can still report `ready=true` when no dependency key is set.
- No `docs/*.md` change is in scope for this row.

## Security considerations

- `REQ-011` / Plan `INV-05`: mdq-mcp validates its own configuration before Ready; the Agent never
  reads `mdq_mcp_server.toml`.
- `REQ-002` / Plan `INV-09`: the auth token value is never read into a result, and paths are reported
  by state only.
- Making deny-all a readiness failure closes a fail-open-shaped gap: a deny-all mdq-mcp currently
  advertises `ready=true` while being unable to serve any document.

## Rollback considerations

- Revert this commit alone; no other row depends on mdq's posture. Row `06`'s optional posture
  parameter means the module keeps working if reverted while row `06` remains.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Empty allowed dirs | `uv run pytest tests/mcp_servers/mdq/test_mdq_security_validation.py` (new test file) | `server.allowed_dirs_configured` `FAILED`, reason `allowlist_empty` |
| Missing or empty auth token | same new test file | `server.auth_token_configured` `FAILED`, reason `auth_token_missing`, and no token value in any message |
| Invalid db path | same new test file | `server.db_path_valid` `FAILED`, reason `db_path_invalid` |
| Schema failure | same new test file | `server.schema_valid` `FAILED`, reason `dependency_unreachable` |
| Empty index is non-fatal | same new test file | `server.index_available` `WARNING` and the posture stays `validated=true` |
| Posture published on `/health` | `uv run pytest tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | body carries the `security` key, and `ready=false` when a check failed |
| Existing MDQ health suite | `uv run pytest tests/mcp_servers/mdq/test_mdq_health.py tests/mcp_servers/mdq/test_mdq_health_stale.py` | passes, `allowed_dirs_count` / `deny_all` / `database` assertions unchanged |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-005` for MDQ: mdq-mcp validates its own configuration and returns the common posture.
- The six finalized check ids are always present, with `NOT_APPLICABLE` used instead of omission.
- mdq-mcp's `/health` body carries the `security` block and `ready` reflects the posture.
- No token value or path appears in any posture field or message.

## Out of scope

- Editing `scripts/mcp_servers/mdq/mdq_server.py` or `mdq_models.py`.
- Redacting the existing `details["database"]` and `deps["db_file"]` path values (recorded as
  Needs-confirmation above).
- Changing `_check_schema_health()` or index-refresh behavior.
- Agent-side validation and classification (rows `17`-`18`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `mdq_security_validation.py` with the validator, config view, and posture builder | Completed | 2026-10-16 | 2026-10-16 | Plan row `56` appended: `health_check.py` reached 405 lines, so the File Split Rule applies |
| 2 | Wire the posture into `check_health()` and `_degraded_response()` | Completed | 2026-10-16 | 2026-10-16 | posture built after the existing `try` / `except`; the early returns became local verdict variables |
| 3 | Add `tests/mcp_servers/mdq/test_mdq_security_validation.py` | Completed | 2026-10-16 | 2026-10-16 | 34 tests; `_mock_config()` in `test_mdq_health_endpoint.py` also updated (Plan row `57`) |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-16 | 2026-10-16 | ruff clean, mypy clean (424 files), lint-imports 6 kept, 387 mdq tests passed, bandit clean, 0 bare except |

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
- **Requirement ID**: `REQ-011` (MDQ self-validation), `REQ-002` (posture published on `/health`)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/mdq/health_check.py`
