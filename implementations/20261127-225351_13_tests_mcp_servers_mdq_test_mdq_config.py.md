# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_config.py

## Goal

Assert the renamed byte-limit default and the field list, so the renamed key is pinned at the
configuration boundary.

## Scope
**Release unit**: byte-limit-key-rename

Requirement implemented: REQ-004 (the renamed byte-limit default and field list).
Acceptance criterion: AC-3.

## Assumptions
- The field itself is renamed by procedure seq 01 and the validated key list by procedure seq 07; this
  document only changes the assertions.
- The strict-type cases in this file belong to the server-boundary plan and are not changed here
  (cross-plan overlap recorded in the Plan's Assumptions).

## Design decisions
- Two assertion sites change: the default value assertion and the parametrized field list. No new case
  is added, because the decoded-character limit is not a configuration key (UNK-02).

## Alternatives considered
- Adding a case that accepts both key names: rejected, because the Plan renames the key rather than
  aliasing it (UNK-01).

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_config.py`

### Procedure
Rename the key in the default assertion and in the parametrized field list.

### Method
Assertion-level changes only.

### Details
- Line 27: `assert cfg.max_file_chars == 100000` becomes the assertion for `max_file_bytes` (new),
  with the same expected default.
- Line 48: the parametrized field-list entry `max_file_chars` becomes `max_file_bytes` (new).

## Compatibility considerations
- The test changes in the same commit as the model field, the validated key list, the config file, and
  the doc statement (release unit `byte-limit-key-rename`).

## Security considerations
- N/A: test-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py` — the renamed default and the field list.
- Baseline before any change: 159 passed for the five-file subset (re-run 20261127).

## Completion criteria
- The renamed key is asserted as the default and appears in the validated field list.

## Out of Scope
- The field definition (procedure seq 01) and the validated key list (procedure seq 07).
- The strict-type cases owned by the server-boundary plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename the key in the default assertion and the field list | Pending | — | — | REQ-004, AC-3, Phase 4 |
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
- **Requirement ID**: REQ-004 (the renamed byte-limit default and field list)
- **Source issue**: `issues/done/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-225351
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_config.py`
