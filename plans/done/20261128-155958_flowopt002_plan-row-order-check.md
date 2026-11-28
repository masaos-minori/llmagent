## Goal
- Make the row order of a Plan's `Implementation Target Files` table carry the implementation sequence: state the ordering rule in `templates/plan.md` and add a Step 8a row-order check to `skills/issue-to-plan/workflow.md`, so a frozen Plan cannot silently encode a wrong implementation order.

## Priority
Medium

## Scope
- **In-Scope**: `templates/plan.md` row-order rule text (three additions inside existing sections) and a Step 8a row-order check bullet in `skills/issue-to-plan/workflow.md`; text-only edits.
- **Out-of-Scope**: a mechanical row-order checker tool or test (the Issue states the order is not checked mechanically and leaves mechanical checking as an open question); reordering rows of existing or archived plans; raising the ceiling in `tools/check_skill_size_baseline.txt`.
- **Dependencies**: flowopt001 (archived Issue and Plan) touches the same two files in an earlier, completed pipeline phase; either order works, so no ordering dependency. No active plan targets either file (Step 6 scan of `plans/*.md` returned no rows for `templates/plan.md` or `skills/issue-to-plan/workflow.md`).

## Background
- The pipeline already derives implementation order from table position: `skills/plan-to-implementation-procedure/workflow.md` "Workflow position" sets `seq` to the row's 1-indexed, zero-padded position in the Plan's `Implementation Target Files` table; `tools/generate_workitem.py` iterates the table "in row order"; `skills/code-implementation/workflow.md` Step 1 iterates plan steps in ascending order, which it calls the Plan's implementation order.
- The flowopt batch review (2026-11-27) raised this Issue (flowopt002) after flowopt001 (`issues/done/20261127-120059_flowopt001_skill-size-fallout-check.md`, plan `plans/done/20261127-151623_flowopt001_skill-size-fallout-check.md`) made `templates/plan.md` and `skills/issue-to-plan/workflow.md` size-constrained; the Issue lists flowopt001 as related with either order acceptable, and flowopt001 is already archived.

## Problem
- `templates/plan.md` states no rule about `Implementation Target Files` row order, and no Step 8 check validates it (grep over `templates/plan.md`, `skills/issue-to-plan/`, `skills/code-implementation/workflow.md`, and `rules/workflow-lifecycle.md` finds no row-order statement). A misordered frozen table therefore silently produces misnumbered procedure files (`seq`) and a wrong execution order downstream.

## Reason for Change
- The frozen table is the canonical source of implementation scope; row order is its last unvalidated property, and the fix is two bounded text edits in files the next flowopt batch items already touch.

## Implementation Intent
- Add the ordering rule as prose to the existing `Implementation Target Files` section rules and the `Implementation steps` / `Dependencies` guidance of `templates/plan.md`, and add one Step 8a validation bullet to `skills/issue-to-plan/workflow.md`. No new sections, headings, tools, or tests.

