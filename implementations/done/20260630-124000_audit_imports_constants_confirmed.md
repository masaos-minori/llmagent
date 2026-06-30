## Goal
- Confirm audit-specific imports/constants removal from cmd_debug.py is already complete

## Findings
- `grep -n "pathlib\|_AUDIT_TAIL_LINES" scripts/agent/commands/cmd_debug.py` → no matches

## Conclusion
No changes needed — already completed.
