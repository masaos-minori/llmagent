## Goal

Retarget the tests that encode the behavior this Plan removes, so the suite does not assert a defect: the
`_classify_mcp_server_changes` patch sites, the startup-only-applied assertions, the removed-key
tolerance, and the coverage of the deleted helpers (REQ-003, startup-only fields stay pending; REQ-010,
registry completeness; REQ-013, dead reload code removed).

## Scope
**Release unit**: R6-dead-code-removal

## Assumptions
- Verified against current source: `_classify_mcp_server_changes` is patched at
  `tests/agent/services/test_config_reload.py:92`, `:139`, `:551`, `:1003`, `:1024`, `:1288`, and
  `test_removed_map_reload_keys_are_ignored` is at `tests/agent/services/test_config_reload.py:372`.
- The retargeting lands before the code deletion (Plan Phase 6 order), so this file is changed first and
  the deletion in rows 5, 6, 10 follows.
- The new `TestConfigFieldRegistrySectionCategorization` class named by row 4 is added here; it does not
  exist today.

## Design decisions
- Retarget rather than delete wherever the behavior still exists in a new form; delete only the cases that
  covered the removed helpers.
- The removed-key case becomes a rejection expectation rather than an ignore expectation, which is the
  AC-6 contract.

## Alternatives considered
- Leaving the tests and marking them skipped — rejected: a skipped test that pins a defect is still a
  record of the defect.

## Implementation
### Target file
`tests/agent/services/test_config_reload.py`

### Procedure

### Method
- Retarget the six `_classify_mcp_server_changes` patch sites to the structured pending records from row 9.
- Retarget the startup-only group to assert the fields stay pending and `HistoryManager` is unchanged.
- Replace `test_removed_map_reload_keys_are_ignored` with a rejection expectation.
- Drop coverage of `prepare_direct_section`, `apply_direct_section`, `reload_validated_section`, and
  `reload_direct_fields` (row 5 deletes them).
- Add `TestConfigFieldRegistrySectionCategorization` (new) for `registry_for` and `startup_only_for`.

### Details
- The `memory_local_only=1` and `context_compress_turns='77'` accept assertions are replaced with
  rejection assertions.

## Compatibility considerations
- Blast radius: 1327 lines, the largest pin on reload behavior; every change here must match the contract
  the code rows create.

## Security considerations
- N/A: the tests assert behavior, not output.

## Rollback considerations
- Revert the Phase 6 commit; the test retargeting and the deletion are in the same commit.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py -q`
- `uv run vulture scripts/agent/services/ --min-confidence 60` — no test-only reference to a deleted helper remains
- `uv run ruff check tests`

## Completion criteria
- No test in this file calls or patches a deleted symbol, no test asserts that a startup-only field is
  applied, and the removed-key case asserts rejection.

## Out of Scope
- The classification contract itself (row 9).
- The helper deletions (rows 5, 6, 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | retargeting lands before the deletion |
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
- **Requirement ID**: REQ-003 (startup-only fields stay pending), REQ-010 (registry completeness), REQ-013 (dead reload code removed); AC-2, AC-6
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `tests/agent/services/test_config_reload.py`
