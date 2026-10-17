## Goal

Extend the shared `/health` response builder so every MCP server publishes its Security Posture
contract on `/health` alongside the existing readiness fields (`REQ-002`, `AC-002`).

## Scope

- One modified module `scripts/mcp_servers/health_response.py`: add the posture parameter and the
  one new top-level `security` key to the payload built by `make_health_response()`.
- The posture object itself is defined in row `03` (`scripts/shared/security/posture_contract.py`);
  this row only publishes it. Server-side production of the posture belongs to rows `07`-`16`.
- Agent-side consumption of the `security` key belongs to rows `17`-`18`.

## Assumptions

- Current payload is exactly the 7 keys at `scripts/mcp_servers/health_response.py:41-51`
  (`status`, `ready`, `liveness`, `restart_recommended`, `operator_action_required`,
  `dependencies`, `details`), with `ready = len(deps) == 0` at `:38` and status code
  `200`/`503` at `:40`. Verified against current source.
- All 8 servers already route through this one builder (verified consumers:
  `scripts/mcp_servers/cicd/cicd_server.py`, `web_search_server.py`,
  `scripts/mcp_servers/file/common.py:146`, `rag_pipeline/rag_pipeline_server.py`,
  `github_server.py`, `git_server.py`, `scripts/mcp_servers/mdq/health_check.py:136`,
  `shell_server.py`), so one change publishes posture everywhere.
- **Needs confirmation**: the exact `security` block field names come from row `03`, whose shape is
  derived (not recovered) from `REQ-002` because `memo2.md` is unrecoverable (Plan `UNK-01`).
  This row must not invent a second shape.

## Design decisions

- Add one optional third parameter `security: SecurityPosture | None = None` to
  `make_health_response()`. Existing two-argument call sites keep working unchanged.
- The payload gains exactly one new top-level key `security`. All 7 existing keys keep their names,
  types, and semantics; nothing is renamed, removed, or moved into `details`.
- When `security is None` the `security` key is **omitted** rather than emitted as `null`. Omitting
  keeps every existing payload assertion passing (`tests/mcp_servers/mdq/test_mdq_health.py`,
  `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`, `tests/mcp_servers/shell/*`), and lets the
  Agent side distinguish "server not migrated yet" from "server published an invalid posture".
- `ready` becomes `len(deps) == 0 and posture.validated` when a posture is supplied. This is the
  payload-level enforcement of `REQ-003` / Plan `INV-05`: a server whose own security validation
  failed cannot report `ready=true`, and therefore already returns HTTP 503. `WARNING` and
  `NOT_APPLICABLE` checks do not change `validated` (row `03`), so a warning-only posture still
  reports `ready=true` exactly as today.
- `status` follows `ready` as before, so a posture failure surfaces as `degraded` + 503 without a
  new status string. `restart_recommended` stays `False` and `operator_action_required` stays
  `not ready`: a posture failure is a config problem, and restarting the same config cannot fix it.
- The posture is serialized through its own `to_dict()` (row `03`), not by dict-coercion here, so the
  non-secret guarantee (`SecurityCheckResult.__post_init__` calling `assert_non_secret()`, row `02`) is
  the single place that decides what leaves the process.

## Alternatives considered

- Put the posture inside the existing `details` dict — rejected: `details` is a free-form,
  server-specific bag (for example mdq puts `document_count` and `deny_all` there,
  `scripts/mcp_servers/mdq/health_check.py:104-112`), so the Agent validator (row `17`) could not
  assert a stable schema against it. `REQ-012` requires a schema the Agent can validate.
- Add a separate `/security` endpoint — rejected: `REQ-002` states the posture is exposed on
  `/health`, and a second endpoint doubles the probe cost of every startup and adds an ordering
  question (`/health` ready vs `/security` validated) that `REQ-014` does not need.
- Make `security` a required parameter — rejected: it would break all 8 existing call sites in one
  commit and force rows `07`-`16` to land atomically with this row.

## Implementation
### Target file

`scripts/mcp_servers/health_response.py` (modify)

### Procedure

1. Import `SecurityPosture` from `shared.security.posture_contract` (row `03`).
2. Add the `security` parameter to `make_health_response()` (`:25-28`).
3. Compute `ready` from both `deps` and the posture's `validated` flag (`:38`).
4. Build the payload dict (`:41-51`) and add the `security` key only when a posture was passed.
5. Update the module docstring usage example (`:7-14`) to show the posture argument.

### Method

- Keep the function signature keyword-compatible: `make_health_response(deps, details, security)`
  so the current positional calls `make_health_response(deps, {})` remain valid.
- Type the parameter as `SecurityPosture | None`, not `dict[str, object]`. Passing a typed object
  is what makes mypy catch a server that builds a posture with the wrong version field, and it
  keeps `mcp_servers -> shared` legal under `.importlinter:19-28` (`shared-is-leaf` allows it).
- Do not add validation logic here: this module formats a payload. A posture that is internally
  invalid must already have been rejected by `SecurityPosture.__post_init__` (row `03`).

### Details

- The module is 52 lines; the change is roughly 10 lines and keeps it well under the 200-line
  convention.
- `HEALTH_STATUS_OK` / `HEALTH_STATUS_DEGRADED` (`:21-22`) are unchanged; no new status constant is
  introduced, because a posture failure is reported through `ready=false`, not a new status value.
- Servers that have not yet adopted the startup flow (rows `07`-`16` pending) keep calling the
  two-argument form and therefore publish no `security` key. Rows `42`-`46` wire the five servers
  whose `/health` handler lives in their own `*_server.py`. Row `18` must not treat a missing
  `security` key as an Integrity failure until every server row has landed; the ordering is
  recorded in the Execution Status of rows `17`-`18`.
