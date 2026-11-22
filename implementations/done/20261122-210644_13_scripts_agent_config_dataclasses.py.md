## Goal

Add the explicit MEDIUM preview-fallback setting to `ApprovalConfig` (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `scripts/agent/config_dataclasses.py`; builder and registry are separate rows; tests are the config builders row.

## Assumptions

- Verified precedent: `gitops_push_blocked: bool = False` in `ApprovalConfig` (`scripts/agent/config_dataclasses.py:293`).
- Needs confirmation (non-blocking, UNK-02): the default; this procedure uses True (fallback allowed, today's behavior).
- Overlap: the open mcpdl003 procedures also edit this file for a different field.

## Design decisions

- Add `approval_medium_preview_fallback`(new)`: bool = True` with a one-line comment that HIGH never falls back.

## Alternatives considered

Rejected: a module constant (the Issue asks for an explicit setting).

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`

### Procedure
1. Add the field next to the other approval booleans with its comment.

### Method
One dataclass field.

### Details
- Respect the config comment length checker (`tools/check_config_comment_length.py`).

## Compatibility considerations

Default preserves current behavior; configs without the key load unchanged.

## Security considerations

HIGH risk ignores this setting and always fails closed.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_config_builders.py -q`
- `uv run ruff check scripts/agent/config_dataclasses.py && uv run mypy scripts/agent/config_dataclasses.py`

## Completion criteria

- The field exists with default True and passes the config checks.

## Out of Scope

Builder, registry, docs, and the approval logic that reads it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-213744 | 20261122-213744 | Changed: scripts/agent/config_dataclasses.py |
| 2 | Run the validation sequence (`rules/toolchain.md`); assertions are in the config builders test row | Completed | 20261122-213744 | 20261122-213744 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-005` (explicit MEDIUM preview-fallback setting)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/config_dataclasses.py`
