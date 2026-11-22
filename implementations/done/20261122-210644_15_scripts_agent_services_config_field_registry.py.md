## Goal

Register the new approval field in the config field registry (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `scripts/agent/services/config_field_registry.py`; tests are the config builders test row.

## Assumptions

- Verified precedent: `ConfigFieldRegistry("gitops_push_blocked", "approval", False)` (`scripts/agent/services/config_field_registry.py:87`); the third argument follows that row.

## Design decisions

- Add one registry entry for `approval_medium_preview_fallback` in the approval group with the same reload class as the precedent.

## Alternatives considered

N/A: follows the existing pattern.

## Implementation
### Target file
`scripts/agent/services/config_field_registry.py`

### Procedure
1. Add the entry next to the `gitops_push_blocked` row.

### Method
One tuple-like entry.

### Details
- Run the registry consistency tests that compare registry names with dataclass fields.

## Compatibility considerations

Reload behavior for the new field matches the precedent.

## Security considerations

N/A: configuration plumbing.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_config_builders.py tests/agent/services -k config -q`
- `uv run ruff check scripts/agent/services/config_field_registry.py && uv run mypy scripts/agent/services/config_field_registry.py`

## Completion criteria

- The registry lists the field and no registry-versus-dataclass consistency test fails.

## Out of Scope

Dataclass, builder, docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-213744 | 20261122-213744 | Changed: scripts/agent/services/config_field_registry.py |
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
- **Requirement ID**: `REQ-005` (register the field and its reload class)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/services/config_field_registry.py`
