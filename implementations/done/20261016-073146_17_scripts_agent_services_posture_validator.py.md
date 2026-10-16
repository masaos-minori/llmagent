## Goal

Add the Agent-side validator that checks a published Security Posture against the common contract, so
the Agent validates the contract instead of reading each server's configuration (`REQ-012`,
`AC-006`).

## Scope

- One new module `scripts/agent/services/posture_validator.py`: parse the `security` block from a
  server's `/health` body, validate it against the contract (schema, contract version, server key,
  required check set, fingerprint shape, ready/validated consistency), and return a structured result
  the classification layer (row `18`) can consume.
- No probing and no classification here: probing stays in `scripts/agent/services/mcp_health.py`
  (row `18`) and `scripts/agent/services/mcp_status.py`, classification is row `18`.

## Assumptions

- The posture shape and vocabulary are defined by rows `02` and `03`: `SecurityCheckResult` /
  `SecurityCheckStatus` / reason codes in `scripts/shared/security/result_dto.py`, and
  `SecurityPosture` / `SECURITY_CONTRACT_VERSION` / `REQUIRED_CHECK_IDS` in
  `scripts/shared/security/posture_contract.py`.
- The Agent already holds the server keys and endpoints without reading server configs:
  `ctx.cfg.mcp.mcp_servers` is used for the `mcp_auth` check at
  `scripts/agent/startup_validation.py:70-81`, and `scripts/agent/services/mcp_status.py:82-162`
  probes each server's `/health` and keeps the raw body in `McpProbeResult.body` (`:121`, `:156`).
- `_probe_mcp_health_detail()` (`scripts/agent/services/mcp_health.py:24-67`) never raises and returns
  `body={}` on network failure (`:40-46`) or `parse_failed=True` on a JSON parse failure (`:50-58`).
- Import contract: `agent -> shared` is allowed, `agent -> mcp_servers` is not, and the only existing
  exception is the `agent-mcp-config-models` grant at `.importlinter:68-82` that row `25` removes. This
  module must therefore import only `shared.*` and `agent.*`.
- **Needs confirmation**: the exact posture JSON key names are finalized in row `03` (Plan `UNK-01`);
  this document uses the row `03` names.

## Design decisions

- `PostureValidationResult` (new frozen dataclass) with fields `server_key`, `accepted`,
  `reason_code`, `message`, `posture`. `accepted=False` always carries a reason code from the
  Agent-side codes added in row `02`: `posture_missing`, `contract_version_mismatch`,
  `check_set_mismatch`, `fingerprint_mismatch`, `server_key_mismatch`, `config_invalid`.
- `parse_posture(body: Mapping[str, object], server_key: str) -> PostureValidationResult` (new):
  reads `body["security"]`, requires the contract keys, and constructs `SecurityPosture` (row `03`).
  A body without the key returns `accepted=False` with `posture_missing`.
- `validate_posture(posture, *, expected_server_key: str) -> PostureValidationResult` (new): the
  contract checks, in fixed order:
  1. `posture.server_key == expected_server_key` — otherwise `server_key_mismatch`. This is the
     identity check `REQ-012` names: a server answering for a key other than the one the Agent asked
     about is rejected rather than trusted.
  2. `posture.contract_version == SECURITY_CONTRACT_VERSION` — otherwise `contract_version_mismatch`.
     Equality only, no prefix or range matching (row `03`).
  3. every id in `REQUIRED_CHECK_IDS` (row `03`) is present in `posture.checks` — otherwise
     `check_set_mismatch`. Missing checks are never treated as passing.
  4. `posture.fingerprint` matches the 64-character lowercase hex shape — otherwise
     `config_invalid`.
  5. `posture.ready` and `posture.validated` are consistent: `ready=true` with `validated=false` is
     `config_invalid`, because row `06` makes `ready` AND `validated` into the payload rule.
- A server key with no entry in `REQUIRED_CHECK_IDS` is rejected with `check_set_mismatch`: the Agent
  cannot validate a posture against a contract it does not hold, and accepting it would let an
  unregistered server reach the registry.
