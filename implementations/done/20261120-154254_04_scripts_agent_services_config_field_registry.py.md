## Goal

Remove the `tool_definitions` config-field-registry row from `scripts/agent/services/config_field_registry.py` (`REQ-002`). Removing the row also makes a reintroduced `tool_definitions` key fail the unknown-key check (`REQ-008`).

## Scope
**Release unit**: static-catalog removal

## Assumptions
- The row is a single entry at line 82 (`ConfigFieldRegistry("tool_definitions", "tool", True)`); verified against current source.
- The registry drives the unknown-key rejection, so removing this row is what makes a reintroduced `tool_definitions` key fail (`REQ-008`).

## Design decisions
- Delete only the `tool_definitions` row; leave the neighboring `tool`-section rows intact.

## Alternatives considered
- Keep the row but mark it deprecated: rejected by `REQ-002`, which requires the registry entry gone so the key is unrecognized.

## Implementation
### Target file
`scripts/agent/services/config_field_registry.py`

### Procedure
Delete the `ConfigFieldRegistry("tool_definitions", "tool", True)` row (line 82).

### Method
Remove the single line; confirm the registry list still parses.

### Details
- Delete line 82.
- Confirm no other module references the `"tool_definitions"` registry key in a way that now breaks (the drift-check caller is replaced in `REQ-004`).

## Compatibility considerations
Backward incompatible by design (`REQ-002`, `REQ-008`): a `tool_definitions` key is now an unrecognized key and is rejected at parse time.

## Security considerations
Removes a recognized config key from the allowlist, reinforcing the fail-closed unknown-key policy.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Parse an `agent.toml` containing a reintroduced `tool_definitions` key and assert it is rejected; run the config-field-registry tests.

## Completion criteria
The registry list contains no `"tool_definitions"` entry and the module parses.

## Out of Scope
The dataclass field (`config_dataclasses.py`), the section builder (`config_section_builders.py`), the TOML blocks (`config/agent.toml`), tests, and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-200400 | 20261120-200400 | Deleted the `ConfigFieldRegistry("tool_definitions", "tool", True)` registry row (line 84; shifted from the assumed 82 after earlier edits) from `scripts/agent/services/config_field_registry.py`, between `system_prompts` and `allowed_tools`. Re-verified current line number. Module parses (`ast.parse` OK); grep for `tool_definitions` in the module returns none. Neighboring `tool`-section rows intact. |
| 2 | Add or update tests per Validation plan | Completed | 20261120-200400 | 20261120-200400 | The registry directly drives the classification test `tests/agent/services/test_config_reload.py::TestRegistryFieldClassification::test_tool_section_fields_are_classified_correctly`, which asserted the exact tool-section field set including `tool_definitions`. Removing the row made that assertion assert a false invariant (1 failure). Updated the expected set to drop `tool_definitions` (single line) — a direct, necessary regression update for _04 (no later procedure owns `test_config_reload.py`). All 72 tests in that file pass afterward. No new test file added (out of scope). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-200400 | 20261120-200400 | `registry_for("tool")` no longer yields `tool_definitions` (verified via import). Module parses. `test_config_reload.py` 72/72 pass. Note: `registry_for` is consumed only by `config_section_reload.py` (the reload path), which iterates registry entries and silently skips keys absent from the registry; the parse-time unknown-key rejection (REQ-008) is enforced elsewhere in the load pipeline, so a reintroduced `tool_definitions` key is unrecognized once this row is gone. `test_config_dataclasses.py` (75 items) still passes with the field removed by _02. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261120-200400 | 20261120-200400 | N/A: documentation is explicitly out of scope for this static-catalog-removal procedure. |

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
- **Requirement ID**: `REQ-002`, `REQ-008`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `scripts/agent/services/config_field_registry.py`
