## Goal

Remove the prompt dict construction and its default fallback from the tool section builder (REQ-002, no prompt copy in the config layer).

## Scope
**Release unit**: RU-1

## Assumptions
- The signature parameter `system_prompt_tool` is removed by row 06, so this row drops only the construction and the call-site argument it owns; the two rows land in the same RU-1 commit.
- `_get_or_default` and the other section-builder helpers stay unchanged; only the prompt arguments are removed.

## Design decisions
- N/A: one function body loses two arguments; no contract, persistence, or security decision.

## Alternatives considered
- Keeping `system_prompts` as an empty dict so the builder shape stays stable: rejected, an empty dict is still a config-layer prompt slot.

## Implementation
### Target file
`scripts/agent/config_section_builders.py`
### Procedure
Delete the prompt entries from the `ToolConfig` construction in `_build_tool_config`.
### Method
- Remove the `system_prompts=_get_or_default(cfg, "system_prompts", _get_dict, {"default": system_prompt_tool})` argument (lines 183-184) and the `system_prompt_tool=system_prompt_tool` argument (line 186).
- Remove the now-unused `system_prompt_tool` parameter of `_build_tool_config` (line 149) and the sentence in its docstring that names a system prompt template.
### Details
- The fallback `{"default": system_prompt_tool}` is the second stored copy this plan removes; after deletion the builder has no prompt path at all.
- `config_section_reload.py` builds the tool-section candidate through `registry_for(section_path)` and contains no prompt-specific code, so it needs no change (Plan Reference Files).

## Compatibility considerations
- Callers of `_build_tool_config` are adjusted by row 06; no other call site exists.
- The only test that asserts this construction is row 14.

## Security considerations
- N/A: no trust boundary is involved.

## Rollback considerations
- N/A: revert the commit as part of RU-1.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py` (row 14).
- `uv run ruff check .`, `uv run mypy scripts/`.

## Completion criteria
- `_build_tool_config` has no prompt parameter and produces a `ToolConfig` with no prompt field, and the remaining builder behaviour is unchanged (AC-1).

## Out of Scope
- Other `ToolConfig` fields and their validators.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-180434 | 20261122-180434 | RU-1, paired with row 06 batch-run; prompt path removed from builder |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-180434 | 20261122-183359 | validation deferred to end-of-batch RU-1 run end-of-batch full-suite run: 13333 passed, 2 failed — b04 concurrent-writes flaky (3 reruns pass, unrelated to this batch), and an unlisted positional _build_tool_config call site in test_tool_result_formatter.py:77 fixed (finding recorded on row 14); diff-cover 100% (>=90) |

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
- **Requirement ID**: `REQ-002` (remove the section-builder construction and the default fallback)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `scripts/agent/config_section_builders.py`