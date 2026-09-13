## Goal

Replace `sys.stdout.write()` in export_formatter.py with `OutputPort` protocol injection, replacing `_CliExportOutput` with `CliOutputPort`.

## Scope

- Modify `scripts/agent/services/export_formatter.py`: Replace `_CliExportOutput` class with `CliOutputPort` injection; remove `sys.stdout.write()` calls

## Assumptions

- `_CliExportOutput` class (export_formatter.py:55-66) exists and uses `sys.stdout.write()` internally
- `write_export()` function (export_formatter.py:73) has default parameter `out: ExportOutputPort = _CliExportOutput()`
- `ExportOutputPort` Protocol (io_ports.py:13-18) will be merged into unified `OutputPort` Protocol
- All `write_export()` call sites use the default parameter or explicitly pass an `ExportOutputPort` instance

## Design decisions

- Replace `_CliExportOutput` class entirely — inject `CliOutputPort` directly instead of creating a separate export-specific output class
- Since `ExportOutputPort` Protocol is being merged into `OutputPort` (handled in output_port.py document), the type annotation should become `OutputPort`
- Default parameter changed from `_CliExportOutput()` to `CliOutputPort()`

## Alternatives considered

- Keeping `_CliExportOutput` but having it delegate to `CliOutputPort`: rejected because unnecessary indirection — `_CliExportOutput` exists solely to wrap `sys.stdout.write()`
- Using a factory pattern for export output: rejected because over-engineering — simple dependency injection suffices

## Implementation
### Target file
scripts/agent/services/export_formatter.py

### Procedure
Replace sys.stdout.write() with OutputPort protocol; replace _CliExportOutput with CliOutputPort injection

### Method
1. Read export_formatter.py lines 55-66 (_CliExportOutput class) and line 73 (write_export signature)
2. Read io_ports.py lines 13-18 (ExportOutputPort Protocol) for merge consideration
3. Replace `_CliExportOutput` class with `CliOutputPort` usage
4. Change `write_export()` default parameter from `_CliExportOutput()` to `CliOutputPort()`
5. Update type annotation from `ExportOutputPort` to `OutputPort`
6. Verify no remaining `sys.stdout.write()` calls in export_formatter.py
7. Search for additional `write_export(` call sites across the codebase to confirm none rely on `_CliExportOutput` internals

### Details
- **export_formatter.py**:
  - Remove `_CliExportOutput` class definition (lines 55-66)
  - Change `write_export(out: ExportOutputPort = _CliExportOutput())` to `write_export(out: OutputPort = CliOutputPort())`
  - Update any internal references from `_CliExportOutput` to `CliOutputPort`
  - Remove `import sys` if no longer needed (was used for `sys.stdout.write`)
  - Update imports: add `CliOutputPort` import, add `OutputPort` import

## Compatibility considerations

- `ExportOutputPort` Protocol is being merged into unified `OutputPort` (handled in output_port.py document)
- Any callers passing explicit `_CliExportOutput` instances will need updating to pass `CliOutputPort` or `OutputPort`
- Export feature functionality must remain unchanged — only I/O backend changes

## Security considerations

N/A: This is a structural consolidation with no security-relevant changes.

## Rollback considerations

- If export fails after I/O backend swap, revert `write_export()` default parameter to `_CliExportOutput()`
- `_CliExportOutput` class can be temporarily restored if needed for debugging
- Incremental rollback possible per-phase since each phase leaves codebase in working state

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/agent/services/export_formatter.py | Unit — I/O backend swap | `uv run pytest tests/agent/services/test_export_formatter.py` | Export works without sys.stdout.write |

## Completion criteria

- [ ] `_CliExportOutput` class removed from export_formatter.py
- [ ] `write_export()` uses `CliOutputPort` as default parameter
- [ ] Type annotation changed from `ExportOutputPort` to `OutputPort`
- [ ] No `sys.stdout.write()` calls remain in export_formatter.py
- [ ] Export feature works correctly with new I/O backend

## Out of scope

- Adding new output tags beyond what OutputTag currently provides
- Changing the REPL input layer or readline behavior
- Modifying workflow/validate.py's independent deployment CLI behavior
- Adding rich/console/ANSI support (plain text only constraint remains)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | _CliExportOutput removed, CliOutputPort injected |
| 2 | Add or update tests per Validation plan | Done | — | — | Tests pass without changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | All agent tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | No docs section mapped |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260718-114608_agent_output_format_inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-093547_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-111930
- **Related target files**: scripts/agent/services/export_formatter.py
