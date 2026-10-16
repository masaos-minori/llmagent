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

- Add `validate_mdq_security(cfg: Mapping[str, object]) -> list[SecurityCheckResult]` (new module-level
  function) that takes the config dict `check_health()` already loads at `:106`, so no second config
  read and no new import of another server's model is introduced.
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

`scripts/mcp_servers/mdq/health_check.py` (modify)

### Procedure

1. Import `SecurityCheckResult`, `SecurityCheckStatus`, and the reason-code constants from
   `shared.security.result_dto` (row `02`), and `SecurityPosture` plus the posture-building helper
   from `shared.security.posture_contract` (row `03`).
2. Add `validate_mdq_security()` (new) before `check_health()` (`:100`).
3. Inside `check_health()`, call `validate_mdq_security(mdq_cfg)` and pass the resulting posture to
   `make_health_response()` at `:135-136` and to `_degraded_response()` at `:24-28`.
4. Keep `_check_stale_documents()`, `_check_schema_health()`, `_collect_index_stats()`, and the
   existing `deps` / `details` keys unchanged.

### Method

- Fixed check order: `server.auth_token_configured`, `server.allowed_dirs_configured`,
  `server.allowed_dirs_exist`, `server.db_path_valid`, `server.schema_valid`,
  `server.index_available`.
- The validator reuses the verdicts `check_health()` already computes (schema check, db-file check)
  instead of re-deriving them, so one fact has one source and the two channels cannot disagree.
- `check_health()`'s early return at `:116-117` and `:126-127` must still attach the posture, so the
  posture is built before those returns.
- Messages report counts and state only (`allowed_dirs is empty`, `db file not found`,
  `schema check failed: <schema key>`). The database path and allowed-directory paths are sensitive
  paths under `REQ-002` and are not copied into posture messages.

### Details

- The module is about 137 lines; the addition is roughly 50 lines.
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
| 1 | Implement `validate_mdq_security()` | Pending | — | — | check ids are Needs-confirmation (Plan `UNK-03`) |
| 2 | Wire the posture into `check_health()` and `_degraded_response()` | Pending | — | — | depends on row `06` signature |
| 3 | Add `tests/mcp_servers/mdq/test_mdq_security_validation.py` | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
