# `/stats` prints a hint pointing to the removed `/db rag consistency` command

Discovered while building `tools/check_agent_docs_consistency.py`
(`plans/20260717-094227_plan.md`, `requires/20260716_17_require.md`). This is
a real implementation defect, not a documentation error — the doc describing
it (`docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md:96`)
accurately reflects current code behavior.

## Problem

`scripts/agent/commands/cmd_config_stats.py:148`:

```python
"  Hint          : Run /db rag consistency for index integrity status"
```

`/db` was removed entirely (see `docs/05_agent_07_07_cli-and-commands-migration-notes.md`,
"`/db`コマンド(完全削除)"), and `/db rag consistency` specifically has
"後継コマンドなし" (no successor command) per that same migration table. `/stats`
still emits this hint whenever `rag_db_configured` is true, telling the user to
run a slash command that the REPL will reject as unrecognized.

## Reproduction

- Configure `rag_db_path` so `db.config.build_db_config()` succeeds (`rag_db_configured=True`).
- Run `/stats`.
- Observe the `Hint` line recommending `/db rag consistency`.
- Run `/db rag consistency` — rejected as an unknown command (`/db` is not in `_COMMANDS`).

## Why this wasn't fixed inline

Fixing the string requires a product decision, not just a mechanical edit:
either (a) remove the hint entirely (index-integrity status becomes
undiscoverable from `/stats`), or (b) point it at whatever the intended
replacement diagnostic path is — and no replacement was ever introduced for
this specific capability. Per this plan's scope ("do not resolve every
implementation mismatch found during triage inline — file as tracked issues
instead"), this is filed rather than silently patched.

## Recommended action

Decide on (a) or (b) above, then update the hint string and its test coverage
(`tests/` — grep for `"Run /db rag consistency"` or `rag_db_configured`) to
match.
