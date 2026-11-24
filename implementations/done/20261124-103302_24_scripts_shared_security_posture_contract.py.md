## Goal

Extend the pinned check inventory at its source so the two checks row 4 adds can be asserted (REQ-009: the posture reports what the code enforces; AC-9). This table is what `tests/mcp_servers/github/test_github_security_validation.py:198` compares the produced checks against; the test constant alone cannot be extended without it. Added as a target row on 2026-11-24 (fallout class, user-approved) because the Plan's consumer scan recorded the inventory as pinned only in the test file.

## Scope
**Release unit**: N/A: not part of a release unit (Plan Phase 4 is validated on its own)

## Assumptions

- The two ids are appended to the github row (lines 50-60) in the order `validate_github_security()` produces them, which is the order row 4 appends its checks at the end of the fixed sequence.
- `COMMON_CHECK_IDS` is unchanged; the companion test's assertion that compares `COMMON_CHECK_IDS + SERVER_CHECK_IDS[server_key]` against this table is what makes the two ids observable.

## Design decisions

- The order in the tuple is a contract, not formatting: the inventory test asserts the produced order equals it, so the tuple order must match the code's emission order.

## Alternatives considered

- Extending only the test constant — rejected: the test derives its expected value from this table, so that change alone fails.

## Implementation
### Target file
`scripts/shared/security/posture_contract.py`

### Procedure
1. Append `"server.global_search"`, `"server.max_file_read_size"` to the `"github"` tuple in `REQUIRED_CHECK_IDS` (lines 50-60), in that order.
2. Change nothing else in the file: the common ids, the other server rows, and the docstrings stay as they are.

### Method
- The file is a data table; no behavior change beyond the recorded inventory.

### Details
- `check_docs_consistency.py --domain mcp` cross-checks the docs settings-to-check mapping (row 22) against this table, so the docs rows and this row must carry the same ids.
- No `# ADR-NNN` marker is required: the file is not named by the ADR Invariant Matrix.

### Companion test files
- `tests/shared/test_security_posture_contract.py`
  - Procedure: add the same two ids to the mirrored `"github"` tuple in `SERVER_CHECK_IDS` (lines 46-55); the mirror exists so a change to the table reads as a decision. No new cases are needed — the assertions at lines 343 and 351 compare the two tables as they are written.
  - Validation: `uv run pytest tests/shared/test_security_posture_contract.py` (AC-9).

## Compatibility considerations

- The `/health` security block gains two entries for github-mcp; the Agent reads the block during startup readiness, so a `warning` from `server.global_search` at the shipped default becomes visible. No response shape change.

## Security considerations

- Keeping the inventory in one place is what makes the docs mapping in row 22 verifiable; a check that is emitted but not in the table is unreported, and a check in the table but not emitted is a claim without enforcement.

## Rollback considerations

- High: revert the two tuple entries; no data or config depends on them.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/shared/security/posture_contract.py` | Unit (contract table and its mirror) | `uv run pytest tests/shared/test_security_posture_contract.py` | Ten github ids, in the order the guard produces them |
| Same file | Cross-check | `uv run python tools/check_docs_consistency.py --domain mcp` | The docs mapping rows agree with this table |
| Same file | Quality gates | `uv run ruff check scripts/shared/security/posture_contract.py`, `uv run mypy scripts/shared/security/posture_contract.py`, `uv run bandit scripts/shared/security/posture_contract.py` | No finding |

## Completion criteria

- The github inventory contains the two new ids in the emitted order, the mirror test agrees, and `tests/mcp_servers/github/test_github_security_validation.py` passes with the cases written by row 20.

## Out of Scope

- Defining the two checks (row 4) and the docs settings-to-check mapping rows (row 22).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the two ids to the github tuple per Procedure | Completed | 20261124-152854 | 20261124-152854 | Row added by amendment on 2026-11-24 (fallout, user-approved) |
| 2 | Add the two ids to the mirror tuple (companion `tests/shared/test_security_posture_contract.py`) | Completed | 20261124-152854 | 20261124-152854 | Same commit as step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) plus `check_docs_consistency.py --domain mcp` | Completed | 20261124-152854 | 20261124-152854 | generated fallout: registry/manifests/health_contracts.yaml regenerated with generate_reference_table.py --manifests |

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
- **Requirement ID**: REQ-009 (the posture reports the settings it enforces)
- **Source issue**: issues/done/20261119-140509_mcpai002_github-read-security-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095007_mcpai002_github-read-security-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103302
- **Related target files**: `scripts/shared/security/posture_contract.py`, `tests/shared/test_security_posture_contract.py`