## Goal

Replace the prompt-key reload cases with single-source cases and update the tool-section expected field set (REQ-003, REQ-007, reload tests).

## Scope
**Release unit**: RU-1

## Assumptions
- Companion judgement: condition 2 fails — named in the `Related Tests` cell of two rows (07 and 10) — so it keeps its own document.
- The test cases must match the change-detection design recorded in row 10: a prompt change is detected by reading the single source through the typed model and comparing with `ctx.conv.system_prompt_content`, not by a `new_cfg` key.
- Unit level, no marker: these tests do not start subprocesses.

## Design decisions
- Keep the prepare/commit failure case as the contract test for AC-4: a prepare-phase failure must leave `ctx.cfg` and `ctx.conv` untouched, so the prompt assertion is written as a no-mutation assertion, not as a report-shape assertion.
- Assert the outcome report shape explicitly (`applied`, `needs_restart`, `skipped`, `startup_only`, `always_live`) so the prompt path cannot introduce a new category.
- The tool-section expected field set is an exact set assertion (lines 1149-1168), so removing the prompt names is a deliberate contract change recorded here, not a incidental fixture edit.

## Alternatives considered
- Asserting only that no prompt key appears in the config dict: rejected, that would not cover the commit-phase-only invariant.

## Implementation
### Target file
`tests/agent/services/test_config_reload.py`
### Procedure
Migrate the prompt cases to the single-source model and update the expected field set.
### Method
- Replace the `system_prompt_tool` input case (line 275) and the applied-change case (line 320) with cases that build the candidate through the typed model from row 03.
- Replace the `system_prompts={}` fixtures (lines 51, 101, 1081) with the typed-source fixture; remove the prompt-key assertion at line 931.
- Remove `system_prompt_tool` and `system_prompts` from the expected tool-section set (lines 1149-1168).
- Add a prepare-phase failure case: a source read error leaves `ctx.cfg` and `ctx.conv` unchanged and no prompt update is applied.
### Details
- Fixture helpers stay shared; only the prompt source of truth changes.

## Compatibility considerations
- The `/reload` command output and report shape are unchanged, so no command-contract test is affected.

## Security considerations
- N/A: no trust boundary beyond the read contract already covered by row 12.

## Rollback considerations
- N/A: revert the commit as part of RU-1.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py`
- `uv run ruff check tests/agent/services/test_config_reload.py`, `uv run mypy scripts/`
- `uv run python tools/check_mock_patch_targets.py` if any `patch("agent.prompt_source....")` target is added.

## Completion criteria
- The prompt case proves commit-phase-only application and no mutation on a prepare failure; the expected field set matches the registry after row 07; the outcome shape assertion passes unchanged (AC-2, AC-4).

## Out of Scope
- Typed staged reload and rollback (`cliplc005`).
- The classification test's fixture, covered by row 16.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | RU-1; design must match row 10 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (tool-section field set excludes the prompt names), `REQ-007` (prompt change applied only in the commit phase)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `tests/agent/services/test_config_reload.py`
