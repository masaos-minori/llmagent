# Reduce implementation-derived detail in docs/05_agent_07_*_cli-and-commands*.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-agent-review.md` to the CLI-and-commands chapter (11 files: reference, CLIView, command registry, purpose, REPL I/O, hot-reload, migration notes, and four slash-command sub-files): keep operational judgments about `/reload` scope, deprecated-command migration, and commonly-misunderstood behaviors; remove full argument tables and handler/mixin detail.

## Reason for Change
This chapter is the canonical source for CLI operational usage notes, but currently also carries full per-command argument tables, handler/mixin names, and readline/prompt-string implementation detail that adds no operational value and duplicates what `command_defs_list.py` already defines authoritatively.

## Implementation Intent
Keep this chapter as the canonical source for CLI operation and command-usage caveats (per `memo-doc-agent-review.md` §「章間の正本ルール」: CLI運用とコマンド利用上の注意 = `05_agent_07_cli-and-commands`). Old-command sub-command mapping tables may be dropped, but migration/deprecation judgment must remain.

## Target Files or Areas
- `docs/05_agent_07_01_cli-and-commands-cli-reference.md`
- `docs/05_agent_07_02_cli-and-commands-cliview.md`
- `docs/05_agent_07_03_cli-and-commands-command-registry.md`
- `docs/05_agent_07_04_cli-and-commands-purpose.md`
- `docs/05_agent_07_05_cli-and-commands-repl-io.md`
- `docs/05_agent_07_06_cli-and-commands-hot-reload.md`
- `docs/05_agent_07_07_cli-and-commands-migration-notes.md`
- `docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `docs/05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `docs/05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `docs/05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Required Changes
- Keep: what the CLI provides, the `CommandRegistry`/`CLIView`/REPL responsibility split, `/reload`'s reflected scope and what requires a restart, deprecated-command migration judgment, how `/mcp tools`/`/mcp status` are used operationally, where the command-list source of truth lives, and commonly-misunderstood behaviors (`/reload` does not reflect all settings, `/mcp status` shows currently-running server state only, `/diff` depends on current history).
- Remove or compress: full per-command argument tables, plain side-effect enumeration, handler names and mixin composition, readline/prompt-string UI implementation detail, full old-command sub-command mapping tables.
- Deprecated-command sections may drop the full sub-command table but must retain: deprecated status, whether a successor exists, and whether compatibility is provided.

## Acceptance Criteria
- All 11 files follow the standard template from `memo-doc-agent-review.md` §「修正後の章構成テンプレート」 where applicable.
- No full command-argument table or handler/mixin listing remains.
- Commonly-misunderstood-behavior notes (`/reload`, `/mcp status`, `/diff`) remain explicit.
- Deprecated-command judgment (status/successor/compatibility) is retained even where sub-command tables are dropped.

## Testing Expectations
Not required for behavior (documentation-only). Run `python tools/check_agent_docs_consistency.py` after editing — this includes the slash-command drift check against `command_defs_list.py`, which is the relevant regression risk when command detail is trimmed.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/05_agent_*.md` chapters.
- `command_defs_list.py` itself (code, not documentation).

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_07_cli-and-commands」 including its 注意 note on deprecated commands. Since `command_defs_list.py` is the argument-table source of truth, replace full argument tables with a pointer to it rather than re-transcribing. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_07_cli-and-commands」
- Generated at: 2026-08-05
