## Goal
Satisfy `REQ-002`: cross-reference the new Component Criticality Classification
subsection (seq 01) from ADR-004's `### Specifications`, and update the existing
Known Deviations bullet that states no such Specification exists.

## Scope
Modify exactly two locations in `docs/adr/ADR-004-environment-failure-handling-policy.md`:
`## Related Documents` → `### Specifications` (line 498-501), and the `## Known
Deviations` bullet at line 453. No other section (Decision, Rationale, Invariants) is
touched.

## Assumptions
- Edited in Japanese, matching this file's existing, wholly-Japanese language, per the
  Plan's `Assumptions` (internal-consistency choice, not a claim of general
  Output-language compliance — see Plan `Risks`).

## Design decisions
Minimal, additive edits: one new bullet under `### Specifications`, and a targeted
rewrite of the specific clause in the line-453 bullet that claims no Specification
exists — the rest of that bullet (the two "報告のみ" test-coverage gaps) is unrelated
to this row and is left untouched.

## Alternatives considered
N/A: this is a direct, minimal consequence of seq 01 landing (per Plan `Design`
section) — no architectural alternative applies.

## Implementation
### Target file
docs/adr/ADR-004-environment-failure-handling-policy.md

### Procedure
1. Add a bullet under `### Specifications` referencing the new subsection.
2. Rewrite the "コンポーネント単位の必須／非必須分類を記録する現行の承認済み
   Specificationも存在しない" clause in the line-453 Known Deviations bullet.

### Method
1. Locate `### Specifications` (line 498), currently:
   ```
   ### Specifications

   - [Turn Processing Flow](05_agent_03_03_turn-processing-flow-workflow-engine.md) — ワークフロー実行の詳細
   - [Deployment Guide](02_deployment.md) — デプロイメント時のワークフロー検証
   ```
   Add a third bullet:
   ```
   - [MCP Configuration / Approval / Observability](../05_agent_08_04_configuration-mcp-approval-obs.md#component-criticality-classification) — MCPサーバーの必須／非必須分類記録(Decision Group 3)
   ```
2. Locate line 453's bullet (starts "**報告のみ（Known Issue未登録）**"). It currently
   ends with the clause:
   ```
   また、コンポーネント単位の必須／非必須分類を記録する現行の承認済みSpecificationも存在しない（Decision #13が要求する分類記録の主体が未整備）。
   ```
   Replace that sentence with:
   ```
   コンポーネント単位の必須／非必須分類を記録するSpecificationは
   `05_agent_08_04_configuration-mcp-approval-obs.md`の
   Component Criticality Classification節に整備済み（Decision #13が要求する
   分類記録の主体を充足）。
   ```
   Leave the sentence's remaining content (the two "報告のみ" test-coverage gaps at
   the start of the bullet) unchanged — this row does not address those.
3. Also update the Completion Checklist line at (current) line 535, which reads
   "関係するSpecificationと矛盾していない（要再確認 — コンポーネント必須性分類を
   記録するSpecificationが現行では存在しない。Known Deviations参照）" — since that
   Specification now exists, remove the "要再確認" parenthetical or reword it to
   confirm no contradiction, consistent with the line-453 update.

### Details
Re-verified against current source (2026-09-02): line 453's clause and line 535's
Completion Checklist item are both still present and unresolved as the Plan
originally described (unlike the same file's separate `ADR-004-D1-profile-config-model-
still-present` bullet immediately above line 453, which a different, earlier Plan
already resolved — not to be confused with this row's target clause).

## Compatibility considerations
Documentation-only change; no code, schema, or runtime behavior affected.

## Security considerations
N/A: no security-relevant content in a Specifications cross-reference or a Known
Deviations wording update.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file. Rolling back
this row alone (without seq 01) would leave a dangling anchor link — if reverting,
revert both rows together.

## Validation plan
- `.venv/bin/python tools/check_docs_quality.py docs/adr/ADR-004-environment-failure-handling-policy.md` → no new issues.
- `.venv/bin/python tools/check_docs_structure.py docs/adr/ADR-004-environment-failure-handling-policy.md` → the new relative link to `../05_agent_08_04_configuration-mcp-approval-obs.md#component-criticality-classification` resolves (file and anchor exist after seq 01 lands).
- Manual: confirm the line-453 bullet no longer claims the Specification is absent, and the line-535 Completion Checklist item no longer flags this as needing reconfirmation.

## Completion criteria
`### Specifications` cites the new subsection; the line-453 Known Deviations clause
and the line-535 Completion Checklist item both reflect that the Specification now
exists.

## Out of scope
`docs/05_agent_08_04_configuration-mcp-approval-obs.md` — covered by its own
implementation procedure document (seq 01) for this same Plan, which must land first
(this row's new link target depends on it).

## Documentation
This file is itself the ADR being updated; no separate `docs/00_index.md` task-scope
mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add Specifications bullet | Pending | — | — | Depends on seq 01 landing first |
| 2 | Rewrite line-453 Known Deviations clause | Pending | — | — | |
| 3 | Update line-535 Completion Checklist item | Pending | — | — | |
| 4 | Run validation sequence | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (cross-reference new Specification, resolve stale Known Deviations claim)
- **Source issue**: `issues/20260831-192510_adr004_06_missing_component_criticality_specification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-103154_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-135510
- **Related target files**: `docs/adr/ADR-004-environment-failure-handling-policy.md`
