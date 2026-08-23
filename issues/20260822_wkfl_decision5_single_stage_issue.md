# Known Issue: Decision #5 — single-stage workflow for simple Q&A not implemented

## Summary

ADR-001 Decision #5 states that simple Q&A workflows should be handled as a lightweight single-stage workflow. The current implementation only supports the full three-stage workflow (plan → execute → [approval] → verify) via default.json. There is no mechanism for a single-stage workflow.

## Details

| Field | Value |
|-------|-------|
| ID | WF-003 |
| Status | Open |
| Severity | Medium |
| Area | Workflow engine design |
| Related ADR | ADR-001-workflow-engine-mandatory |
| Conflicting Source | docs/adr/ADR-001-workflow-engine-mandatory.md:155-157, config/workflows/default.json |
| Expected Design | Decision #5: "シンプルなQ&Aワークフローは軽量な単一ステージWorkflowで処理する" |
| Observed Implementation | Only one workflow config exists: config/workflows/default.json with plan/execute/verify stages. The WorkflowEngine.run() method requires all four callbacks (plan_fn, execute_fn, verify_fn). No single-stage workflow variant exists. |
| Impact | Simple Q&A scenarios must go through unnecessary plan/verify overhead. The design intent from Decision #5 is not realized. |
| Recommended Action | Either implement single-stage workflow support (add conditional stage execution in WorkflowEngine.run()) or update ADR-001 Decision #5 to reflect that this optimization is deferred. |
| Owner | TBD |
| Resolution Target | Next planning cycle |
