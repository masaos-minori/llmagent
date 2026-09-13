## Goal

Replace manual key-value formatting with `write_kv()` method from the unified `OutputPort` Protocol in cmd_config_display.py.

## Scope

- Modify `scripts/agent/commands/cmd_config_display.py`: Replace manual key-value formatting with `write_kv()` calls

## Assumptions

- cmd_config_display.py has approximately 59 lines of self._out.write() key-value formatting
- No existing `write_kv` or `write_table` usage in cmd_config_display.py (verified by rg search returning no results)
- `OutputPort.write_kv(pairs, key_width)` accepts list of (key, value) tuples and handles formatting

## Design decisions

- Replace manual `self._out.write(key + ": " + value)` patterns with `self._out.write_kv(pairs)` where pairs is a list of (key, value) tuples
- `write_kv()` already exists on `OutputPort` Protocol and handles alignment — reuse it rather than maintaining custom formatting logic
- The visual output format must remain identical to pre-refactor (REQ-009)

## Alternatives considered

- Keeping manual formatting but using `print()` instead of `self._out.write()`: rejected because it doesn't solve the fragmentation problem
- Creating a config-specific formatter: rejected because adds unnecessary complexity when `write_kv()` covers the need

## Implementation
### Target file
scripts/agent/commands/cmd_config_display.py

### Procedure
Replace manual key-value formatting with write_kv()

### Method
1. Read cmd_config_display.py to identify all manual key-value formatting patterns (approximately 59 lines of self._out.write())
2. Group related key-value pairs into lists of tuples for `write_kv()` calls
3. Replace sequential `self._out.write(f"{key}: {value}")` calls with single `self._out.write_kv([(key, value), ...])` calls
4. Verify key alignment and spacing match previous format
5. Remove any unused formatting helper methods

### Details
- **cmd_config_display.py**:
  - Identify all `self._out.write()` calls that produce key-value output
  - Group related key-value pairs into lists: `pairs = [("Key1", "Value1"), ("Key2", "Value2")]`
  - Replace sequential writes: `self._out.write_kv(pairs, key_width=22)` (matching default key_width of 22 from OutputPort.write_kv signature)
  - For sections with different key widths, adjust `key_width` parameter accordingly
  - Remove any unused formatting helper methods or local variables
  - Update imports if needed

## Compatibility considerations

- Visual output format must remain identical to pre-refactor (REQ-009) — verify column alignment, spacing, and content match
- Default `key_width=22` from `OutputPort.write_kv` signature should be verified against current manual formatting width
- Existing tests in tests/agent/commands/test_cmd_config_char.py may need updates for new method signatures

## Security considerations

N/A: This is a display formatting change with no security-relevant changes.

## Rollback considerations

- If key-value formatting breaks after replacement, restore manual `self._out.write()` calls individually
- Can selectively roll back specific sections while keeping others migrated
- Incremental rollback possible per-phase since each phase leaves codebase in working state

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/agent/commands/cmd_config_display.py | Integration — visual diff | Manual terminal comparison | Config display matches previous format |

## Completion criteria

- [ ] Manual key-value formatting replaced with `write_kv()` calls
- [ ] Key alignment and spacing match previous format exactly (visual diff)
- [ ] No remaining `self._out.write()` calls producing key-value output
- [ ] Config display output matches previous format exactly (visual diff)

## Out of scope

- Adding new output tags beyond what OutputTag currently provides
- Changing the REPL input layer or readline behavior
- Modifying workflow/validate.py's independent deployment CLI behavior
- Adding rich/console/ANSI support (plain text only constraint remains)

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260718-114608_agent_output_format_inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-093547_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-111930
- **Related target files**: scripts/agent/commands/cmd_config_display.py
