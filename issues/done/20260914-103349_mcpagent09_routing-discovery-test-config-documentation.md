# Correct MCP routing, discovery, test, and configuration documentation

## Priority
Low

## Summary
Several non-functional wording defects across routing/discovery comments, `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` terminology, test names/assertions, and configuration documentation currently misdescribe current behavior; this issue corrects them in one documentation-only cleanup pass, performed after the functional issues in this batch (`mcpagent01`–`mcpagent08`) have stabilized behavior.

## Background
`docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` is the design document whose routing-authority terminology this issue reviews and, if needed, corrects against the (by then stabilized) runtime behavior established by the other issues in this batch.

## Problem
Docstrings/comments may state that static registry or configured tool names directly drive runtime routing, when live discovery is what actually builds the routing registry — those names are validation inputs, not routing inputs. Duplicate-finding severity documentation may not say duplicates are always fatal (per `mcpagent08`'s corrected policy). Retry-exhaustion tests may assert a generic exception rather than `TransportError` (per `mcpagent06`'s corrected behavior). `AgentConfig` documentation may report an outdated sub-configuration count, and some validation messages or `ToolDefinition` fields may reference incomplete/historical material.

## Reason for Change
Routing authority wording, discovery severity comments, strict-mode naming, test names, exception assertions, configuration counts, incomplete references, and unused metadata are documentation and maintenance defects that can be corrected in one non-functional cleanup after behavior is stabilized.

## Implementation Intent
Make code comments, tests, validation messages, and design documentation accurately describe current behavior without changing functional policy — this issue is a documentation/wording pass, not a behavior change.

## Target Files or Areas
- `scripts/shared/route_resolver.py`
- `scripts/shared/tool_registry.py`
- `scripts/agent/services/mcp_tool_discovery.py`
- `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`
- `tests/shared/test_tool_executor.py`
- `scripts/agent/config_dataclasses.py`
- `scripts/shared/config_validator.py`

## Required Changes
- State that live discovery builds the runtime registry used for routing.
- State that static registry and configured tool names are validation inputs, not runtime routing inputs.
- Correct duplicate-finding severity documentation to say duplicates are always fatal.
- Rename or remove resolver strict mode if it changes only error wording.
- Review related ADR terminology for ownership authority versus runtime routing authority.
- Rename retry-exhaustion tests to state that `TransportError` is raised.
- Replace generic exception assertions with `TransportError` assertions.
- Correct AgentConfig documentation from eight to nine sub-configurations (verify the current count before editing, since this batch's other issues may have changed it further).
- Replace incomplete semantic-cache issue references with current specification guidance or remove historical references.
- Remove unused future-reserved `ToolDefinition` fields, or document a current compatibility requirement and removal condition.
- Run spelling, lint, type, and documentation checks for modified files.

## Constraints
This issue should be implemented last among `mcpagent01`–`mcpagent09`, since several corrections (duplicate-severity wording, `TransportError` assertions) depend on those issues' behavior actually being implemented first — documenting an intended future state as current would itself be inaccurate.

## Acceptance Criteria
- Docstrings describe the same routing sources used by code.
- Severity documentation matches duplicate and strict-mode behavior.
- No wording implies that configuration tool names directly route calls.
- Test names and asserted exception types match runtime behavior.
- AgentConfig documentation reports the correct sub-configuration count.
- Validation messages contain actionable current references rather than ellipses.
- Unused metadata fields are removed or justified by a current requirement.

## Testing Expectations
Not required beyond running spelling, lint, type, and documentation checks for modified files — this is a documentation/wording correction, not a behavior change, so no new test coverage is expected; existing tests renamed per Required Changes must still pass.

## Documentation Impact
This issue's entire scope is documentation and wording correction across the files listed in Target Files or Areas, performed only after the referenced behavior (from `mcpagent01`, `mcpagent06`, `mcpagent08`, and any config-dataclass changes) is actually implemented and verified.

## Out of Scope
- Unrelated refactoring outside the design and implementation boundary described in this issue.
- Any functional/behavioral change — if a described correction would require a behavior change, file it as a separate issue instead of bundling it here.

## Dependencies
Depends on `mcpagent06` (HTTP retry/backoff, for the `TransportError` test-naming correction) and `mcpagent08` (duplicate-tool ownership, for the duplicate-severity wording correction) having landed. Should be sequenced after `mcpagent01`–`mcpagent08` generally, since it documents their resulting behavior.

## Unresolved Questions
The current (post-this-batch) count of `AgentConfig` sub-configurations should be verified at implementation time rather than assumed to be nine, since other issues in this batch may add or remove configuration sections. Non-blocking.

## AI Implementation Instruction
Do not start this issue until the functional issues it documents (`mcpagent06`, `mcpagent08`, and any others whose behavior it describes) have landed — verify the actual current behavior/count before writing documentation, rather than transcribing the source review's numbers unchanged. Keep changes wording/comment/test-name-only; if a described defect turns out to require an actual behavior change, stop and report it as a separate issue rather than expanding this one's scope.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-103349
- **Related target files**: scripts/shared/route_resolver.py, scripts/shared/tool_registry.py, scripts/agent/services/mcp_tool_discovery.py, docs/adr/ADR-003-runtime-tool-registry-routing-authority.md, tests/shared/test_tool_executor.py, scripts/agent/config_dataclasses.py, scripts/shared/config_validator.py
