## Goal
- Remove `server.supported_extensions` from the shared posture check inventory for the file_write server (REQ-006, `supported_extensions` removal).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `file_write` check-id tuple entry at line 82; the pinned test update in the companion.
- Out of scope: the producer removal (seq 11), the health-view removal (seq 12).

## Assumptions
- Verified in Step 3a: the id is listed in the `file_write` tuple at line 82 of `scripts/shared/security/posture_contract.py`.
- The inventory and the producer must drop the id in the same change set; the check-set comparison tests pin both sides.

## Design decisions
- The inventory entry is deleted, not marked optional: the producer no longer emits the check, so a retained id would fail the inventory-vs-produced comparison.

## Alternatives considered
- N/A: single-entry removal with no contract decision of its own.

## Implementation
### Target file
`scripts/shared/security/posture_contract.py`

### Procedure
1. Remove `"server.supported_extensions"` from the `file_write` check-id tuple (line 82).

### Method
- `COMMON_CHECK_IDS` and the other server tuples are unchanged.

### Companion test files
- `tests/shared/test_security_posture_contract.py`
  - Procedure: update the expected `file_write` id set at line 74.
  - Validation: run the inventory-vs-produced comparison.

## Compatibility considerations
- Any consumer comparing the inventory against produced checks sees one fewer id; the only recorded consumers are the pinned tests (seq 11 companion) and the write server posture (seq 12 companion).

## Security considerations
- N/A: inventory bookkeeping for a control that never existed.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Companion tests: update the expected id set; run the inventory-vs-produced comparison.
- `uv run pytest tests/shared/test_security_posture_contract.py -v`; `uv run pytest tests/mcp_servers/file/test_file_security_validation.py -v` (seq 11 companion); full `rules/toolchain.md` sequence.

## Completion criteria
- The shared inventory no longer lists `server.supported_extensions` for file_write; comparison tests pass (AC-5).

## Out of Scope
- Producer removal (seq 11), health view (seq 12).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-183358 | 20261126-183358 | Removed the id from the file_write tuple. Tool-gate regeneration: registry/manifests/health_contracts.yaml regenerated via generate_reference_table.py --manifests — the manifest carried the same id, so the generated artifact changed in the same change set (Step 3a addition). Files: scripts/shared/security/posture_contract.py, registry/manifests/health_contracts.yaml |
| 2 | Add or update tests per Validation plan | Completed | 20261126-183358 | 20261126-183358 | Expected file_write id set updated at line 74. Targeted run 110 passed (contract test 60 + seq 11 companion 50); the seq 11 check-set comparison failure is resolved by this cycle. Files: tests/shared/test_security_posture_contract.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-201535 | 20261126-201535 | ruff/mypy/lint-imports/module-size/mock-patch-targets/reference-table pass after manifest regeneration; full-suite run deferred to end of plan batch; Step 5/6: N/A: no docs/00_index.md task-scope mapping for scripts/shared/security/posture_contract.py End-of-batch full-suite run passed (15774 passed, 5 skipped); diff-cover 100% on changed lines; gates pass including reference-drift after the manifest regeneration. Intermittent flaky failures in 3 unrelated tests under -n logical, all pass serially. |

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
- **Related target files**: `scripts/shared/security/posture_contract.py`, `tests/shared/test_security_posture_contract.py`