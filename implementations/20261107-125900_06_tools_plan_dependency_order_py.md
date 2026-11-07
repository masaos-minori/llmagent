# Implementation Procedure: non-blocking `REQ-003` note in plan_dependency_order.py

## Goal

Implement the `REQ-003` decision in `tools/plan_dependency_order.py` **without changing its
dependency-driven `ready`/`gated` classification**. Currently an archived Plan
(`plans/done/`) is treated as `CLOSED` and removed from the recommended order
(`resolve_dependency` lines 223-241; `build_report` lines 366-368), so a Plan whose
procedures were archived but never executed is invisible to the order. Add a separate,
non-blocking report line that flags an open Plan whose executed procedures are not all
archived-and-completed, while leaving `readiness`/`recommended_order`/`render_text`
`ready`/`gated` output untouched. (`REQ-003`: a Plan with an uncompleted procedure is
surfaced without its dependents changing `ready`/`gated` status.)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- A Plan's executed procedures live in `implementations/done/*.md`; each carries a
  `**Source plan**:` field in its Traceability section naming the originating Plan file.
- "Not all archived-and-completed" means at least one of the Plan's procedures in
  `implementations/done/` still has a `Pending`, `In Progress`, or `Blocked` row in its
  `### Execution Status` table.
- The flag applies to Plans currently **open** (`plans/*.md`); the goal is to surface open
  Plans that leaked unexecuted procedures into `done/`, not to re-gate already-closed ones.

## Design decisions
- **Non-blocking report line, not a classification change**: add a new computed field to
  `Report` (e.g. `incomplete: list[str]` of Plan paths with uncompleted procedures) and a
  corresponding section in `render_text`/`render_json`. Do NOT touch `resolve_dependency`,
  `readiness`, `recommended_order`, cycle/overlap detection, or the `Ready:`/`Gated:`
  sections. This preserves the ripple-risk mitigation in the Plan's Risks.
- **Mapping Plan → procedures**: enumerate `implementations/done/*.md`, read each file's
  `**Source plan**:` field (reuse the traceability-field extractor shape already present in
  `tools/manage_workitem_stage.py`'s `_extract_traceability_field`, copied locally here since
  it is not exported), normalize `plans/done/` twins, and group by source-plan stem. For each
  open Plan, check its grouped procedures' Execution Status rows.
- **Window**: scope the check to recently-archived procedures (default last 7 days, matching
  the `detect-unexecuted-archive` detector) so historical `done/` plans are not flagged; make
  it configurable via a `--days` flag on the CLI entry.

## Alternatives considered
- Changing `resolve_dependency` to return `OPEN` for an archived Plan with uncompleted
  procedures: rejected; this would change the dependency-driven `ready`/`gated`
  classification and ripple through dependent Plans, exactly the risk `REQ-003` forbids.
- Reporting only for archived Plans (the `only_plan` path): rejected; `REQ-003` targets open
  Plans whose procedures leaked into `done/`, and the archived-Plan path already handles its
  own gating (code-implementation Step 1).
- Recording the decision not to change the tool: acceptable per the Plan's fallback, but the
  recommended path is the non-blocking report line.

## Implementation
### Target file
`tools/plan_dependency_order.py`

### Procedure
1. **Add a helper to map Plan → executed procedures.** Enumerate
   `implementations/done/*.md`; for each, extract the `**Source plan**:` value via a local
   traceability-field regex (same shape as `manage_workitem_stage._extract_traceability_field`);
   normalize `plans/done/<x>` ↔ `<x>`; group paths by normalized source-plan stem. Skip files
   with no recognizable `Source plan` field.
2. **Add a helper to detect an uncompleted procedure.** For a given procedure file, parse its
   `### Execution Status` table with `parse_execution_status_rows` (import from
   `tools._workitem_status_table`) and return True if any row's `Status` is `Pending`,
   `In Progress`, or `Blocked`.
