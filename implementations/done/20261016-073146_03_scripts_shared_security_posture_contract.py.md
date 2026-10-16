## Goal

Implement the Security Posture contract: the versioned, non-secret envelope a server publishes on
`/health` and the Agent validates (`REQ-002`: server key, policy version, check results,
non-secret config fingerprint; never Secret, raw allowlist, sensitive path, or config body).

## Scope

- One new module `scripts/shared/security/posture_contract.py`: the posture envelope, the
  fingerprint helper, the contract version constant, and the per-server required-check-id list.
- Publishing the posture on `/health` is row `06`; validating it on the Agent side is row `17`.

## Assumptions

- The exact JSON field names were defined in `memo2.md`, which is no longer recoverable (Plan
  `Assumptions`, `UNK-01`). The shape below is derived from `REQ-001`/`REQ-002` and from the
  existing `/health` payload (`scripts/mcp_servers/health_response.py:41-51`).
- **Needs confirmation**: the `security` block field names and the initial
  `SECURITY_CONTRACT_VERSION` (new) value are finalized here and must be confirmed before row `06`
  publishes them to monitoring.

## Design decisions

- `SecurityPosture` (new) is a frozen dataclass: `contract_version`, `server_key`,
  `policy_version`, `validated`, `ready`, `fingerprint`, `checks` (a tuple of
  `SecurityCheckResult` from row `02`).
- Posture is added to `/health` as one new top-level `security` key, leaving `status`, `ready`,
  `liveness`, `restart_recommended`, `operator_action_required`, `dependencies`, and `details`
  untouched. Liveness, Readiness, and Security Posture stay distinct concepts (`REQ-002`).
- `compute_config_fingerprint()` (new) hashes a caller-supplied normalized mapping:
  sha256 over the UTF-8 encoding of a canonical JSON dump (`sort_keys=True`,
  `separators=(",", ":")`, `ensure_ascii=False`) of only non-secret scalar values. The shared
  module never reads a config file — each server builds its own normalized view, which keeps
  `shared` a leaf (`shared-is-leaf`, `.importlinter:19-28`).
- `REQUIRED_CHECK_IDS` (new) maps a server key to the tuple of check ids that must appear in its
  posture. It lives in the shared contract so the Agent can assert "required checks present"
  (`REQ-012`) without importing any MCP config model (`REQ-022`).
- `SECURITY_CONTRACT_VERSION` (new) is a module constant string; a server reports it verbatim and
  the Agent compares it for equality, not prefix-matching.
- `validated` is derived from check statuses: it is `false` when any check has status `FAILED`,
  and stays `true` when the only non-`OK` statuses are `WARNING` or `NOT_APPLICABLE`. This keeps
  the old audit's warning-only findings (for example `github.allow_force_push=true`) from becoming
  startup aborts, while `REQ-013` still treats `validated=false` as a Safety/Integrity failure.

## Alternatives considered

- Fold posture into the existing `details` dict — rejected: `details` is free-form per-server
  diagnostic space, so a schema-validated contract placed there cannot be validated without
  server-specific knowledge.
- Have the Agent compute the fingerprint from its own view of server config — rejected: it
  requires reading `*_mcp_server.toml`, which is exactly the cross-config read `REQ-017` removes.

## Implementation
### Target file

`scripts/shared/security/posture_contract.py` (new)

### Procedure

1. Define `SECURITY_CONTRACT_VERSION` (new) and `POSTURE_STATUS_OK` (new).
2. Define `SecurityPosture` (new) with the seven fields above and `__post_init__` validation.
3. Define `compute_config_fingerprint()` (new).
4. Define `SecurityPosture.to_dict()` (new) / `from_dict()` (new) for the `/health` `security`
   block.
5. Define `REQUIRED_CHECK_IDS` (new) covering `shell`, `git`, `github`, `cicd`, `file_read`,
   `file_write`, `file_delete`, `rag_pipeline`, `mdq`, and `web_search` (rows `51`-`52`, added 2026-10-16
   resolving Plan `UNK-04`).

### Method

- `__post_init__` raises `ValueError` when: `contract_version` or `server_key` is empty,
  `validated` is true while any check has status `FAILED`, `fingerprint` does not match the
  64-hex shape validated by row `02`, or `checks` is empty.
- `to_dict()` emits `{"contract_version", "server_key", "policy_version", "validated", "ready",
  "fingerprint", "checks": [...]}` where each check entry is the row `02` `to_dict()` output.