## Requirements
- `REQ-001`: `templates/plan.md` states that `Implementation Target Files` rows are ordered by implementation sequence, that `Implementation steps` cites rows in that order, and that canonical implementation order lives in this table (the `Dependencies` bullet in `Scope` defers to it).
- `REQ-002`: `skills/issue-to-plan/workflow.md` Step 8 gains a row-order check bullet: reject a table marked `Frozen` whose `Implementation steps` citations do not match the 1-indexed row order.
- `REQ-003`: Heading sets and section names of both files stay unchanged, and both files stay within their `tools/check_skill_size.py` ceilings after the edits (`wc -c` measured before and after each file).

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b: every row `Verified`; `tools/audit_plan_target_paths.py`, `tools/check_plan_target_overlaps.py`, `tools/backtick_plan_related_tests.py`, and `tools/check_workitem_structure.py` passed)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `templates/plan.md` | Add the row-order rule to the `Implementation Target Files` section rules, the `Implementation steps` note, and the `Dependencies` bullet note in `Scope`; text-only edit inside existing sections. | The table lacks any row-order statement, yet downstream phases derive order from it. | `REQ-001`; `AC-1`, `AC-3` | `templates/plan.md` 12596 B, ceiling 20480 B, headroom 7884 B (`tools/check_skill_size.py --headroom`); no row-order statement found by grep over `templates/plan.md`, `skills/issue-to-plan/`, `skills/code-implementation/workflow.md`, `rules/workflow-lifecycle.md` | `tests/tools/test_check_workitem_structure.py` (heading-set comparison against `templates/plan.md`) | Verified |
| `skills/issue-to-plan/workflow.md` | Add one Step 8a row-order check bullet to the Step 8 validation list; text-only edit. | Step 8 validates paths, overlaps, evidence, and structure but not row order, so an out-of-order table can be frozen. | `REQ-002`; `AC-2`, `AC-3` | Step 8 validation bullet list in `skills/issue-to-plan/workflow.md`; file 42152 B, ceiling 42533 B (`tools/check_skill_size_baseline.txt`), headroom 381 B | `tests/tools/test_check_workitem_structure.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `skills/plan-to-implementation-procedure/workflow.md` | Its "Workflow position" `seq` derivation is the consumer that makes row order load-bearing; wording of the new rule must match it. | `REQ-001` |
| `skills/code-implementation/workflow.md` | Consumes the Plan's implementation order (ascending step iteration); confirms the rule's downstream meaning. | `REQ-001` |
| `tools/check_skill_size_baseline.txt` | Pins the 42533 B ceiling for `skills/issue-to-plan/workflow.md`; the new bullet must fit under it. | `REQ-003` |
| `skills/issue-to-plan/workflow-edge.md` | Overflow destination if the Step 8a bullet does not fit the headroom (Step 9 fallout path). | `REQ-002`, `REQ-003` |

## Acceptance Criteria
- `AC-1` (`REQ-001`): `templates/plan.md` states the row-order rule, the row-order-citation note in `Implementation steps`, and the `Dependencies` bullet deferral in `Scope`; heading set unchanged.
- `AC-2` (`REQ-002`): `skills/issue-to-plan/workflow.md` Step 8 contains a row-order check bullet that rejects out-of-order `Frozen` tables.
- `AC-3` (`REQ-003`): after the edits, `uv run python tools/check_skill_size.py --headroom templates/plan.md skills/issue-to-plan/workflow.md` reports both files under ceiling, `uv run python tools/check_skills_references.py` reports 0 missing references, `uv run python tools/check_skills_heading_cycles.py` passes, and `uv run python tools/check_workitem_structure.py --related templates/plan.md` passes.

## Tests
- `REQ-001`, `REQ-003`: `uv run pytest tests/tools/test_check_workitem_structure.py -q` passes after the edits (heading sets and structure of `templates/plan.md` and Plans remain valid); `uv run python tools/check_workitem_structure.py --file plans/20261128-155958_flowopt002_plan-row-order-check.md` passes.
- `REQ-002`, `REQ-003`: `uv run python tools/check_skill_size.py --headroom templates/plan.md skills/issue-to-plan/workflow.md` exits 0 with both files under ceiling; `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` pass.

## Documentation Impact
N/A: no `docs/*.md` change. The edits are instruction text in `templates/` and `skills/`, carried by this Plan's procedure documents.

## Assumptions
- The 381 B headroom of `skills/issue-to-plan/workflow.md` fits one short Step 8a bullet (~150-250 B); if the measured growth exceeds it, the implementation phase moves the explanation into `skills/issue-to-plan/workflow-edge.md` (Step 9 skill-size fallout) rather than raising the baseline.
- Enforcement stays AI-executed (the Step 8a workflow bullet); no new checker tool, per the Issue Constraints ("Do not add a checker in this issue").
- `deploy/` is unaffected: `deploy/deploy.sh` rsyncs `scripts/`, `registry/`, `tests/`, and `docs/`, never `templates/` or `skills/`, so `templates/` and `skills/` changes need no deploy.sh row.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the row order of `Implementation Target Files` can be checked mechanically (the Issue leaves this open). | No evaluation of a checker extension for `tools/check_workitem_structure.py` exists. | Decide in a follow-up Issue after the rule text lands; out of scope for this Plan by the Issue Constraints. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `templates/plan.md` | Modify | Medium | 8 | High (100% single author) | not applicable (not rsynced) |
| `skills/issue-to-plan/workflow.md` | Modify | Medium | 16 | High (98% single author) | not applicable (not rsynced) |

## Design
- Consumers of row order: `skills/plan-to-implementation-procedure/workflow.md` `seq` derivation (lines 9-15), `tools/generate_workitem.py` row iteration ("in row order"), and `skills/code-implementation/workflow.md` ascending step execution (line 89). The rule must be stated where writers read it: the `Implementation Target Files` rules and `Implementation steps` sections of `templates/plan.md`.
- Predictable fallout check (`skills/issue-to-plan/workflow-edge.md` Step 3, Skill size item): both target files are covered instruction files gaining text. Measured at HEAD `d8ad1a194e1bfa042ff6b2b51547759da1211a72`: `templates/plan.md` 12596 B / ceiling 20480 B / headroom 7884 B (default limit); `skills/issue-to-plan/workflow.md` 42152 B / ceiling 42533 B (baseline) / headroom 381 B. Module size, pinned counts, tool inventory, generated blocks: not affected (no code, tool, or generated-block change).
- Heading-set coupling: `tools/check_workitem_structure.py` compares Plan heading sets against `templates/plan.md`; all additions go inside existing sections, so no heading changes.

## Implementation steps
1. **Phase 1: Template rule text**
   - [ ] Measure `wc -c templates/plan.md` (before). Edit `templates/plan.md`: add the row-order rule to the `Implementation Target Files` rules, the `Implementation steps` citation note, and the `Dependencies` deferral note; re-measure `wc -c` (after). (REQ-001; `templates/plan.md`)
2. **Phase 2: Workflow check**
   - [ ] Measure `wc -c skills/issue-to-plan/workflow.md` (before). Add the Step 8a row-order check bullet; re-measure and confirm the file stays at or under 42533 B; on overflow move explanatory text to `skills/issue-to-plan/workflow-edge.md`. (REQ-002, REQ-003; `skills/issue-to-plan/workflow.md`)
3. **Phase 3: Verification**
   - [ ] Run the Validation plan commands (gate tools, related tests, full pytest suite). Deployment validation: N/A — no `scripts/` or `config/` change, so `deploy/deploy.sh` needs no update (`rules/env.md` rsync contract). (REQ-003; `templates/plan.md`, `skills/issue-to-plan/workflow.md`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `templates/plan.md` | Gate + regression | `uv run python tools/check_skill_size.py --headroom templates/plan.md`; `uv run python tools/check_workitem_structure.py --file plans/20261128-155958_flowopt002_plan-row-order-check.md`; `uv run python tools/check_workitem_structure.py --related templates/plan.md` | Under 20480 B; structure and heading comparison pass |
| `skills/issue-to-plan/workflow.md` | Gate | `uv run python tools/check_skill_size.py --headroom skills/issue-to-plan/workflow.md`; `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | At or under 42533 B; 0 missing references; no heading cycles |
| Both | Full suite | `uv run pytest -q -n auto --dist loadscope --durations-path tools/pytest_durations.json` | No new failures against the known-failure baseline |

## Risks
- **Risk**: the Step 8a bullet pushes `skills/issue-to-plan/workflow.md` past its 42533 B ceiling. → **Mitigation**: measure `wc -c` before and after (Issue Constraints); on overflow move explanatory text to `skills/issue-to-plan/workflow-edge.md` (Phase 2 branch).
- **Risk**: template wording changes break downstream heading comparisons or repeated-procedure tools. → **Mitigation**: text-only edits inside existing sections; `tools/check_workitem_structure.py`, `tools/check_skills_references.py`, and `tools/check_skills_heading_cycles.py` run in Phase 3.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the row-order rule text (`templates/plan.md`) | In Progress | — | — |  |
| 2 | Add the Step 8a row-order check (`skills/issue-to-plan/workflow.md`) | In Progress | — | — |  |
| 3 | Run gate tools, related tests, and full suite; deployment N/A | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261128-161650_01_templates_plan.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261128-161650_02_skills_issue-to-plan_workflow.md.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261127-120100_flowopt002_plan-row-order-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261128-155958
- **Evidence revision**: d8ad1a194e1bfa042ff6b2b51547759da1211a72
- **Related target files**: `templates/plan.md`, `skills/issue-to-plan/workflow.md` — the full list of `File Path` values from
  `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | `## Problem`; `## Requirements` | `templates/plan.md` | 1 | AC-1 | `tests/tools/test_check_workitem_structure.py` | Planned |
| REQ-002 | `## Problem`; `## Requirements` | `skills/issue-to-plan/workflow.md` | 2 | AC-2 | `tools/check_skill_size.py` | Planned |
| REQ-003 | `## Constraints` | `templates/plan.md` | 1,3 | AC-3 | `tools/check_skill_size.py`; `tests/tools/test_check_workitem_structure.py` | Planned |
| REQ-003 | `## Constraints` | `skills/issue-to-plan/workflow.md` | 2,3 | AC-3 | `tools/check_skill_size.py` | Planned |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261128-161650 -->