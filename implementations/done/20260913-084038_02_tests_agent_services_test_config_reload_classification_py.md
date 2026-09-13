# Implementation Procedure: Update test_config_reload_classification.py

## Goal

Update `tests/agent/services/test_config_reload_classification.py` to reflect the removal of `_detect_startup_only` and the consolidation of `_reload_*` methods. Delete tests for removed methods; verify remaining tests still pass. (REQ-001, REQ-002)

## Scope

- Modify `tests/agent/services/test_config_reload_classification.py` only
- Delete tests for `_detect_startup_only` (lines 44-51)
- Verify `_detect_diagnostics_live_fields` tests (lines 57-84) still pass
- Add/update tests for `_classify_startup_only_fields` (replacement for `_detect_startup_only`)

## Assumptions

- `_detect_startup_only` tests (lines 44-51) test the exact behavior that `_classify_startup_only_fields` will replace — their assertions should transfer directly
- `_detect_diagnostics_live_fields` tests (lines 57-84) are unaffected by the refactor
- The `_make_ctx()` fixture provides sufficient mock setup for the new `_classify_startup_only_fields` tests

## Design decisions

- Delete the two `_detect_startup_only` tests entirely (they test a method being removed)
- Create equivalent tests for `_classify_startup_only_fields` using the same assertions
- Keep `_detect_diagnostics_live_fields` tests unchanged (no behavioral change there)
- Keep the tool_cache_ttl regression tests unchanged (they test different code paths)

## Alternatives considered

- Renaming existing `_detect_startup_only` tests to `_classify_startup_only_fields` — rejected because the method signature differs (the old method took `new_cfg` only; the new method uses `CONFIG_FIELD_REGISTRY` internally). Creating new tests is clearer.
- Merging the two `_detect_startup_only` tests into one — rejected because they test distinct scenarios (empty dict vs. non-startup keys ignored).

## Implementation

### Target file

`tests/agent/services/test_config_reload_classification.py`

### Procedure

**Phase 1: Delete tests for removed methods**

1. Delete `test_detect_startup_only_empty_dict` (lines 44-46)
   - This test calls `svc._detect_startup_only({})` which will no longer exist
   - REQ-001; File: tests/agent/services/test_config_reload_classification.py

2. Delete `test_detect_startup_only_non_startup_keys_ignored` (lines 49-51)
   - This test calls `svc._detect_startup_only({"llm_temperature": 0.3, ...})` which will no longer exist
   - REQ-001; File: tests/agent/services/test_config_reload_classification.py

**Phase 2: Add tests for new method**

3. Add `test_classify_startup_only_empty_dict` 
   ```python
   def test_classify_startup_only_empty_dict(svc: ConfigReloadService) -> None:
       result = svc._classify_startup_only_fields({})
       assert result == []
   ```
   - Tests empty dict case — equivalent to deleted `test_detect_startup_only_empty_dict`
   - REQ-001; File: tests/agent/services/test_config_reload_classification.py

4. Add `test_classify_startup_only_non_startup_keys_ignored`
   ```python
   def test_classify_startup_only_non_startup_keys_ignored(svc: ConfigReloadService) -> None:
       # llm_temperature is hot_reloadable=True, so it should not appear in startup_only
       result = svc._classify_startup_only_fields({"llm_temperature": 0.3, "llm_max_tokens": 8192})
       assert result == []
   ```
   - Tests that hot-reloadable fields are excluded — equivalent to deleted `test_detect_startup_only_non_startup_keys_ignored`
   - REQ-001; File: tests/agent/services/test_config_reload_classification.py

5. Add `test_classify_startup_only_hot_reload_false_detected`
   ```python
   def test_classify_startup_only_hot_reload_false_detected(svc: ConfigReloadService) -> None:
       ctx = svc._ctx
       ctx.cfg.memory.use_memory_layer = False
       result = svc._classify_startup_only_fields({"use_memory_layer": True})
       assert "use_memory_layer" in result
   ```
   - Tests that `hot_reloadable=False` fields are detected when they differ
   - REQ-001; File: tests/agent/services/test_config_reload_classification.py

