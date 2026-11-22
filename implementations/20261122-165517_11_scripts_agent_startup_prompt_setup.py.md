## Goal

Read the initial prompt from the single source through the typed model, keeping the existing name lookup and memory injection (REQ-006, startup path).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The name lookup stays as it is today: `ctx.conv.system_prompt_name` with `default` as the fallback name; no setter and no selection command is added (Plan Out-of-Scope, UNK-04).
- Memory injection behaviour is unchanged: the injected snippets are appended to the prompt exactly as today.
- The prompt source is read through the typed model from row 03; this file must not parse the file or resolve the registry path itself.
- A missing source or missing `default` entry fails at the read boundary (REQ-001); startup reports the reader's error rather than falling back to a code default.

## Design decisions
- Startup and `/reload` use the same model instance shape, so the two paths cannot disagree about prompt content (AC-4).
- The runtime value stays the single place the prompt lives at runtime: `ctx.conv.system_prompt_content` is written here and read by `scripts/agent/conversation_state_manager.py` and `scripts/agent/services/session_restore.py`, which are not modified.

## Alternatives considered
- Keeping a code-level fallback string in the startup path: rejected, a silent default is the failure mode REQ-001 removes.
- Reading the prompt at each conversation turn instead of at startup: rejected, out of this plan's scope and changes runtime behaviour.

## Implementation
### Target file
`scripts/agent/startup_prompt_setup.py`
### Procedure
Replace the config-field read with the typed single-source read.
### Method
- In `setup_prompt()`, resolve the prompt content through the typed model from row 03 using `ctx.conv.system_prompt_name` (default `default`) instead of `ctx.cfg.tool.system_prompts` and `ctx.cfg.tool.system_prompt_tool` (lines 67-70).
- Keep the memory-injection block and the order of operations: resolve, inject, then write `ctx.conv.system_prompt_content` and `replace_history()` (line 122).
- No new state field, no new default.
### Details
- `scripts/agent/commands/cmd_context.py` line 75 only displays `ctx.conv.system_prompt_name`; unaffected.
- `scripts/agent/context.py` lines 106 and 109 keep the runtime fields; unchanged.

## Compatibility considerations
- The startup observable contract changes only in where prompt content comes from; the initial prompt text is identical because the values move unchanged to the single source.
- Tests that set `ctx.cfg.tool.system_prompts` as a fixture must switch to the typed source (rows 18, 19, 20, 21).

## Security considerations
- Fail-fast at startup: a missing source means startup reports the error at the read boundary, consistent with the existing fail-fast pattern for registry data files.

## Rollback considerations
- Reverting this row restores the config-field read and requires the config-layer fields, so revert with rows 03, 04, 05, 06 and 01 together.

## Validation plan
- `uv run pytest tests/agent/test_startup_prompt_setup.py tests/agent/test_startup.py` (rows 18, 19): prompt comes from the typed source, memory injection unchanged.
- `uv run ruff check .`, `uv run mypy scripts/`, `uv run lint-imports`.

## Completion criteria
- The initial prompt is identical to the current `default` prompt content, obtained only through the typed model, and memory injection still runs unchanged (AC-4).

## Out of Scope
- Prompt-name selection features (UNK-04).
- Any change to `ctx.conv` field definitions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | covered by rows 18, 19, 20, 21 |
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
- **Requirement ID**: `REQ-006` (startup builds the initial prompt from the single source through the typed model)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `scripts/agent/startup_prompt_setup.py`
