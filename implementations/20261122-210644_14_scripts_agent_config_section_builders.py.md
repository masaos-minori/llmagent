## Goal

Build the new approval field from config with its default (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `scripts/agent/config_section_builders.py`; tests are the config builders test row.

## Assumptions

- Verified precedent: `gitops_push_blocked` is read with `_get_or_default(cfg, ..., _get_bool, False)` and passed to the constructor (`scripts/agent/config_section_builders.py:269,277`).

## Design decisions

- Read `approval_medium_preview_fallback` the same way with default True and pass it to `ApprovalConfig`.

## Alternatives considered

N/A: follows the existing pattern.

## Implementation
### Target file
`scripts/agent/config_section_builders.py`

### Procedure
1. Add the `_get_or_default` read and the constructor argument beside `gitops_push_blocked`.

### Method
Two lines in the approval section builder.

### Details
- A non-boolean value is rejected by `_get_bool` as for the other fields.

## Compatibility considerations

Missing key yields True; configs stay valid.

## Security considerations

N/A: configuration plumbing.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_config_builders.py -q`
- `uv run ruff check scripts/agent/config_section_builders.py && uv run mypy scripts/agent/config_section_builders.py`

## Completion criteria

- The builder returns the field's default and honors an override.

## Out of Scope

Dataclass, registry, docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`); assertions are in the config builders test row | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (build the new approval field)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/config_section_builders.py`
