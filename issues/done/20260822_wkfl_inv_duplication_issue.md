# Known Issue: INV-01 and INV-05 are duplicates

## Summary

ADR-001 defines INV-01 and INV-05 as separate invariants, but they describe identical requirements: abort agent startup when the workflow definition file is missing or validation fails. This creates confusion about whether there are actually two distinct failure conditions or one.

## Details

| Field | Value |
|-------|-------|
| ID | WF-001 |
| Status | Open |
| Severity | Low |
| Area | ADR-001 documentation consistency |
| Related ADR | ADR-001-workflow-engine-mandatory |
| Conflicting Source | docs/adr/ADR-001-workflow-engine-mandatory.md:243, docs/adr/ADR-001-workflow-engine-mandatory.md:247 |
| Expected Design | INV-01: "ワークフロー定義ファイルが欠落している場合、Agentの起動を中止する。" INV-05: "ワークフロー定義ファイルの欠落または検証失敗時は起動を中止する。" |
| Observed Implementation | Both invariants reference the same startup check in startup.py:314-320 and orchestrator.py:178-183. The implementation treats them as one condition. |
| Impact | Documentation ambiguity; developers may assume INV-01 and INV-05 cover different failure modes when they do not. |
| Recommended Action | Merge INV-01 and INV-05 into a single invariant, or clarify the distinction between them (e.g., INV-01 covers missing file, INV-05 covers validation failure). |
| Owner | TBD |
| Resolution Target | Next ADR review cycle |
