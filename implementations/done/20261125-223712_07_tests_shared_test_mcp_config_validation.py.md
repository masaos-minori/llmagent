## Goal

Cover the server-key pattern, the removed `fields` field, and the new `credential_env` key at the configuration layer (REQ-005 identifier rule, REQ-009 tests written before the implementation).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- These cases are written in Plan Phase 1 and are expected to fail until rows 1 and 6 land (Plan Execution Status step 1).
- The file's existing config helpers `_http_cfg` (line 7) and `_subprocess_cfg` (line 22) build configs through keyword arguments, so new cases extend them rather than constructing `McpServerConfig` directly.

## Design decisions

- One parametrized key table reused across both enforcement points (`McpServerConfig(key=...)` and `_build_mcp_servers` on a TOML-shaped dict), so the config layer and the parser are proven to enforce the identical rule (AC-4).
- The `fields` case asserts a `TypeError` from the constructor rather than inspecting the dataclass fields, which is the contract REQ-002 states.

## Alternatives considered

N/A: the test design follows the Plan's Tests section directly; no alternative case layout was considered.

## Implementation
### Target file
`tests/shared/test_mcp_config_validation.py`
### Procedure
Add the key-pattern, `fields`-removed, and `credential_env` type cases alongside the existing denylist cases at `:176-188`.

### Method
- Add a parametrized invalid-key case: `..`, `a/b`, `a.b`, `A`, `a b`, `a\n`, a 65-character key, and a key with a control character, asserted against both `McpServerConfig(key=...)` and `_build_mcp_servers`.
- Add a valid-key case for the accepted forms (`a`, `a0`, `a_b`, `a-b`, a 64-character key) to pin the boundary.
- Add `test_config_fields_kwarg_rejected` (new): `McpServerConfig(fields={...})` raises `TypeError` (REQ-002).
- Add `credential_env` cases: a valid list of names parses to a tuple, a non-list value raises, a non-string element raises, a wildcard-containing name raises, and a denylisted name (`LD_PRELOAD`) raises (REQ-006).
- Add an unknown-key case proving `credential_env` is a declared key once row 1 lands, so `reject_unknown_keys` accepts it.

### Details
- Assert that raised messages name the server key and the field and do not contain the value, matching the parser convention (`scripts/shared/mcp_config.py:353-366`).
- Keep the empty-`key` default behavior explicit with one case that a directly constructed config with the default `key` still validates.

## Compatibility considerations

Additive cases only; the existing 30-plus cases in the file stay unchanged, so the ADR citations of `tests/shared/test_mcp_config.py` are untouched (Plan Design).

## Security considerations

N/A: this row only asserts the rules enforced by rows 1 and 5.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_mcp_config_validation.py tests/shared/test_mcp_config.py`
- Expected outcome before rows 1 and 6 land: the new cases fail (Plan Phase 1)

## Completion criteria

- Every invalid key form in AC-4 is asserted at both config-layer enforcement points.
- A `fields` keyword and a malformed `credential_env` value are both rejected with a message that names the field.

## Out of Scope

- Implementing `validate_server_key` (row 1).
- The log-manager key case (row 12).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the test cases described in Implementation > Procedure/Method/Details | Completed | 20261126 | 20261126 | Plan Phase 1: expected to fail until rows 1 and 6 land |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261126 | Changed: tests/shared/test_mcp_config_validation.py; 23 new cases fail as expected (Plan Phase 1) |

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
- **Requirement ID**: REQ-005 (server-identifier rule), REQ-009 (tests written before the implementation)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `tests/shared/test_mcp_config_validation.py`