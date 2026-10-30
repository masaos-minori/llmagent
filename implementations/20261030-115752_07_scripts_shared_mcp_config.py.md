# Implementation Procedure: `scripts/shared/mcp_config.py`

## Goal

Point the `McpServerConfig.required` field documentation at the mandatoriness registry as its authority (plan row: `required` field docstring points at the registry authority; P2).

## Scope

- Comment/docstring text in `scripts/shared/mcp_config.py` around the `required` field (:100 block), the subprocess rejection (`:163-167`), and the normalization site (`:326`).
- No validation added here: startup cross-validation belongs to rows 4-5 (plan Design: config provides effective values only).

## Assumptions

- Lightweight row: comment-only change, no behavior or contract change.

## Design decisions

- At the `required` field comment (:100-102, already citing ADR-004 Exceptions): add that the effective value is validated against `registry/component_mandatoriness.yaml` at startup and cannot weaken the approved classification (ADR-004 Group 3 item 13).
- Do not import the loader or call it here (REQ-007 leaf discipline and single-validation-site design).

## Alternatives considered

- N/A: comment-only change.

## Implementation

### Target file

`scripts/shared/mcp_config.py`

### Procedure

1. Extend the `required` field comment block (:100-103) with one sentence naming the registry path as the classification source.
2. At the normalization `required=bool(v.get("required", True))` (:326), add a short inline comment: value is checked against the registry in the startup pipeline (`scripts/agent/startup_validation.py`).

### Method

Comment edits only; `git diff` must show code lines unchanged.

### Details

- Keep wording consistent with row 6's `mcp_health.py` text (same registry path string).

## Compatibility considerations

- N/A: comments only.

## Security considerations

- N/A: no behavior change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run mypy scripts`, `uv run ruff check scripts tests tools`; no test changes required.

## Completion criteria

- A reader of the `required` field finds the registry path and the cannot-weaken rule from the field's own comment; no behavior changed (plan AC-6).

## Out of Scope

- All validation wiring (rows 4-5), `config/agent.toml` values (plan Excluded).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the two comment edits | Pending | — | — | |
| 3 | Run mypy/ruff gates | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (supports the classification contract by documenting the authority; validation itself lives in rows 4-5)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `scripts/shared/mcp_config.py`
