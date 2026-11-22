## Goal
Remove the two prompt fields from `ToolConfig` so the config layer holds no stored prompt copy (REQ-002, single-function row).
## Scope
**Release unit**: RU-1

## Assumptions
- Cross-plan overlap with `plans/20261121-172154_mcpdl003_dedup-config-isolation.md` on this row is judged compatible, not a conflict: that plan adds an approval-grant field here, this row removes the prompt fields, and the edits do not touch the same lines.
- The fields have no consumer after rows 05, 06, 10 and 11 land, so no replacement field is introduced.
- `tests/agent/test_config_dataclasses.py` has no prompt-field reference (Plan Reference Files); the only test change is row 14.
## Design decisions
- N/A: field deletion only; the remaining `ToolConfig` fields keep their defaults and validation.
## Alternatives considered
- Keeping the fields as read-only views of the single source: rejected, that reintroduces a stored copy and contradicts REQ-002.

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`
### Procedure
Delete the `system_prompts` and `system_prompt_tool` field declarations (lines 194-195); no comment, no rename, no default replacement.

## Compatibility considerations
- `production_config_validator.py` derives valid keys from the dataclass fields, so removing them makes the two keys unknown, which is the behaviour row 09 makes explicit.
## Security considerations
- N/A: no trust boundary is involved.
## Rollback considerations
- N/A: revert the commit; RU-1 is reverted as a unit with rows 05, 06, 07, 09 and 14-17.
## Validation plan
- `uv run pytest tests/agent/test_config_builders.py` (row 14); `uv run ruff check .`, `uv run mypy scripts/`, `uv run lint-imports`.
## Completion criteria
- `ToolConfig` has no prompt field and no prompt content is reachable from the config layer (AC-1).
## Out of Scope
- Any other `ToolConfig` field, including the two registered-but-absent fields reported to `agentcfg006` (Plan UNK-05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure | Completed | 20261122-180355 | 20261122-180355 | RU-1 fields deleted at batch-run; consumer updates land in rows 05/06/10/11 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-180355 | 20261122-183359 | validation deferred to end-of-batch RU-1 run (row 14 tests) end-of-batch full-suite run: 13333 passed, 2 failed — b04 concurrent-writes flaky (3 reruns pass, unrelated to this batch), and an unlisted positional _build_tool_config call site in test_tool_result_formatter.py:77 fixed (finding recorded on row 14); diff-cover 100% (>=90) |

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
- **Requirement ID**: `REQ-002` (remove the config-layer prompt fields)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `scripts/agent/config_dataclasses.py`