- `compute_config_fingerprint()` rejects a mapping whose value is a `Mapping`, `list`, `set`, or
  `tuple` of more than a fixed small size, because collection values are where allowlists and
  paths appear; only scalars and short scalar tuples are hashed, and a scalar string longer than
  120 characters is rejected as a probable config body.

### Details

- The normalized view each server builds is defined by that server's own row (`07`-`16`); this
  module only defines the hashing and the rejection rules.
- `server_key` values must match the keys the Agent already uses for MCP servers
  (`ctx.cfg.mcp.mcp_servers` keys, see `scripts/agent/startup_validation.py:71-73`) so identity
  comparison in row `17` is a string equality test.
- Keep the module under 160 lines.

## Compatibility considerations

- New module; the first consumers are `scripts/mcp_servers/health_response.py` (row `06`) and
  `scripts/agent/services/posture_validator.py` (row `17`).
- Adding a top-level `security` key is additive for existing `/health` readers
  (`scripts/agent/services/mcp_health.py:24` `_probe_mcp_health_detail` reads specific keys, not
  the whole body).

## Security considerations

- `REQ-002` / Plan `INV-09`: the posture contains no Secret, raw allowlist, sensitive path, or
  config body. Enforcement points are the scalar-only fingerprint input and `__post_init__`.
- `REQ-004`: a validation failure must not echo the offending config value into the exception
  text; raise with the field name and reason code only.

## Rollback considerations

- Revert the commit. Rows `06` and `17` are the only consumers and land after this row.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Envelope round-trip | `uv run pytest tests/shared/test_security_posture_contract.py -v` (new test file) | `from_dict(to_dict(p)) == p` |
| Secret non-exposure | same test file | a posture built from a mapping containing a token, an absolute path, or a long string raises `ValueError` |
| Required-check closure | same test file | every id in `REQUIRED_CHECK_IDS` (new) is a check id some server row can emit |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean; `shared-is-leaf` keeps |

## Completion criteria

- Plan `AC-002`: the contract carries no Secret, raw allowlist, sensitive path, or config body, and
  is publishable on `/health`.
- Fingerprint is deterministic: the same normalized mapping always yields the same digest, and a
  changed non-secret value always changes it.

## Out of scope

- Building each server's normalized config view (rows `07`-`16`).
- Extending the `/health` builder (row `06`).
- Agent-side validation and failure classification (rows `17`-`18`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `posture_contract.py` per Procedure/Method/Details | Completed | — | 20261016-175140 | JSON field names Needs-confirmation stale gate clean after marking 2 unmarked (new) names. Shape finalized: security block = 7 keys (contract_version, server_key, policy_version, validated, ready, fingerprint, checks); SECURITY_CONTRACT_VERSION aliases result_dto.DEFAULT_CONTRACT_VERSION = '1' so check and posture cannot drift. REQUIRED_CHECK_IDS encodes the check ids finalized by rows 07-16/51-52 plus three common ids named here: common.own_config_only, common.auth_token, common.published_tools (row 04 must emit exactly these). Module is 246 lines, over the 160-line guideline, because 51 check ids across 10 servers are enumerated; DESIGN.md split trigger (400 lines) not met. POSTURE_STATUS_OK has no consumer yet (procedure step 1 requires it); validated is the authority |
| 2 | Add `tests/shared/test_security_posture_contract.py` per Validation plan | Completed | 20261016-175140 | 20261016-175140 | tests/shared/test_security_posture_contract.py: 60 tests, all pass; required-check table mirrored in the test so a change to it is an explicit decision |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-175140 | 20261016-175140 | ruff clean; mypy 419 files clean; lint-imports 6 kept (shared-is-leaf holds); bandit delta +1 Low B105 on CHECK_ID_AUTH_TOKEN (pre-existing pattern), no new medium/high; bare-except constraint 0 hits via ast-grep-py (ast-grep CLI not installed); check_docstrings.py reports 294 pre-existing findings, none in scripts/shared/security/; full suite 8548 passed, 19 skipped, 9 pre-existing failures in tests/agent/test_startup_rollback.py; N/A: no docs/00_index.md task-scope mapping for scripts/shared/security/posture_contract.py |

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
- **Requirement ID**: `REQ-002` (versioned, non-secret Security Posture contract)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/shared/security/posture_contract.py`