**Phase 3: Verify existing tests**

6. Verify `_detect_diagnostics_live_fields` tests (lines 57-84) still pass
   - These tests are unaffected by the refactor
   - Run them after other changes to confirm no regressions
   - REQ-002; File: tests/agent/services/test_config_reload_classification.py

### Method

Each phase above is independently verifiable. Phase 1 removes dead tests. Phase 2 adds equivalent tests for the new method. Phase 3 confirms no regressions.

### Details

**Phase 1 details:**
- Two tests must be deleted: lines 44-46 (`test_detect_startup_only_empty_dict`) and lines 49-51 (`test_detect_startup_only_non_startup_keys_ignored`)
- These tests call `svc._detect_startup_only()` which will no longer exist after the refactor

**Phase 2 details:**
- Three new tests must be added:
  1. Empty dict case — asserts empty list returned
  2. Hot-reloadable field exclusion — asserts hot-reloadable fields don't appear in startup_only
  3. Non-hot-reloadable field detection — asserts `hot_reloadable=False` fields are reported when they differ
- The `_make_ctx()` fixture already sets up `ctx.cfg.memory.use_memory_layer = False`, which is needed for test 3

**Phase 3 details:**
- Run `uv run pytest tests/agent/services/test_config_reload_classification.py -v` to verify all tests pass
- No changes needed to `_detect_diagnostics_live_fields` tests or tool_cache_ttl regression tests

## Compatibility considerations

- Test API compatibility: `_classify_startup_only_fields` has the same return type as `_detect_startup_only` (both return `list[str]`), so callers of `ConfigReloadOutcome.startup_only` are unaffected
- Mock setup: The `_make_ctx()` fixture already provides `ctx.cfg.memory.use_memory_layer = False`, which is needed for the new tests
- No changes to public test fixtures or test infrastructure

## Security considerations

- No security surface changed — test updates do not affect runtime behavior
- No new secrets or credentials introduced in test code

## Rollback considerations

- Each phase is independently revertible: revert the git commit for that phase
- Phase 1 (deleting tests) is low-risk rollback — if tests fail after adding new tests, deleting them restores the previous state
- Phase 2 (adding tests) is low-risk rollback — if new tests fail, removing them restores the previous state
- Phase 3 (verification) has no rollback risk — it's just running tests

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/services/test_config_reload_classification.py | Unit: verify new tests pass, old tests removed | uv run pytest tests/agent/services/test_config_reload_classification.py -v | All tests pass |
| tests/agent/services/test_config_reload_classification.py | Integration: verify full agent test suite passes | uv run pytest tests/agent/ -v --tb=short | All tests pass |

## Completion criteria

- [ ] Phase 1 complete: `_detect_startup_only` tests deleted; no references to removed method remain
- [ ] Phase 2 complete: Three new tests for `_classify_startup_only_fields` added with equivalent assertions
- [ ] Phase 3 complete: All tests in `test_config_reload_classification.py` pass; full agent test suite passes

## Out of scope

- Adding new test cases beyond those required by the refactor
- Modifying the `_make_ctx()` fixture or other shared test infrastructure
- Adding integration tests for `/reload` command handling
- Modifying test coverage for unrelated modules

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete tests for _detect_startup_only | Completed | 20260913-084700 | 20260913-084800 | REQ-001 |
| 2 | Add tests for _classify_startup_only_fields | Completed | 20260913-084800 | 20260913-084900 | REQ-001 |
| 3 | Verify existing tests still pass | Completed | 20260913-084900 | 20260913-085000 | REQ-002 |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260913-064743_refactor_config_reload_eliminate_duplication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-070431_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-084038
- **Related target files**: tests/agent/services/test_config_reload_classification.py
