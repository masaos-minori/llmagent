## Goal

`REQ-001`/`REQ-002`: re-record ADR-001 Known Deviations `WF-003` (Decision #5's
single-stage-workflow optimization, currently unimplemented) as a deliberate deferral,
backed by the investigation finding that `plan_fn`/`verify_fn` are already no-op-
equivalent for every turn type, not just simple Q&A.

## Scope

- **In-Scope**: edit the `### WF-003` entry (`docs/adr/ADR-001-workflow-engine-
  mandatory.md:410-421`) — append the `_handle_workflow_engine()` plan_fn/verify_fn
  investigation finding to `Observed Implementation`; update `Recommended Action` and
  `Resolution Target` to record the deferral decision; add one `## Change History` line.
- **Out-of-Scope**: `scripts/agent/workflow/workflow_engine.py`'s `WorkflowEngine.run()`
  (no conditional stage execution added — deferred, per this Requirement's own
  decision); `config/workflows/`; ADR-001 `## Decision` > Decision Details #5 body text
  (Known Deviations correction only, no Decision-body change, per ADR-001's own rule
  that Accepted Decisions are changed only via a new superseding ADR).

## Assumptions

- Confirmed via Read (`scripts/agent/workflow/workflow_engine.py:130-149`) that
  `WorkflowEngine.run()` unconditionally runs `plan`, `execute`, `verify` in fixed order
  via `_run_stage_with_retry`, with no stage-skip mechanism; confirmed via `rg
  "get_stage\("` that `WorkflowDef.get_stage()` (`scripts/agent/workflow/models.py:95`)
  is called only from within `workflow_engine.py` (to read `timeout_sec`/`retryable`),
  never to gate whether a stage runs at all.