- `parse_posture()` reports a parse failure as `config_invalid` with a message it wrote itself. The
  `ValueError` text from `SecurityPosture.from_dict()` quotes the server-supplied key or status
  string, so it is not carried into the result.
- `compare_fingerprint(server_key: str, posture: SecurityPosture) -> PostureValidationResult` (new)
  keeps a process-local last-seen fingerprint per server key so a config change between two Agent
  startups is detectable as `fingerprint_mismatch`. The Agent never recomputes a fingerprint from
  server config: that would require reading `*_mcp_server.toml`, which `REQ-017` removes. The
  fingerprint is therefore a drift and shadow-comparison signal, not an Agent-verifiable proof. The
  return type is the same verdict object as the other two functions rather than `bool`: the first
  posture seen for a key is accepted, and a drift has to carry `fingerprint_mismatch` for row `18` to
  classify it, which is the same reason rejecting a `bool` return is recorded above.
- No `REQUIRED_SERVER_KEYS` constant is introduced here: the set of servers to validate comes from
  `ctx.cfg.mcp.mcp_servers` in row `18`, so a server added to `agent.toml` is validated without a code
  change in this module. `web_search` is covered: rows `51` and `52` were added 2026-10-16 resolving
  Plan `UNK-04`, so a missing `web_search` posture is a `posture_missing` rejection like any other
  HTTP server's.

## Alternatives considered

- Have the Agent compute each server's fingerprint from its own view of the server config — rejected:
  it is exactly the cross-config read `REQ-017` removes and would re-create the
  `agent-mcp-config-models` exception row `25` deletes.
- Return `bool` from the validator — rejected: `REQ-013` requires distinguishing Availability failures
  from Safety/Integrity failures, so the reason code must travel with the result.
- Validate the posture inside `mcp_status.py`'s probe interpretation
  (`scripts/agent/services/mcp_status.py:82-162`) — rejected: that path is the status/observability
  view and already has its own reason derivation (`:115-119`); putting contract validation there
  would make two places decide whether a posture is acceptable.
- Accept unknown extra keys in the posture body — accepted for forward compatibility, but unknown keys
  are ignored rather than stored, so a newer server cannot smuggle fields into Agent decisions.

## Implementation
### Target file

`scripts/agent/services/posture_validator.py` (new)

### Procedure

1. Create the module with a docstring in the repository style (`scripts/agent/services/*.py` header
   convention) and `from __future__ import annotations`.
2. Import `SecurityPosture`, `SECURITY_CONTRACT_VERSION`, `REQUIRED_CHECK_IDS` from
   `shared.security.posture_contract` (row `03`) and `SecurityCheckResult`, `SecurityCheckStatus`, and
   the reason-code constants from `shared.security.result_dto` (row `02`).
3. Define `PostureValidationResult`, `parse_posture()`, `validate_posture()`, `compare_fingerprint()`.
4. Do not import `httpx`, `agent.context`, or anything under `mcp_servers`.

### Method

- The module is pure and synchronous: no I/O, no async, no logging of posture contents. Callers own
  probing and logging, which keeps the validator testable with plain dicts.
- Every rejection path returns a `PostureValidationResult` with `accepted=False`, a reason code, and a
  message that names the mismatch and the expected value kind (`contract version`, `server key`) but
  never echoes a fingerprint value or a check message from the server.
- `parse_posture()` constructs `SecurityCheckResult` objects through the row `02` DTO, so a malformed
  check raises `ValueError` inside `parse_posture()` and is converted to `accepted=False` with
  `config_invalid` rather than propagating.
- `compare_fingerprint()` stores `{server_key: fingerprint}` in a module-level dict guarded by a
  `threading.Lock`, and exposes `reset_fingerprint_state()` (new) for tests, following the existing
  `ConfigLoader._reset_for_testing()` convention (`tests/conftest.py:37-46`).

