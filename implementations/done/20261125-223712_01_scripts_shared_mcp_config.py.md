## Goal

Enforce the server-identifier rule, remove the `fields` Popen-kwargs field, and add the declared `credential_env` (new) field in the MCP configuration model (REQ-005 identifier rule, REQ-002 `fields` removal, REQ-006 declared credential variables).

## Scope
**Release unit**: R1-launch-spec

## Assumptions

- cliplc005 is already implemented: `_MCP_SERVER_KEYS` (`scripts/shared/mcp_config.py:37-53`) and the `reject_unknown_keys` call (`:368`) are in the current source, so this edit extends an existing declared key set (Plan Assumptions, UNK-01 resolved).
- `key` is declared with `compare=False, repr=False` (`:111-113`); the new `credential_env` (new) participates in dataclass equality the way `env` does, which is the intended restart-required behavior (Plan Risks).
- An empty `key` stays accepted: the dataclass default is `""` and direct construction in tests relies on it. Only a non-empty, non-matching key is rejected (REQ-005).

## Design decisions

- One shared validator: `validate_server_key` (new) plus a module-level compiled `_SERVER_KEY_RE` (new) for `^[a-z0-9][a-z0-9_-]{0,63}$`, so the config layer and the agent-layer log manager enforce the identical rule instead of duplicating a pattern (REQ-005).
- `credential_env` (new) is a `tuple[str, ...]` defaulting to empty: immutable, and read through the existing strict primitives so a wrong-typed or absent value behaves like every other MCP key (REQ-006).
- `fields` is deleted outright rather than filtered: REQ-002 forbids any configuration value reaching `shell`, `env`, `stdout`, `stderr`, `start_new_session`, or `preexec_fn`, and no `cwd` support is wanted.

## Alternatives considered

Keeping `fields` with a denylist of rejected Popen keywords was rejected: it leaves a config-reachable escape hatch and cannot express "no override at all" (REQ-002, AC-2). A per-server credential enum was rejected: the variable set is deployment-declared, not a fixed vocabulary.

## Implementation
### Target file
`scripts/shared/mcp_config.py`
### Procedure
Add the identifier validator and enforce it at both config entry points, delete the `fields` field, and add `credential_env` (new) to the declared key set, the dataclass, and the parser.

### Method
- Add `_SERVER_KEY_RE` (new) and `validate_server_key` (new) at module level: return the key unchanged, or raise `ValueError` naming the section and the field, never the value.
- Enforce it in `McpServerConfig` validation (extend `_validate_cross_fields` at `:156`, or add a `_validate_key` (new) called from the same place) for a non-empty `key`.
- Enforce it in `_build_mcp_servers` (`:273-281`) on every TOML section name before `_build_single_server` is called.
- Delete the `fields` field (`:108-110`) and the sentence in the comment above `_MCP_SERVER_KEYS` (`:35-36`) that names it.
- Add `credential_env` (new) to `_MCP_SERVER_KEYS` (`:37-53`), to the dataclass as `credential_env: tuple[str, ...] = field(default_factory=tuple)`, and to the `_build_single_server` constructor call (`:388-406`).

### Details
- Read `credential_env` (new) in `_build_single_server` (`:353-407`) through the strict primitives used by the sibling keys, so a present-but-wrong-typed value is rejected and an absent key takes the default.
- Reject any `credential_env` (new) entry that contains a glob metacharacter (`*`, `?`, `[`), whitespace, or `=`, and any entry in `_ENV_KEY_DENYLIST`: the list names variables, not patterns (REQ-006).
- Keep the existing message convention: messages name `mcp_servers.{key}` and the field and never the value, because `auth_token` and `env` carry credentials.

## Compatibility considerations

`McpServerConfig(fields=...)` becomes a `TypeError`. The only construction that passes it is `tests/agent/test_http_lifecycle.py:299` (row 10), and the only reader of `.fields` is `scripts/agent/http_lifecycle_subprocess_launcher.py:102-103` (row 4); the consumer scan found no other reader (Plan Design). `credential_env` (new) is additive and defaulted, so the 19 importing modules are source-compatible.

Verification finding (Step 3a, 20261126): the `render_config_payload` docstring at `scripts/agent/config_builders.py:249` names `McpServerConfig.fields` and becomes stale prose once the field is removed. That file is a Plan `Reference Files` row (MUST NOT be modified), so the fix is out of this batch's scope; report it as a follow-up item.

## Security considerations

The identifier rule is what stops a TOML section name from becoming a path component or terminal text (REQ-005, AC-4). `credential_env` (new) values are variable names only; the launch audit records names, never values (REQ-007).

## Rollback considerations

Revert the commit. The change is only safe as part of R1-launch-spec: rows 4 and 10 remove the `fields` reader and the test that pins it in the same unit.

## Validation plan

- `uv run pytest tests/shared/test_mcp_config_validation.py tests/shared/test_mcp_config.py`
- `uv run mypy scripts/shared/mcp_config.py`
- `uv run ruff format` and `uv run ruff check`

## Completion criteria

- `validate_server_key` (new) exists and rejects keys with `.`, `/`, `\`, whitespace, control characters, uppercase, or more than 64 characters, at both `McpServerConfig` and `_build_mcp_servers`.
- `fields` is absent: constructing `McpServerConfig(fields=...)` raises `TypeError` and no code reads `.fields`.
- `credential_env` (new) is a declared key, parsed strictly, and defaults to an empty tuple.

## Out of Scope

- Building the child environment from `credential_env` (new) (rows 2 and 3).
- The `credential_env` (new) values themselves (row 6, `config/agent.toml`).
- The path-boundary check in the stderr log manager (row 5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261126 | Execute after the row 7-12 Phase 1 tests are in place (REQ-009) Implemented as specified, with the Step 3a verification findings applied. |
| 2 | Confirm the Phase 1 test additions from row 7 fail before this change and pass after it | Completed | — | 20261126 | Tests-first order per Plan Phase 1 tests/shared/test_mcp_config_validation.py and tests/shared/test_mcp_config.py: 137 passed after this change (23 failed before it). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261126 | Batch-end validation (release unit R1-launch-spec): ruff format+check, mypy 473 files, bandit 0 issues, lint-imports 6 contracts kept, check_module_size, check_mock_patch_targets, check_suppression_justification, check_docstrings. Full suite: 15116 passed, 16 failed (identical to the HEAD baseline: tests/integration/test_call_state_* pre-existing ToolCallState.args_hash failures). diff-cover 100% on changed source lines. |

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
- **Requirement ID**: REQ-002 (remove `fields`), REQ-005 (server-identifier rule), REQ-006 (declared credential variables)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `scripts/shared/mcp_config.py`