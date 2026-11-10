## Goal

Delete the single-valued `SecurityProfile` enum from `shared/mcp_config.py` and its test class (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

Edit `scripts/shared/mcp_config.py` and its companion `tests/shared/test_mcp_config.py`. All other readers are separate Plan rows.

## Assumptions

- Phase 3 of the Plan. Every `SecurityProfile` user in `scripts/` is a Plan row (`production_config_validator.py`, `config_dataclasses.py`, `config_builders.py`); the enum must be deleted last among them or in the same change, otherwise their imports fail.
- `StrEnum` stays imported (still used by `FailurePolicy`, `TransportType`, `StartupMode`).

## Design decisions

- Delete the class (lines 66-70) and nothing else; no alias is left behind (no-compatibility-shim rule, `tools/check_compat_shims.py`).

## Alternatives considered

N/A: removal is the Plan decision.

## Implementation
### Target file
`scripts/shared/mcp_config.py`

### Procedure
1. Delete `class SecurityProfile(StrEnum)` and its docstring (lines 66-70) plus the surrounding blank lines.

### Method
- `rg -n "SecurityProfile" scripts/shared` must return nothing afterwards (other modules are fixed by their rows).

### Details
- Do not touch `FailurePolicy`, `TransportType`, `StartupMode`.

### Companion test files
- `tests/shared/test_mcp_config.py`
  - Procedure: Delete the `SecurityProfile` import (line 8) and the `TestSecurityProfile` class (lines 275-285 and its parametrized members).
  - Validation: `uv run pytest tests/shared/test_mcp_config.py -v`

## Compatibility considerations

Import of `shared.mcp_config.SecurityProfile` now fails; in-repo users are Plan rows.

## Security considerations

N/A: the enum had one member and gated nothing.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_mcp_config.py -v`; `uv run ruff format`/`ruff check` on both files; `uv run mypy --no-namespace-packages scripts/`.
- `uv run python tools/check_compat_shims.py` (no shim left).

## Completion criteria

- No `SecurityProfile` in `scripts/shared/mcp_config.py` or `tests/shared/test_mcp_config.py`.

## Out of Scope

- Documentation of the profile (own Plan rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the enum | Pending | — | — | REQ-007 |
| 2 | Delete the companion test class and import | Pending | — | — | REQ-007 |
| 3 | Run ruff, mypy, compat-shim check and the config tests | Pending | — | — |  |

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
- **Requirement ID**: `REQ-007`
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/shared/mcp_config.py`, `tests/shared/test_mcp_config.py`