3. **Add the report field.** Extend the `Report` dataclass with an `incomplete: list[str]`
   field (sorted Plan paths). In `build_report`, after computing `order`/`results`, compute
   `incomplete` for the currently-open Plans (`plans/*.md`) whose grouped procedures include
   at least one uncompleted procedure archived within the last N days; attach it to the
   returned `Report`.
4. **Render the note.** In `render_text`, append a non-blocking section (e.g.
   `Incomplete procedures:`) listing the flagged Plans only when `report.incomplete` is
   non-empty — placed after the existing sections, never interleaved with `Ready:`/`Gated:`.
   In `render_json`, add `"incomplete"` to the payload. Do not alter existing keys.
5. **CLI flag.** Add `--days` (default 7) to the CLI entry point for this tool so the window
   is configurable; thread it into the `build_report` computation.

### Method
- Additive: new helpers, one new `Report` field, one render section, one CLI flag. No
  existing function signature used by callers changes except adding an optional
  `days` parameter with a default.

### Details
- Keep the mapping normalization consistent with `_normalize_plan_path` semantics already in
  this file's sibling tool; reuse the same `plans/done/` ↔ `plans/` equivalence.
- Guard directory enumeration so a missing `implementations/done/` yields an empty
  `incomplete` list, never an exception.
- The `incomplete` set should be computed once and shared by both renderers.

## Compatibility considerations
- Backward compatible: the `Report` gains a field and the text/json outputs gain an optional
  section/key; consumers that ignore them are unaffected. The dependency-driven
  `ready`/`gated` classification is provably unchanged (no edit to `resolve_dependency`,
  `readiness`, or `recommended_order`).
- Regression: existing plan-dependency-order tests must still pass, including any asserting
  the exact rendered output — update those golden-output assertions only to reflect the new
  optional section when flagged Plans exist in their fixtures.

## Security considerations
N/A: read-only analysis of file paths and Execution Status tables; no permission change.

## Rollback considerations
N/A: revert the commit; the change is additive and isolated.

## Validation plan
- Unit: a plan-dependency-order test asserting the `ready`/`gated` classification is
  unchanged for the same Plan with and without an uncompleted procedure (the REQ-003
  regression guard), plus a test that a Plan with an uncompleted procedure appears in the
  `Incomplete procedures:` section.
- Regression: existing `uv run pytest` (plan-dependency-order tests) passes.
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy tools/plan_dependency_order.py`,
  `uv run bandit tools/plan_dependency_order.py`.

## Completion criteria
`tools/plan_dependency_order.py` reports, in a dedicated non-blocking section, the open Plans
whose executed procedures are not all archived-and-completed, while its dependency-driven
`ready`/`gated` classification and recommended order are unchanged; the regression test
asserting the unchanged classification passes.

## Out of Scope
- Changing `resolve_dependency`, `readiness`, or `recommended_order` (forbidden by
  `REQ-003`).
- Editing any other tool.
- If the ripple risk cannot be contained, recording the decision not to modify this file
  with this rationale instead of implementing the report line.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add Plan→procedure mapping and uncompleted-procedure helpers | Pending | — | — | |
| 2 | Add the `incomplete` Report field and compute it for open Plans | Pending | — | — | |
| 3 | Render the non-blocking section in text and json; add `--days` flag | Pending | — | — | |
| 4 | Add the readiness-unchanged regression test + uncompleted-flag test | Pending | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` — surface Plans with uncompleted procedures without changing ready/gated classification
- **Source issue**: `issues/20261106-123521_procarch001_archive-procedures-only-after-execution.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-121954_procarch001_archive-procedures-only-after-execution.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-125900
- **Related target files**: `tools/plan_dependency_order.py`

## Reference Files (do not modify)
- `tools/_workitem_status_table.py` — reuse `parse_execution_status_rows` for the Execution Status parse.
- `tools/manage_workitem_stage.py` — reference for the `**Source plan**:` extractor shape (`_extract_traceability_field`) and `plans/done/` normalization; not modified.
- `rules/toolchain.md` — validation sequence for the tool change.
