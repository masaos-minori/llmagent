## Goal
- Confirm /audit regression tests preserved after /debug audit removal is already complete

## Findings
- `tests/test_cmd_audit.py` exists with 20 tests — all passing
- TestAuditTail: 6 tests (default tail, custom N, empty file, file_not_found, oserror, invalid_n)
- TestAuditTurn: 6 tests (matching, no_match, missing task_id, file_not_found, oserror, non-JSON/empty lines)
- TestAuditTool: 4 tests (file_not_found, oserror, no_match, cap_at_50)
- TestAuditUnknownSubcommand: 1 test

## Conclusion
No changes needed — already completed.
