## Goal

Give the config errors a structured payload and add the commit and rollback failure types, so the CLI
catches them instead of showing an unhandled `TypeError` (REQ-011, structured config error).

## Scope
**Release unit**: R4-transaction-and-restore

## Assumptions
- Verified against current source: `exceptions.py:17` defines `ConfigReloadValidationError(ValueError)`
  with no payload; it is the only config error class in the module. `ConfigReloadError` (new) and the commit
  and rollback error types do not exist and are created by this document.
- `cmd_config.py:78-83` catches only `OSError` and `ValueError`, so a `TypeError` from a validator
  escapes today.

## Design decisions
- `ConfigReloadError` (new) is the base the command layer catches; `ConfigReloadValidationError`
  becomes its subclass so existing `except ValueError` behavior is preserved during the transition.
- The payload is the field path and the violated rule name, never the raw value (OD-04's error
  vocabulary from row 1).

## Alternatives considered
- Catching `TypeError` in the command layer — rejected: it would keep two error vocabularies and print
  the value.

## Implementation
### Target file
`scripts/agent/services/exceptions.py`

### Procedure
Give `ConfigReloadValidationError` a structured payload (field path, violated rule) and add
`ConfigReloadError` (new), `ConfigReloadCommitError` (new), and `ConfigReloadRollbackError` (new).

### Method
- Each error carries the field path and the rule name as attributes and builds its message from them.
- The rollback error also names the service left inconsistent, which is what `degraded` reports.

### Details
- No message includes the raw value; the existing `got {value!r}` wording is removed.

## Compatibility considerations
- `ConfigReloadValidationError` stays a `ValueError` subclass, so callers that catch `ValueError` keep
  working; `tests/agent/commands/test_agent_cmd_config.py` asserts the CLI outcome, not the class
  hierarchy.

## Security considerations
- Paths and tokens in `approval_protected_paths` and `memory_embed_url` must not reach the message.

## Rollback considerations
- Revert the Phase 4 commit.

## Validation plan
- `uv run pytest tests/agent/commands/test_agent_cmd_config.py -q`
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- Every config error names the field and the rule, no message contains a raw value, and the command
  layer catches `ConfigReloadError` (new) without an unhandled `TypeError`.

## Out of Scope
- The command-layer catch itself (row 19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | row 38 |
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
- **Requirement ID**: REQ-011 (structured config error); AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/services/exceptions.py`
