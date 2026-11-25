## Goal

Type `ConfigReloadRequest` so a request cannot carry a raw value of the wrong shape, which is what
makes the reload path reject the same inputs startup rejects (REQ-005, outcome stage; REQ-009, pending
state; REQ-013, dead code).

## Scope
**Release unit**: R4-transaction-and-restore

## Assumptions
- Verified against current source: `ConfigReloadRequest` is a mutable dataclass at `models.py:336` with
  `dict | None` and `list[str] | None` fields, so a wrong-typed value enters the service as a `dict`.
- `ConfigReloadOutcome` is defined in `scripts/agent/services/config_reload.py:43`, not in `models.py`;
  the `stage` and `pending` fields are added by row 6, so this document does not add them.
- `source_files` is written by `cmd_config.py:61` and read by no code; it stays as-is because OD-07
  keeps the existing outcome fields for cliplc013.

## Design decisions
- The request fields become the typed section shapes the shared primitives produce, so a raw value of
  the wrong shape cannot be represented at the request boundary.
- The dataclass stays mutable; the typed candidate is built from it, not stored in it.

## Alternatives considered
- Validating the request inside the service — rejected: the type error would then be raised after the
  request was constructed, which is the current defect.

## Implementation
### Target file
`scripts/agent/services/models.py`

### Procedure
Type `ConfigReloadRequest` fields so a request cannot carry a raw value of the wrong shape.

### Method
- Each field keeps its `None` meaning (field not supplied) and becomes the typed section shape the
  candidate build produces.
- `masked_fields` keeps its `list[str]` shape because it is not a registry entry.

### Details
- No field stores the raw value; the field path and the rule name are what the error carries.

## Compatibility considerations
- `cmd_config.py` (row 19) constructs the request; the field names are unchanged, only their types.

## Security considerations
- No raw configuration value is stored in the request, so nothing can be printed from it.

## Rollback considerations
- Revert the Phase 4 commit.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload_transaction.py tests/agent/commands/test_agent_cmd_config.py -q`
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- A request built from a wrong-typed payload cannot be constructed, and the transaction tests read the
  stage from the outcome produced by row 6.

## Out of Scope
- The outcome `stage` and `pending` fields (row 6).
- The CLI reporting (row 19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | outcome fields are row 6 |
| 2 | Add or update tests per Validation plan | Pending | — | — | rows 26, 38 |
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
- **Requirement ID**: REQ-005 (reload transaction and stage), REQ-009 (pending display), REQ-013 (dead reload code removed); AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/services/models.py`
