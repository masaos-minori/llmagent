# Known Issue: INV-03 lacks explicit test coverage

## Summary

ADR-001 INV-03 states "実行成功と検証成功は区別され、それぞれ独立して検証される" (execution success and verification success are distinguished and independently verified). While the implementation correctly separates plan→execute→verify stages in workflow_engine.py:130-158, there is no explicit test verifying this separation.

## Details

| Field | Value |
|-------|-------|
| ID | WF-002 |
| Status | Open |
| Severity | Medium |
| Area | Workflow engine testing |
| Related ADR | ADR-001-workflow-engine-mandatory |
| Conflicting Source | scripts/agent/workflow/workflow_engine.py:130-158 |
| Expected Design | INV-03: "実行成功と検証成功は区別され、それぞれ独立して検証される" |
| Observed Implementation | The run() method executes plan (line 145), execute (line 146), optional approval gate (lines 147-148), then verify (line 149). Failure at any stage updates task status accordingly (halted/failed/completed). However, no test explicitly verifies that execution success does NOT imply verification success. |
| Impact | Without explicit test coverage, regression could reintroduce conflation of execution and verification outcomes. |
| Recommended Action | Add a test case that verifies: (1) execution succeeds but verification fails results in task status "failed"; (2) execution fails but would succeed if re-executed after fix results in task status "completed". |
| Owner | TBD |
| Resolution Target | Next sprint |
