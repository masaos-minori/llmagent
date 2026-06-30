## Goal
- Document workflow approval recovery behavior covered by tests in CLI commands docs

## Findings
- Startup warning format in doc was outdated — actual format: `[workflow] Pending approval from previous session — task=<task_id> approval=<approval_id> reason=<reason>. Use /approve [reason] or /reject [reason].`
- Missing cross-session guarantee documentation (DB-lookup when ctx.turn.pending_approval_id is None)
- `test_cmd_workflow.py`: 5 tests pass including DB-lookup fallback tests ✓

## Changes Made
1. Updated Startup Recovery warning format in `docs/05_agent_07_cli-and-commands.md:L162` to match actual code output
2. Added cross-session guarantee paragraph after L167: DB-lookup when in-memory state absent, ctx.turn.pending_approval_task_id set after /approve
3. Updated /approve and /reject command table rows in `docs/05_agent_07_cli-and-commands.md:L149-L150` to note DB-lookup fallback when pending_approval_id is None

## Conclusion
Code and tests already complete. Documentation improvements applied.
