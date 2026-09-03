# Implementation Procedure: tests/agent/test_startup_prompt_setup.py

## Goal

Create dedicated test module for `PromptSetup` class extracted from `startup.py` (REQ-006).

## Scope

- Create `tests/agent/test_startup_prompt_setup.py` with tests for `PromptSetup` class
- Preserve all existing test behavior — no behavioral changes to test assertions
- Extract relevant tests from `tests/agent/test_startup.py` (TestStartupOrchestratorSetupPrompt, TestStartupMemoryFailures)

## Assumptions

- The `PromptSetup` class has two methods:
  - `setup_prompt()` — public method to inject semantic memories into system prompt
  - `_classify_memory_failure(exc)` — private helper for categorizing failures

## Design decisions

- **Dedicated test file**: One test file per new module following REQ-015 alignment
- **Preserve helper functions**: `_make_startup`, `_http_subprocess_cfg` stay in `test_startup.py` as shared helpers
- **No test logic changes**: Only move code, do not modify test assertions or behavior

## Alternatives considered

- **Keep all tests in one file**: Rejected: defeats the purpose of REQ-015 (align test structure with new module layout).
- **Rename existing test classes**: Rejected: would break test discovery and CI pipelines that reference specific class names.

## Implementation

### Target file

`tests/agent/test_startup_prompt_setup.py`

### Procedure

Create test file with tests for PromptSetup class.

### Method

File creation.

### Details

**Phase 4: Test Reorganization** (REQ-015)

Create `tests/agent/test_startup_prompt_setup.py` with:

1. `TestPromptSetupClassifyFailure` — tests for `_classify_memory_failure`:
   - `test_network_transient_classification` — ConnectionError → "NETWORK_TRANSIENT"
   - `test_database_or_io_classification` — sqlite3.Error → "DATABASE_OR_IO"
   - `test_unknown_classification` — ValueError → "UNKNOWN"

2. `TestPromptSetupSetupPrompt` — tests for `setup_prompt()`:
   - `test_no_pinned_notes_block_injected` — pinned notes must NOT appear
   - `test_memory_snippets_are_injected_when_enabled` — snippets ARE injected when enabled
   - `test_no_memory_injection_when_disabled` — prompt unchanged when disabled
   - `test_history_set_to_system_message` — history set after setup
   - `test_memory_snippets_truncated_when_exceeds_limit` — truncation works

3. `TestPromptSetupMemoryFailures` — tests for categorized logging:
   - `test_memory_injection_categorized_logging` — parametrized test for each category

## Compatibility considerations

- **Critical**: All test assertions must remain identical. No behavioral changes to test outcomes.
- **Import paths**: After moving test classes, update imports to reference new module locations.
- **Helper function placement**: `_make_startup` may need to be duplicated or imported into moved test files depending on which tests use it.

## Security considerations

- No security-sensitive changes. Test files contain no secrets or credentials.
- `_mask_secrets` is not called in test files.
- `StartupInterrupted` exception handling in tests must remain unchanged.

## Rollback considerations

- If reorganization breaks test discovery, revert to original `test_startup.py` structure.
- Restore all removed test classes to `test_startup.py`.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `tests/agent/test_startup_prompt_setup.py` | Unit — PromptSetup tests | `uv run pytest tests/agent/test_startup_prompt_setup.py` | All pass |

## Completion criteria

- [ ] Test file created at `tests/agent/test_startup_prompt_setup.py`
- [ ] All test assertions preserved verbatim
- [ ] Import paths updated for moved test classes
- [ ] `ruff`, `mypy`, `bandit` clean on test file
- [ ] All tests pass

## Out of scope

- Changing test assertions or adding new tests
- Modifying `repl_health.py`, `http_lifecycle.py`, or `factory.py` internals
- Performance optimization

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-015
- **Source issue**: issues/20260831-155933_refactor_008_startup_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-073153_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142637
- **Related target files**: tests/agent/test_startup_prompt_setup.py
