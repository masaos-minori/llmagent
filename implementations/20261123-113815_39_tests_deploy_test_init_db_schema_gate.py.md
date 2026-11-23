## Goal

Update the deploy gate test that pins the stamped `PRAGMA user_version` to the literal 1 so it follows `_USER_VERSION`.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the assertion at about line 439 and any message text comparing against `expected 1`.

## Assumptions

- Verified: the test runs `init_db.sh` and then asserts `PRAGMA user_version` equals 1.

## Design decisions

- Import `_USER_VERSION` from `shared.mcp_dedup_schema` and compare with it.

## Alternatives considered

N/A: minimal edit.

## Implementation
### Target file
`tests/deploy/test_init_db_schema_gate.py`

### Procedure
1. Replace the literal with `_USER_VERSION`; update any helper text that mentions version 1.

### Method
Single-file edit; keep the surrounding fixtures.

### Details
- If a test simulates a version mismatch with a literal, derive it from `_USER_VERSION + 1`.

## Compatibility considerations

N/A: tests only.

## Security considerations

N/A: tests only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/deploy/test_init_db_schema_gate.py`

## Completion criteria

- The deploy gate tests pass with version 2 and do not hard-code a version.

## Out of Scope

The script itself (row 38).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (store schema bump and fingerprint refusal)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `tests/deploy/test_init_db_schema_gate.py`