### Details

- The module is 213 lines, above the 150-line target this document set: the fixed check order needs
  one rejection per violation, and the messages are written here rather than carried from the server.
  It is still one responsibility and well under the 400-line split trigger. The module has no
  configuration and no environment reads.
- The last-seen fingerprint map is process-local by design: it detects drift within one Agent
  process's lifetime and across restarts only if the Agent persists it, which is out of scope.
- `SecurityCheckStatus` values are compared by enum identity after parsing, so a server sending an
  unknown status string fails at parse time.

## Compatibility considerations

- New module; nothing imports it until rows `18` and `26`-`35` land, so no existing behavior changes.
- `tools/stale_detector.py` reports `new_target_exists` for this document once the module exists. That
  is the expected state of a row that creates its own target file, the same finding rows `03` and `04`
  carry in `implementations/done/`.
- `scripts/agent/repl_health.py` is excluded from coverage (`pyproject.toml:153`) but this module is
  not, so the new tests must reach the repository's diff-coverage threshold.
- No `docs/*.md` change is in scope for this row; `docs/23_agent/agent_13_reference-api-generated.md`
  is regenerated by `tools/generate_reference_table.py` as a follow-up.

## Security considerations

- `REQ-012` / Plan `INV-06`: the Agent validates the posture contract and never reads MCP server
  config files, so the `agent-mcp-config-models` exception can be removed (row `25`).
- Fail-closed by construction: a missing, malformed, version-mismatched, key-mismatched, or
  check-incomplete posture is `accepted=False`, and row `18` classifies those as Safety/Integrity
  failures.
- Fingerprint values and server-supplied messages are never logged or echoed, so a hostile or broken
  server cannot use the posture as a channel to inject text into Agent logs.

## Rollback considerations

- Delete the module and revert row `18`, which is its only consumer. No config or data migration is
  involved.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Missing posture | `uv run pytest tests/agent/services/test_posture_validator.py` (new test file) | `accepted=False`, reason `posture_missing` |
| Contract version mismatch | same new test file | `accepted=False`, reason `contract_version_mismatch` |
| Server key mismatch | same new test file | `accepted=False`, reason `server_key_mismatch` |
| Missing required check | same new test file | `accepted=False`, reason `check_set_mismatch` |
| Bad fingerprint shape | same new test file | `accepted=False`, reason `config_invalid` |
| ready/validated inconsistency | same new test file | `accepted=False`, reason `config_invalid` |
| Fingerprint drift | same new test file | second call with a different fingerprint reports `fingerprint_mismatch` |
| Malformed check entry | same new test file | the DTO `ValueError` is converted to `accepted=False`, never raised |
| Import contract | `PYTHONPATH=scripts uv run lint-imports` | no `agent -> mcp_servers` import introduced |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/` | clean |

## Completion criteria

- Plan `AC-006`: a posture that violates the contract is rejected with a machine-readable reason code,
  and a conforming posture is accepted.
- The module performs no I/O and imports nothing under `mcp_servers`.
- Every rejection path names a reason code from the shared vocabulary.

## Out of scope

- Probing servers and classifying failures (row `18`), and registry gating (row `19`).
- Persisting fingerprints across Agent restarts.
- Adding the `web_search` self-validation rows (`51`, `52`) — resolved 2026-10-16 (Plan `UNK-04`).
- `docs/*.md` updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `posture_validator.py` per Procedure/Method/Details | Completed | 2026-10-16 | 2026-10-16 | 213 lines, imports only `shared.security` and the standard library |
| 2 | Add `tests/agent/services/test_posture_validator.py` | Completed | 2026-10-16 | 2026-10-16 | 30 tests, all passing |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-16 | 2026-10-16 | ruff clean, mypy clean (425 files), lint-imports 6 kept, bandit clean, 0 bare except, no mock-patch findings |

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
- **Requirement ID**: `REQ-012` (Agent validates the posture contract)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/agent/services/posture_validator.py`
