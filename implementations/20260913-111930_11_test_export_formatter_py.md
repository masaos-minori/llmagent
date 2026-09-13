## Goal

Create tests for `ExportOutputPort` to `OutputPort` transition in export_formatter.py.

## Scope

- New file: Create `tests/test_export_formatter.py` — Tests for ExportOutputPort to OutputPort transition

## Assumptions

- These test files do not exist yet and need to be created during implementation
- After merge, `ExportOutputPort` Protocol is subsumed into unified `OutputPort` Protocol (handled in output_port.py document)
- `_CliExportOutput` class is replaced by `CliOutputPort` injection (handled in export_formatter.py document)
- Test structure follows the project convention (pytest fixtures, assertions, etc.)

## Design decisions

- Tests should verify that `export_formatter.py` works with `OutputPort` protocol injection
- Mock `OutputPort` replaces `ExportOutputPort` mock in test fixtures
- T-003: Verify `export_formatter.py` works with `OutputPort` protocol injection

## Alternatives considered

- Keeping separate test expectations for `ExportOutputPort`: rejected because it perpetuates the separation being consolidated
- Merging into an existing test file: rejected because test structure should follow production code structure — export formatter tests belong with export formatter

## Implementation
### Target file
tests/test_export_formatter.py

### Procedure
Create tests for ExportOutputPort to OutputPort transition

### Method
1. Create test file following project conventions (pytest fixtures, assertions)
2. Define mock `OutputPort` instance covering all merged methods
3. Write tests verifying export functionality works with `OutputPort` injection:
   - Verify `write_export()` accepts `OutputPort` parameter
   - Verify export output goes through `OutputPort` methods
   - Verify no `sys.stdout.write()` calls during export
4. Verify T-003: `export_formatter.py` works with `OutputPort` protocol injection

### Details
- **test_export_formatter.py** (new):
  - Follow pytest conventions: use `@pytest.fixture`, `MagicMock(spec=OutputPort)`
  - Import `OutputPort` from `scripts.agent.commands.output_port`
  - Write parametrized tests for export functionality
  - Verify `write_export()` uses `OutputPort` instead of `_CliExportOutput`
  - Ensure all existing test assertions pass with unified Protocol

## Compatibility considerations

- `ExportOutputPort` Protocol is being merged into unified `OutputPort` (handled in output_port.py document)
- `_CliExportOutput` class is being replaced by `CliOutputPort` (handled in export_formatter.py document)
- Export feature functionality must remain unchanged — only I/O backend changes
- Visual output format must remain identical to pre-refactor (REQ-009)

## Security considerations

N/A: This is a test creation with no security-relevant changes.

## Rollback considerations

- If test failures occur after creation, revert individual test method changes
- Can selectively roll back specific test cases while keeping others migrated
- Incremental rollback possible per-phase since each phase leaves codebase in working state

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| tests/test_export_formatter.py | Unit — I/O backend swap | `uv run pytest tests/test_export_formatter.py` | Export works without sys.stdout.write |

## Completion criteria

- [ ] Tests verify `export_formatter.py` works with `OutputPort` protocol injection
- [ ] `OutputPort` mock replaces `ExportOutputPort` mock in test fixtures
- [ ] Test assertions check against `OutputPort` method calls
- [ ] Fixture setup uses `CliOutputPort` instead of `_CliExportOutput`
- [ ] All existing tests pass after refactor

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260718-114608_agent_output_format_inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-093547_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-111930
- **Related target files**: tests/test_export_formatter.py
