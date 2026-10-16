## Goal

Implement the single Security Validation result DTO that every MCP server returns from its
self-validation and that the Agent consumes (`REQ-001`: check ID, check status, reason code,
security policy version, posture-contract version, ready state, non-secret config fingerprint).

## Scope

- One new module `scripts/shared/security/result_dto.py`: the DTO, its status enum, and the
  reason-code vocabulary.
- No server-side or Agent-side call sites; those are rows `06`-`19`.

## Assumptions

- The exact reason-code enumeration was defined in `memo2.md`, which is no longer recoverable
  (see the Plan's `Assumptions`). The vocabulary below is derived from the Plan's `REQ-001` and
  `REQ-005`..`REQ-011` check descriptions.
- **Needs confirmation**: the reason-code strings and the `policy_version` / `contract_version`
  literal values are finalized at implementation; confirm them against the Plan's `REQ-001`
  wording before the first server row (rows `07`-`16`) consumes them.

## Design decisions

- `SecurityCheckStatus` (new) is a four-value enum: `OK`, `WARNING`, `FAILED`, `NOT_APPLICABLE`.
  `NOT_APPLICABLE` is required by the Plan's Design section ("a common check is expressed as
  `not_applicable` or a dedicated check ID rather than silently skipped") so an ADR-carried
  exception stays visible in the posture. `WARNING` (new) carries a finding the retired Agent
  audit reported as a warning — for example `github.allow_force_push=true`
  (`scripts/agent/services/security_audit.py:205-212`) — without flipping the posture's
  `validated` flag, so a server that starts today with a warning still starts after migration.
  Only `FAILED` blocks Ready.
- `SecurityCheckResult` (new) is a frozen dataclass with fields `check_id`, `status`,
  `reason_code`, `message`, `policy_version`, `contract_version`, `ready`, `fingerprint`.
  Frozen because the posture is produced once at startup and then read by the Agent; mutability
  would let a server mutate a published posture after the fact.
- `message` is a human-readable, non-secret summary; the machine-readable decision is carried by
  `reason_code`, so consumers must not parse `message`.
- Reason codes are a module-level `frozenset[str]` named `SECURITY_REASON_CODES` (new) plus one
  module-level constant per code, so a typo fails at import rather than at comparison time.
  Initial set: `ok`, `config_missing`, `config_invalid`, `allowlist_empty`, `allowlist_invalid`,
  `path_out_of_boundary`, `symlink_escape`, `sandbox_backend_missing`,
  `sandbox_backend_unsupported`, `auth_token_missing`, `protected_branch_violation`,
  `force_push_enabled`, `wildcard_range_invalid`, `destructive_guard_missing`,
  `delete_limit_invalid`, `atomic_write_disabled`, `db_path_invalid`, `index_path_invalid`,
  `allowed_dir_invalid`, `dependency_unreachable`, `not_applicable`.
  The set also carries the five codes the Agent-side posture validator (row `17`) emits when a
  published posture is unusable: `posture_missing`, `contract_version_mismatch`,
  `check_set_mismatch`, `fingerprint_mismatch`, `server_key_mismatch`. They live in the same
  vocabulary so the Agent and the servers share one machine-readable namespace.

## Alternatives considered

- Return plain `list[str]` warning messages like the retired `audit_security_defaults`
  (`scripts/agent/services/security_audit.py:40`) — rejected: it carries no check identity, no
  status, and no version, so the Agent cannot classify Safety/Integrity vs Availability
  (`REQ-013`).
- Pydantic model — rejected for the shared leaf layer: the DTO is consumed by both the Agent and
  every server process, and a stdlib frozen dataclass keeps `shared` free of a validation
  dependency and keeps the contract serializable through `to_dict()` for `/health`.

## Implementation
### Target file

`scripts/shared/security/result_dto.py` (new)

### Procedure

1. Define `SecurityCheckStatus` (new) as a `StrEnum`.
2. Define the reason-code constants and `SECURITY_REASON_CODES` (new).
3. Define `SecurityCheckResult` (new) as a frozen dataclass with the eight `REQ-001` fields.
4. Add `SecurityCheckResult.to_dict()` (new) returning the JSON-safe form used by `/health`
   (row `06`), and `SecurityCheckResult.from_dict()` (new) used by the Agent validator (row `17`).
5. Add a module-level `assert_non_secret()` (new) helper that rejects a value containing a raw
   token, an absolute path, or a config body, and call it from `__post_init__`.

### Method

- `__post_init__` validation raises `ValueError` on: an unknown `reason_code`, an empty
  `check_id`, `status == OK` combined with a reason code other than `ok`, `status == WARNING`
  combined with reason code `ok` (a warning must name why it warns), or a `message` that fails
  `assert_non_secret()`. Fail-closed at construction, not at consumption.
- `to_dict()` emits keys `id`, `status`, `reason_code`, `message`; the version/ready/fingerprint
  fields are emitted once at the posture level (row `03`), not repeated per check.

### Details

- `fingerprint` is a 64-character lowercase hex sha256 string; this module only stores and
  validates its shape (`_FINGERPRINT_RE` (new)), it does not compute it. Computation belongs to
  `scripts/shared/security/posture_contract.py` (row `03`).
- `policy_version` and `contract_version` are short dotted strings (for example `"1"`); the
  literal starting value is Needs-confirmation above.
- Keep the module under 120 lines and free of any `agent` or `mcp_servers` import.

## Compatibility considerations

- New module; nothing imports it yet. The first consumers are `posture_contract.py` (row `03`)
  and `scripts/mcp_servers/health_response.py` (row `06`).
- `to_dict()` output must stay additive: existing `/health` consumers read `status`, `ready`,
  `liveness`, `restart_recommended`, `operator_action_required`, `dependencies`, `details`
  (`scripts/mcp_servers/health_response.py:41-51`).

## Security considerations

- `REQ-002` / `REQ-004`: the DTO must never carry a Secret, a raw allowlist value, a sensitive
  path, or a config body. `assert_non_secret()` in `__post_init__` is the enforcement point, and
  it must not echo the offending value into the raised exception message.
- Existing secret masking (`scripts/agent/secrets_masker.py`) stays in force for logs; this DTO
  is the transport, not a log line.

## Rollback considerations

- Revert the commit. No consumer exists until rows `03` and `06` land, so rollback is a clean
  file deletion.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| DTO round-trip | `uv run pytest tests/shared/test_security_result_dto.py -v` (new test file) | `from_dict(to_dict(x)) == x` for every status |
| Reason-code closure | same test file | every emitted code is in `SECURITY_REASON_CODES`; an unknown code raises `ValueError` |
| Secret non-exposure | same test file | constructing a result with a token-like or absolute-path value raises `ValueError` and the message is not echoed |
| WARNING is non-fatal | same test file | `status == WARNING` round-trips, requires a reason code other than `ok`, and `status == OK` with a non-`ok` reason code raises `ValueError` |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean; `shared-is-leaf` keeps |

## Completion criteria

- `REQ-001` fields are all present on the DTO and are the only type a server returns and the
  Agent consumes (Plan `AC-001`).
- Every reason code a server can emit is enumerated in the module.
- A DTO holding a secret cannot be constructed.

## Out of scope

- Fingerprint computation and the posture envelope (row `03`).
- Server-side check implementations (rows `07`-`16`).
- The Agent-side validator (row `17`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `result_dto.py` per Procedure/Method/Details | Pending | — | — | reason-code vocabulary Needs-confirmation |
| 2 | Add `tests/shared/test_security_result_dto.py` per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (common Security Validation result DTO)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/shared/security/result_dto.py`
