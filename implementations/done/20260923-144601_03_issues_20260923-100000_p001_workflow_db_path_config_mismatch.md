## Goal

Correct stale `tools/gen_deployment_reference.py` references in the archived issue document `issues/done/20260923-100000_p001_workflow_db_path_config_mismatch.md` to use the consolidated `tools/generate_reference_table.py --type deployment`, ensuring the issue document accurately reflects current tooling.

## Scope

- Update line 21: Change `tools/gen_deployment_reference.py` → `tools/generate_reference_table.py --type deployment`
- Update line 27: Change `tools/gen_deployment_reference.py` → `tools/generate_reference_table.py --type deployment`
- Update line 32: Change `tools/gen_deployment_reference.py` → `tools/generate_reference_table.py --type deployment`
- Update line 64: Change `tools/gen_deployment_reference.py` → `tools/generate_reference_table.py --type deployment`
- Update line 73: Change `tools/gen_deployment_reference.py` → `tools/generate_reference_table.py --type deployment`
- Verify REQ-001 acceptance criterion

## Assumptions

- The consolidation of `gen_deployment_reference.py` into `tools/generate_reference_table.py` was intentional and complete
- Archived issue documents should maintain accuracy — stale references can mislead future readers
- Updating an archived issue is appropriate when it contains incorrect tool references that affect downstream workflows

## Design decisions

- Minimal changes approach: only modify the five stale references identified in the plan
- Preserve all other content (Japanese text, structure, formatting) — only update tool references
- Note: This is an archived issue (`issues/done/`), so updates are informational rather than operational

## Alternatives considered

- Leaving the archived issue unchanged: rejected because stale references could mislead developers following the issue's instructions
- Creating a separate note documenting the correction: less effective than updating the source document directly

## Implementation

### Target file

`issues/done/20260923-100000_p001_workflow_db_path_config_mismatch.md`

### Procedure

1. Update line 21: Change `tools/gen_deployment_reference.py` → `tools/generate_reference_table.py --type deployment`
2. Update line 27: Change `tools/gen_deployment_reference.py` → `tools/generate_reference_table.py --type deployment`
3. Update line 32: Change `tools/gen_deployment_reference.py` → `tools/generate_reference_table.py --type deployment`
4. Update line 64: Change `tools/gen_deployment_reference.py` → `tools/generate_reference_table.py --type deployment`
5. Update line 73: Change `tools/gen_deployment_reference.py` → `tools/generate_reference_table.py --type deployment`

### Method

Use Edit tool to perform exact string replacements at the identified line numbers.

### Details

**Line 21 — Implementation Intent:**
- Current: `3. 自動生成スクリプト \`tools/gen_deployment_reference.py\` の出力ロジックを確認し、Python-level default のケースでも明確に表示されるようにする`
- Replace with: `3. 自動生成スクリプト \`tools/generate_reference_table.py --type deployment\` の出力ロジックを確認し、Python-level default のケースでも明確に表示されるようにする`

**Line 27 — Target Files or Areas:**
- Current: `- \`tools/gen_deployment_reference.py\``
- Replace with: `- \`tools/generate_reference_table.py --type deployment\``

**Line 32 — Required Changes:**
- Current: `- 必要に応じて \`tools/gen_deployment_reference.py\` の出力ロジックを修正`
- Replace with: `- 必要に応じて \`tools/generate_reference_table.py --type deployment\` の出力ロジックを修正`

**Line 64 — AI Implementation Instruction:**
- Current: `- 自動生成テーブルの表示を改善するには \`tools/gen_deployment_reference.py\` のロジック変更が必要な場合がある`
- Replace with: `- 自動生成テーブルの表示を改善するには \`tools/generate_reference_table.py --type deployment\` のロジック変更が必要な場合がある`

**Line 73 — Related target files:**
- Current: `- **Related target files**: docs/02_deployment.md, scripts/db/config.py, config/agent.toml, tools/gen_deployment_reference.py`
- Replace with: `- **Related target files**: docs/02_deployment.md, scripts/db/config.py, config/agent.toml, tools/generate_reference_table.py --type deployment`

## Compatibility considerations

- Future developers reading this archived issue will follow the correct tool reference
- No impact on active workflows since the issue is archived

## Security considerations

N/A: Only documentation changes in an archived issue document.

## Rollback considerations

- Revert all edits to restore original values if any unexpected side effects occur
- Document the rollback path in case of issues

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| issues/done/20260923-100000_p001_workflow_db_path_config_mismatch.md | Manual verification of content correctness | `grep 'gen_deployment_reference' issues/done/20260923-100000_p001_workflow_db_path_config_mismatch.md` | Zero matches after fix |
| Entire repository | Full-scan for stale references | `rg 'gen_deployment_reference'` | Zero matches after fix |

## Completion criteria

- [ ] All five instances of `tools/gen_deployment_reference.py` replaced with `tools/generate_reference_table.py --type deployment`
- [ ] `grep 'gen_deployment_reference' issues/done/20260923-100000_p001_workflow_db_path_config_mismatch.md` returns zero matches
- [ ] `rg 'gen_deployment_reference'` returns zero matches across entire repository

## Out of scope

- Modifying Japanese text or structural elements of the issue
- Updating other archived issues that may contain similar stale references
- Modifying the issue's Traceability section beyond the related target files field

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-152316 | 20260923-152316 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260923-152325 | 20260923-152325 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-152329 | 20260923-152329 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-152334 | 20260923-152334 |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260923-100000_p001_workflow_db_path_config_mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-142236_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-144601
- **Related target files**: issues/done/20260923-100000_p001_workflow_db_path_config_mismatch.md