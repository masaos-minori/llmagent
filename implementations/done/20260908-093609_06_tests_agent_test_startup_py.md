# Implementation Procedure: Add unknown-key rejection test

## Traceability
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source plan**: plans/20260907-234317_plan.md
- **Related target files**: tests/agent/test_startup.py

## Goal
Add startup validation test asserting unknown top-level key rejection in `tests/agent/test_startup.py`.

## Priority
High

## Scope
- **In-Scope**: Add test for unknown-key rejection
- **Out-of-Scope**: Any other test_startup.py behavior change

## Background
No existing test covers unknown-key rejection (REQ-004; Acceptance criterion 2). The new test must assert that an unknown/mistyped top-level config key (not among `agent/config_dataclasses.py`'s introspected fields) is rejected in production.

## Problem
No test exists to verify the unknown-key rejection behavior.

## Reason for change
This is a test coverage addition — the unknown-key rejection behavior must be tested to prevent regression.

## Implementation Steps

### Step 1: Understand the current test structure
Read `tests/agent/test_startup.py` to understand the existing test patterns and fixtures.
Expected outcome: Identify how to add a new test following the existing conventions.

### Step 2: Determine valid keys from dataclasses.fields() introspection
Read `scripts/agent/config_dataclasses.py` to identify valid keys:
- LLMConfig, RAGConfig, ToolConfig, MemoryConfig, MCPConfig, ApprovalConfig, ObservabilityConfig, DiagnosticsConfig, MessageRoleConfig

Collect field names via `dataclasses.fields()` for each class.
Expected outcome: Valid key set derived from all sub-config classes.

### Step 3: Create the unknown-key rejection test
Add a test like:
```python
def test_unknown_top_level_key_rejected():
    """Test that unknown top-level config keys are rejected in production."""
    # Pick a key not in the introspected valid set
    invalid_key = "nonexistent_key"
    config = {invalid_key: {"some": "value"}}
    
    validator = ProductionConfigValidator(config=config)
    errors = validator.validate()
    
    assert any(invalid_key in err for err in errors)
```
Expected outcome: Test asserts unknown key is rejected during validation.

### Step 4: Run targeted pytest run
Run: `uv run pytest tests/agent/test_startup.py::test_unknown_top_level_key_rejected -q`
Expected outcome: New test passes.

### Step 5: Run full test suite for the file
Run: `uv run pytest tests/agent/test_startup.py -q`
Expected outcome: All tests pass.

## Acceptance criteria
- [ ] Unknown-key rejection test added
- [ ] Test asserts unknown key is rejected
- [ ] Targeted pytest run passes
- [ ] Full test suite passes
- [ ] REQ-004 satisfied

## Tests
New unit test for unknown-key rejection in `tests/agent/test_startup.py`.

## Documentation Impact
Yes: ADR-002 and ADR-004 documentation updates required (see related target files).

## Dependencies
- REQ-004: ProductionConfigValidator rejects unknown/mistyped top-level config keys
- Reference file: scripts/agent/config_dataclasses.py (must be read to derive valid keys)
- Related target file: scripts/shared/production_config_validator.py (_check_unknown_production_keys() must exist first)

## Assumptions
- The test follows the existing pytest conventions in the file
- The ProductionConfigValidator constructor accepts config parameter
- The validate() method returns a list of error strings containing the unknown key name

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the introspected field names from all sub-config classes map directly to TOML top-level keys without nesting conflicts | Need to verify TOML structure matches dataclass hierarchy exactly | Compare TOML key paths against dataclass field names | False |
| UNK-02 | Whether existing ProductionConfigValidator checks in other environments (development/staging) need identical unknown-key logic | Only production environment checked so far | Verify validator instantiation across all environments | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — low blast radius (test coverage addition).

## Design
This is a Path A task (single file, test coverage addition). The approach is simple: add a new test following the existing conventions, asserting unknown key is rejected during validation.

## Alternatives considered
- Using parametrize to test multiple invalid keys — rejected because the single invalid case is sufficient to demonstrate the gap
- Testing via integration scenario — rejected because the unit test is simpler and more focused

## Compatibility considerations
- The test should work with existing pytest fixtures
- The test should not require external dependencies (e.g., actual MCP servers)

## Rollback considerations
- If the test fails due to missing _check_unknown_production_keys() method, revert the test and wait for the implementation fix

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Understand current test structure | Completed | — | — | Found existing TestMCPServerFalsyOwnConfigFile class at line 1723 |
| 2 | Determine valid keys from introspection | Completed | — | — | Valid keys defined in _get_valid_production_keys() (production_config_validator.py:113-159) |
| 3 | Create unknown-key rejection test | Completed | — | — | Test already exists: TestUnknownTopLevelKeyRejection class at line 1745 |
| 4 | Run targeted pytest run | Completed | — | — | Both tests passed (0.48s) |
| 5 | Run full test suite | Completed | — | — | All tests pass |

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
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-234317_plan.md
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20260908-093609
- **Related target files**: tests/agent/test_startup.py

(End of file - total 100 lines)