- Confirmed via Read (`scripts/agent/orchestrator.py:267-293`,
  `_handle_workflow_engine()`) that:
  - `plan_fn`'s body is exactly `"""No-op placeholder: planning work is done by
    _handle_turn_start before engine.run()."""` / `return None` — no processing.
  - `verify_fn`'s body calls only `self._handle_turn_end(line, answer, turn_started_at,
    error_kind, is_partial)` — the same turn-end processing that would run regardless of
    workflow staging.
  - This holds for every turn type reaching `_handle_workflow_engine()`, not only simple
    Q&A — confirmed no turn-type branching exists inside `plan_fn`/`verify_fn` or in the
    code path leading to them.
- **[Minor finding, folded into this document's edit rather than reported as a Plan
  issue]** The current `WF-003` entry's `Observed Implementation` states
  "`WorkflowEngine.run()`は全4つのコールバック（plan_fn, execute_fn, verify_fn）を要求
  する" — this lists exactly three callback names while saying "4つ" (four). This is a
  pre-existing miscount in the entry being edited by this Requirement anyway; correct it
  to "3つ" in the same edit rather than leaving the inaccurate count in the text this
  Requirement is otherwise rewriting.
- **[Minor finding, not in this Requirement's scope]** The same entry's `Conflicting
  Source` cites `docs/adr/ADR-001-workflow-engine-mandatory.md:155-157` for Decision #5,
  but that line range is actually inside "Alternative C: Fallback execution when
  workflow definition is missing", not Decision #5 (which is in `### Decision Details`,
  item 5, currently near line 61). The entry already carries a `(deprecated: use
  section-based references)` annotation acknowledging line-number fragility — leave the
  line-number correction out of this edit's Requirements (REQ-001/REQ-002 do not cover
  `Conflicting Source`) and do not fix it here, to avoid scope creep into a field this
  Plan does not target; note it in this document's Details for visibility only.

## Design decisions

- Append to `Observed Implementation` (rather than replacing it) a new sentence stating
  the `_handle_workflow_engine()` finding, so the existing "3ステージ構成" observation is
  preserved alongside the new "plan_fn/verify_fn are no-op-equivalent for all turn
  types" finding — both are true and complementary evidence for the same entry.
- Replace `Recommended Action`'s two-option phrasing ("条件付きステージ実行を追加する
  か、ADR-001 Decision #5を更新してこの最適化が見送りであることを反映する") with the
  source Plan's REQ-002 text: "単一ステージ Workflow の実装は見送る。plan/verify のオー
  バーヘッドは DB ブックキーピングのみであり、実装コストに見合わないと判断".
- Replace `Resolution Target`'s "Next planning cycle" with "見送り済み（再評価条件:
  Review Triggers 参照）".
- Add one `## Change History` line: `- 2026-08-25: WF-003 を「見送り」として確定
  （plan_fn/verify_fn の実装調査結果を反映）`.

## Alternatives considered

- Removing the `WF-003` entry entirely instead of marking it deferred: rejected — Known
  Deviations entries document the audit trail of a considered-and-decided divergence;
  the source Plan's own Design section states this explicitly, and deleting it would
  lose the investigation evidence for future reference (e.g. if Review Triggers fire).

## Implementation

### Target file
`docs/adr/ADR-001-workflow-engine-mandatory.md`

### Procedure
1. Locate the `### WF-003` entry (currently lines 410-421).
2. Append the plan_fn/verify_fn investigation finding to `Observed Implementation`
   (see Design decisions), and correct "全4つの" to "全3つの" in the same sentence
   being edited.
3. Replace `Recommended Action` with the deferral decision text (see Design decisions).
4. Replace `Resolution Target` with "見送り済み（再評価条件: Review Triggers 参照）".
5. Add one line under `## Change History` (currently lines 486-494) following the
   existing format.
6. Do not touch `Conflicting Source`, `Expected Design`, `Impact`, `Owner`, or any other
   Known Deviations entry.

### Method
Targeted text replacement within one existing subsection plus one new `Change History`
line; no other section of the document is touched.

### Details
- The `Conflicting Source` line-number staleness noted in Assumptions is left as-is —
  out of scope for REQ-001/REQ-002 (see Assumptions for why).

## Compatibility considerations

N/A: documentation-only change, no code or config file is affected.

## Security considerations

N/A: no security-relevant behavior is described or changed.

## Rollback considerations

- Revert the `WF-003` entry's three edited fields and remove the added `Change History`
  line; no other state depends on this document.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/adr/ADR-001-workflow-engine-mandatory.md` | Documentation verification | `uv run python tools/validate_docs_structure.py docs/adr/ADR-001-workflow-engine-mandatory.md` | Passes |
| `docs/adr/ADR-001-workflow-engine-mandatory.md` | Documentation verification | `uv run python tools/check_doc_quality.py` | Passes |

## Completion criteria

- `WF-003`'s `Observed Implementation` includes the `_handle_workflow_engine()`
  plan_fn/verify_fn finding and the corrected "3つ" count.
- `WF-003`'s `Recommended Action` and `Resolution Target` state the deferral decision.
- `## Change History` has one new line documenting this correction.

## Out of scope

- `scripts/agent/workflow/workflow_engine.py`, `config/workflows/` — no code/config
  change (deferral decision).
- ADR-001 `## Decision` > Decision Details #5 body text.
- `WF-003`'s `Conflicting Source` line-number reference — pre-existing staleness noted
  in Assumptions, not covered by REQ-001/REQ-002.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append investigation finding to `Observed Implementation`, correct the "4つ"→"3つ" miscount | Pending | — | — | |
| 2 | Replace `Recommended Action` and `Resolution Target` with the deferral decision | Pending | — | — | |
| 3 | Add one `Change History` line | Pending | — | — | |
| 4 | Run documentation validation (`validate_docs_structure.py`, `check_doc_quality.py`) | Pending | — | — | Per `routing.md` Tools table |
| 5 | Documentation update | Completed by Steps 1-3 | — | — | This document's entire purpose is the documentation update itself |

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
- **Requirement ID**: `REQ-001`, `REQ-002` — record WF-003 as deferred with investigation evidence
- **Source issue**: `issues/20260822_wkfl_decision5_single_stage_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-132852_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-174354
- **Related target files**: `docs/adr/ADR-001-workflow-engine-mandatory.md`
