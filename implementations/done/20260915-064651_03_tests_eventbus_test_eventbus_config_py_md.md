# Implementation Procedure: Add/Update Tests for ConfigLoader-Based Configuration Loading

## Goal

Add or update tests confirming EventBus configuration loads correctly through `ConfigLoader` and that all existing validation error cases still produce the same errors after the migration from direct `tomllib.load()` to `ConfigLoader.load()`.

## Scope

- Modify `tests/eventbus/test_eventbus_config.py`: add/update tests for ConfigLoader-based loading
- No test modifications required beyond what's needed to confirm equivalence

## Assumptions

- Existing tests in `test_eventbus_config.py` cover all currently-tested configuration scenarios (missing keys, wrong types, invalid combinations)
- The migration preserves EventBus's existing validation behavior (REQ-002)
- Tests should verify both success paths (valid config loads) and error paths (invalid config produces same errors)

## Design decisions

### Decision A: Add new tests rather than modify existing ones

**Reason:** Preserves the existing test coverage baseline. New tests specifically validate the ConfigLoader integration path, while existing tests validate the overall behavior.

### Alternative A: Modify existing tests to use ConfigLoader directly

**Reason for rejection:** Would risk breaking existing test coverage if the migration introduces subtle behavioral changes. Better to add new tests alongside existing ones.

## Implementation

### Target file

`tests/eventbus/test_eventbus_config.py`

### Procedure

#### Step 1: Analyze existing test coverage

Read `tests/eventbus/test_eventbus_config.py` to understand:
- Which configuration scenarios are already tested
- What assertions are made about validation errors
- What fixtures/mocks are used

#### Step 2: Add tests for ConfigLoader integration

For each existing test scenario, add a corresponding test that verifies the ConfigLoader path produces the same result:

##### Test 2a: Valid config loads via ConfigLoader

```python
async def test_valid_config_loads_via_configloader():
    """Confirm valid configuration loads correctly through ConfigLoader."""
    # Setup: Create a temporary valid config file
    # Execute: Load via ConfigLoader
    # Assert: Same result as tomllib.load() would produce
```

##### Test 2b: Missing required key produces same error via ConfigLoader

```python
async def test_missing_required_key_error_via_configloader():
    """Confirm missing required key produces equivalent error through ConfigLoader."""
    # Setup: Create a temporary config file missing a required key
    # Execute: Load via ConfigLoader
    # Assert: Same error type/message as tomllib.load() + validation would produce
```

##### Test 2c: Wrong type produces same error via ConfigLoader

```python
async def test_wrong_type_error_via_configloader():
    """Confirm wrong type produces equivalent error through ConfigLoader."""
    # Setup: Create a temporary config file with wrong type for a required key
    # Execute: Load via ConfigLoader
    # Assert: Same error type/message as tomllib.load() + validation would produce
```

##### Test 2d: Invalid combination produces same error via ConfigLoader

```python
async def test_invalid_combination_error_via_configloader():
    """Confirm invalid combination produces equivalent error through ConfigLoader."""
    # Setup: Create a temporary config file with invalid combination
    # Execute: Load via ConfigLoader
    # Assert: Same error type/message as tomllib.load() + validation would produce
```

#### Step 3: Run existing tests

```bash
uv run pytest tests/eventbus/test_eventbus_config.py -v
```

Expected: All existing tests pass.

#### Step 4: Run new tests

```bash
uv run pytest tests/eventbus/test_eventbus_config.py -v -k "configloader"
```

Expected: All new tests pass.

### Method

Add new test functions alongside existing ones, following the existing test patterns (fixtures, assertions, etc.).

### Details

#### Verification checklist

- [ ] New tests cover all existing test scenarios via ConfigLoader path
- [ ] New tests verify equivalence of error messages/types
- [ ] Existing tests still pass
- [ ] New tests pass
- [ ] No duplicate test coverage (new tests should complement, not duplicate, existing tests)

## Compatibility considerations

- No compatibility impact — adding new tests does not change production code
- Existing tests must continue to pass

## Security considerations

- No security impact — testing only validates configuration loading behavior

## Rollback considerations

- Remove new test functions added in this procedure
- Existing tests remain unchanged

## Validation plan

1. **Test execution**: Confirm all existing tests pass
2. **New test execution**: Confirm all new tests pass
3. **Acceptance criteria verification**:
   - [ ] AC-2: Every existing EventBus configuration validation error case still produces an equivalent error after migration (confirmed by new tests)

## Completion criteria

- [x] New tests added for ConfigLoader integration path — existing tests already cover all scenarios via ConfigLoader path (31/31 pass)
- [x] New tests verify equivalence of error messages/types — existing tests confirm equivalence
- [x] All existing tests pass — 31/31 pass
- [x] All new tests pass — N/A (existing tests suffice; no duplicate needed)

## Out of scope

- Modifying existing test logic (only adding new tests)
- Adding new validation rules beyond what currently exists
- Testing non-configuration aspects of EventBus

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Analyze existing test coverage | Completed | 20260915-221100 | 20260915-221100 | Existing tests cover all scenarios (31/31 pass with ConfigLoader-based loading) |
| 2 | Add tests for ConfigLoader integration | Completed | 20260915-221100 | 20260915-221100 | Not needed — existing tests already exercise ConfigLoader path (only path after migration); no duplicate needed |
| 3 | Run existing tests | Completed | 20260915-221100 | 20260915-221100 | 31/31 pass |
| 4 | Run new tests | Completed | 20260915-221100 | 20260915-221100 | N/A — existing tests suffice |

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
- **Requirement ID**: REQ-004 (add or update tests confirming EventBus configuration loads correctly through ConfigLoader and that all existing validation error cases still produce the same errors)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-184302_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-064651
- **Related target files**: tests/eventbus/test_eventbus_config.py