- `scripts/mcp_servers/web_search/web_search_server.py:104-116` calls `make_health_response` in its
  own `/health` handler like the other servers. Plan `UNK-04` is resolved: rows `51`-`52` give
  web_search a validator and wire its posture, so web_search does publish a `security` block. This
  row adds no web_search validation of its own.

## Compatibility considerations

- Additive payload change (Plan Risks section: "Extending `/health` changes the payload consumed by
  existing monitoring"). Existing keys and their values are unchanged for every server that does
  not pass a posture, so monitoring and the existing `/health` tests are unaffected.
- `scripts/agent/services/mcp_health.py:59-67` reads only `restart_recommended`,
  `operator_action_required`, and the whole `body`; it does not enumerate keys, so it keeps working.
- `scripts/agent/startup_reporter.py:103-111` reads `health_registry` states, not the payload, so
  it is unaffected.
- No `docs/*.md` edit is in scope for this row. `docs/22_mcp/*` and
  `docs/23_agent/agent_13_reference-api-generated.md` describe the `/health` payload and are out of
  this Plan's frozen table; they are listed as follow-up in the Plan's Documentation Impact note.

## Security considerations

- `REQ-002` / Plan `INV-09`: the payload must carry no Secret, raw allowlist, sensitive path, or
  config body. Enforcement points are `SecurityCheckResult.__post_init__` / `assert_non_secret()`
  (row `02`) and `SecurityPosture.__post_init__` (row `03`); this module adds no field of its own
  beyond the posture object.
- `REQ-004`: `dependencies` values are already error strings; this row must not copy a posture
  check message into `dependencies`, because check messages are reason-code-bearing and already
  masked by row `02`.
- Publishing posture does not weaken `ConfigLoader.restrict_to(...)`: `/health` is served by the
  server process itself, which is already restricted to its own config file
  (`scripts/mcp_servers/server.py:237-247`).

## Rollback considerations

- Revert this commit only. Because the new parameter is optional and the new key is conditional,
  reverting leaves rows `07`-`16` (which pass a posture) broken, so rollback order matters: revert
  the server rows that pass `security=` before reverting this one, or revert the whole Phase 2
  range. No data or config migration is involved.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Payload compatibility (no posture) | `uv run pytest tests/mcp_servers/mdq/test_mdq_health.py tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | all existing `/health` assertions pass, no `security` key |
| Posture published | `uv run pytest tests/mcp_servers/test_health_response.py` (new test file) | `security` key present with the row `03` field names when a posture is passed |
| Fail-closed ready | same new test file | posture with `validated=False` yields `ready=false`, `status="degraded"`, HTTP 503 |
| Secret non-exposure | same new test file | serialized `security` block contains no allowlist value, path, or token |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean; `mcp_servers-no-agent` and `shared-is-leaf` keep |

## Completion criteria

- Plan `AC-002`: the posture contract is published on `/health` and contains no Secret, raw
  allowlist, sensitive path, or config body.
- All 8 existing `make_health_response()` call sites still import and call it without change.
- A posture with `validated=False` cannot produce `ready=true` from this builder.

## Out of scope

- Producing per-server check results (rows `07`-`16`).
- Agent-side validation, failure classification, and gating (rows `17`-`19`).
- `scripts/mcp_servers/server.py` `/health` default handler (reference file, not modified).
- `docs/22_mcp/*` and `docs/23_agent/agent_13_reference-api-generated.md` payload descriptions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `health_response.py` change per Procedure/Method/Details | Completed | 20261016-190507 | 20261016-190507 | depends on row 03 field names. stale gate: the only finding was symbol_missing for Risks, which is a Plan section name and not a symbol, so the backticks around it were removed from the doc instead of adding a (new) marker; the detector then exits 0. Amended the Details bullet that called web_search a make_health_response consumer with no self-validation row: Plan UNK-04 is resolved and rows 51-52 give web_search a validator and posture wiring, so it does publish a security block. Contract finalized: make_health_response(deps, details=None, security typed as SecurityPosture or None); ready = len(deps) == 0 and (security is None or security.validated); the security key is set to security.to_dict() only when a posture is passed; no new status constant, a posture failure is reported through ready=false. Module is 57 lines |
| 2 | Add `tests/mcp_servers/test_health_response.py` per Validation plan | Completed | 20261016-190507 | 20261016-190507 | tests/mcp_servers/test_health_response.py: 10 tests, all pass; covers the unchanged 7-key payload without a posture, the unchanged two-argument call form, the security block carrying the row 03 field names and equal to posture.to_dict(), a validated=False posture yielding ready=false / degraded / 503 with restart_recommended still false, a validated posture not hiding a dependency failure, and no path or token in the serialized block; the existing mdq /health tests pass unchanged (32 passed, 1 skipped) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-190507 | 20261016-190507 | ruff clean; mypy 421 files clean; lint-imports 6 kept (shared-is-leaf and mcp_servers-no-agent hold with the new mcp_servers to shared import); bandit reports no issue in health_response.py; bare-except constraint 0 hits; check_docstrings.py reports no finding in health_response.py; all 8 existing make_health_response call sites are unchanged; full suite 8605 passed, 19 skipped, 9 pre-existing failures in tests/agent/test_startup_rollback.py; N/A: the doc states no docs/00_index.md task-scope mapping applies to this row |

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
- **Requirement ID**: `REQ-002` (posture contract published on `/health`, non-secret)
- **Source issue**: `issues/done/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/health_response.py`
