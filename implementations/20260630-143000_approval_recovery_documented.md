## Goal
- Document workflow pending approval startup recovery semantics in operations docs

## Findings
- `startup.py` L184-207: `_recover_pending_approvals()` already emits warning with task_id and approval_id ✓
- `tests/test_startup.py`: Both required tests exist and pass (9 passed) ✓
- Docs: Missing "Workflow Pending Approval Recovery" section in `05_agent_10_operations-and-observability.md`

## Changes Made
- Added "Workflow Pending Approval Recovery" subsection to `docs/05_agent_10_operations-and-observability.md:L42-L53`:
  - When recovery occurs (startup, if ctx.workflow is not None)
  - What is recovered: latest global pending approval from workflow.sqlite via StateStore.find_latest_pending_approval()
  - Multi-session behavior: only one pending approval tracked at a time; latest record across all sessions restored
  - Startup warning format documented
  - How to inspect via sqlite3 documented

## Conclusion
Code and tests already complete. Documentation added.
