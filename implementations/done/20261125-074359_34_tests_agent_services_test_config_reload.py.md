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
Retarget this file before the code deletion, per the Plan's Phase 6 step 1: the
`_classify_mcp_server_changes` patch sites, the startup-only group, the removed-key tolerance, and the new
registry-categorization class.

### Method
- Retarget the six `_classify_mcp_server_changes` patch sites to the structured pending records from row 9.
- Retarget the startup-only group to assert the fields stay pending and `HistoryManager` is unchanged.
- Replace `test_removed_map_reload_keys_are_ignored` with a rejection expectation.
- Add `TestConfigFieldRegistrySectionCategorization` (new) for `registry_for` and `startup_only_for`.

### Details
- Verified against current source: no test in this file calls `prepare_direct_section`,
  `apply_direct_section`, `reload_validated_section`, or `reload_direct_fields`, so row 5's deletion needs
  no test removal here.
- Verified against current source: this file contains no `memory_local_only=1` or
  `context_compress_turns='77'` accept assertion; those values were accepted by a probe during Plan
  analysis. The rejection assertions for them belong to the parity test (row 27).

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-205000 | 20261125-210919 | retargeting lands before the deletion R6 run 20261125: six direct _sync_services calls, four _classify_startup_only_fields calls and the sync mock retargeted to ServiceSyncer steps and classify_startup_only_fields; 83 cases pass |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-205000 | 20261125-210919 | R6 run 20261125: six direct _sync_services calls, four _classify_startup_only_fields calls and the sync mock retargeted to ServiceSyncer steps and classify_startup_only_fields; 83 cases pass |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | The patch sites and the removed-key case this procedure named were retargeted in the R2 and R3 runs (`diff_mcp_definitions` at the import, `test_removed_map_reload_keys_are_rejected`, `TestConfigFieldRegistrySectionCategorization`). The R6 run covers what the procedure did not name: six direct `_sync_services` calls, four `_classify_startup_only_fields` calls, and the `svc._sync_services = MagicMock()` patch in `TestMaskedFieldsCandidateFold` | Yes | 2026-11-25 |
| 1 | `TestLegacySyncServicePath` is retargeted, not deleted: `TestServiceSyncerLlmStep` pins the same live-LLM behavior on `ServiceSyncer.prepare_llm`, the step the transaction now drives, so no assertion is lost (REQ-006, REQ-013) | Yes | 2026-11-25 |
| 1 | `TestRuntimeToolPolicyReapplication` now drives `ServiceSyncer.prepare_runtime_tools` and its `apply()`, so the registry policy assertions survive the deletion; `test_runtime_tools_reported_in_applied` becomes `test_the_registry_step_is_named_runtime_tools` because the applied report is the transaction's, not a sync result's | Yes | 2026-11-25 |
| 1 | `tests/agent/services/test_config_reload_classification.py` also called the deleted wrapper four times and is not a target row of this Plan. Retargeted to the module-level `classify_startup_only_fields` in the same commit | Yes | 2026-11-25 |

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