## Goal
- Remove `supported_extensions_count` from the write server health view (REQ-006, `supported_extensions` removal).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the health-view line 75 that reads `cfg.supported_extensions`; the pinned test updates in the companion.
- Out of scope: the config field removal (seq 03), the posture check removal (seq 11), the shared inventory removal (seq 13).

## Assumptions
- Verified in Step 3a: the view function builds a scalars-and-counts dict (the file-write health view, REQ-009 lineage); `supported_extensions_count` is one of its entries at line 75.
- After seq 03 the config field no longer exists, so the view line must be removed in the same change set.

## Design decisions
- The view keeps the scalars-and-counts-only contract; removing one count entry does not change the shape rule.

## Alternatives considered
- N/A: single-entry removal with no contract decision of its own.

## Implementation
### Target file
`scripts/mcp_servers/file/write_server.py`

### Procedure
1. Remove the `supported_extensions_count` entry from the health view dict (line 75).

### Method
- N/A: mechanical removal; remaining entries are unchanged.

### Companion test files
- `tests/mcp_servers/file/test_file_write_health_posture.py`
  - Procedure: remove the pins at lines 32, 103, 127-128.
  - Validation: assert the view has no `supported_extensions_count` key.

## Compatibility considerations
- Health consumers reading `supported_extensions_count` from the view lose the key; the companion pins are the only recorded consumers.

## Security considerations
- N/A: the view already carries only scalars and counts; no sensitive values are involved.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Companion tests: remove the pins listed above; assert the view has no `supported_extensions_count` key.
- `uv run pytest tests/mcp_servers/file/test_file_write_health_posture.py -v`; full `rules/toolchain.md` sequence.

## Completion criteria
- The health view no longer contains `supported_extensions_count`; pinned tests pass (AC-5).

## Out of Scope
- Config field (seq 03), posture check (seq 11), shared inventory (seq 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-183306 | 20261126-183306 | Removed the supported_extensions_count entry from the health view dict. Files: scripts/mcp_servers/file/write_server.py |
| 2 | Add or update tests per Validation plan | Completed | 20261126-183306 | 20261126-183306 | Pins removed: expected-check-ids set, view assertion. Step 3a correction: the line-103 pin was the whole body of test_unenforced_extension_setting_is_published_as_not_applicable, so the test was deleted with the check removed by seq 11. Targeted run 34 passed — this cycle resolves the pending supported_extensions failures in test_call_tool_validation.py and test_file_server_audit_records.py owned by this seq. Files: tests/mcp_servers/file/test_file_write_health_posture.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-201535 | 20261126-201535 | ruff/mypy/lint-imports/module-size/mock-patch-targets/reference-table pass; full-suite run deferred to end of plan batch; Step 5/6: N/A: no docs/00_index.md task-scope mapping for scripts/mcp_servers/file/write_server.py End-of-batch full-suite run passed (15774 passed, 5 skipped); diff-cover 100% on changed lines; gates pass. Intermittent flaky failures in 3 unrelated tests under -n logical, all pass serially. |

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
- **Requirement ID**: `REQ-006` (`supported_extensions` removal from code, posture, tests, documentation)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `scripts/mcp_servers/file/write_server.py`, `tests/mcp_servers/file/test_file_write_health_posture.py`