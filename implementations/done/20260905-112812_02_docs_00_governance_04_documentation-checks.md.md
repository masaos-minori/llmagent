## Goal

Register the new `tools/check_docs_content_policy.py` check in
`docs/00_governance_04_documentation-checks.md`'s Automated Checks list and
Governance Verification Matrix, as report-only (Warning) (REQ-003, REQ-004).

## Scope

- In-scope: one new numbered "Automated Checks" entry; one new Governance
  Verification Matrix row.
- Out-of-scope: implementing the script itself
  (`implementations/20260905-112812_01`); the test file
  (`implementations/20260905-112812_03`); `tools/TOOL_DESCRIPTIONS.md`
  (`implementations/20260905-112812_04`).

## Assumptions

- **Blocking precondition (Plan Phase 1)**: same as
  `implementations/20260905-112812_01` — this row's registration text
  describes what the check detects, so it should be written once the check's
  actual detection scope (Plan `docscope1`'s landed remove-category wording)
  is confirmed, though the registration entries themselves do not require
  `docscope1` to be implemented before they can be drafted.
- The next available `GV-*` ID is `GV-021` — re-verified this cycle:
  `docs/00_governance_04_documentation-checks.md` line 290 remains the
  highest-numbered entry (`GV-020`). Per Plan Risks, re-check for collision
  immediately before insertion (i.e., at Method execution time, not now),
  since another in-flight Plan could claim it first.

## Design decisions

Follow the existing `GV-020` rollout precedent exactly (re-confirmed present
at line 290: `Chk | Auto | check_compat_shims.py --check-removed-names | PR |
Warning | Partial | Implement the context-aware ... detection case; promote
to default-on once the corpus is compliant`) — same
Type/Detection/Trigger/Severity/Status columns, same "promote to default-on
once the corpus is compliant" framing in the Next Action column.

## Alternatives considered

Marking the new check's initial Status as anything other than `Partial` (the
same status `GV-020` uses while its own rollout is incomplete) — rejected:
this check is, by design, launched before the corpus is compliant (per Plan
Background's explicit rollout rationale), so `Partial` accurately reflects
that the check exists and runs, but the corpus it scans is not yet clean.

## Implementation

### Target file

`docs/00_governance_04_documentation-checks.md`

### Procedure

1. Confirm the insertion points are unchanged from Plan creation: Automated
   Checks entries 1-8 still occupy lines 19-153 (confirmed this cycle,
   `check_docs_structure.py` still entry 8), and the Governance Verification
   Matrix's highest row is still `GV-020` at line 290 (confirmed this cycle).
2. Add a new "### 9. Docs Content Policy Check
   (`check_docs_content_policy.py`)" entry after entry 8, describing what it
   detects (the five remove-categories) and its report-only status,
   following entry 1's descriptive style (confirmed present: "Checks all
   documents under `docs/*.md` for quality issues." plus a "**Core checks:**"
   bullet list and a "**Usage:**" code block).
3. Add a new Governance Verification Matrix row immediately after `GV-020`
   (next available ID, re-checked for collision immediately before this
   edit — see Assumptions), following that row's exact column structure.

### Method

Direct `Edit`: insert one new `### 9.` section (matching entry 1's
descriptive-paragraph + bullet-list + usage-block shape) and one new table
row in the Governance Verification Matrix.

### Details

New Automated Checks entry content: name
`check_docs_content_policy.py`; description "Checks all `docs/*.md` for
implementation-detail content the docs content policy prohibits: full file
trees, per-file descriptions, index tables, implementation-location
mappings, literal port numbers"; usage line `python
tools/check_docs_content_policy.py`; explicit note that it is report-only
(Warning), matching `GV-020`'s rollout framing.

New Governance Verification Matrix row (columns per `GV-020`'s confirmed
structure — ID | Rule | Type | Detection | Trigger | Severity | Status |
Next Action): `GV-021` (re-checked for collision at edit time) | "Docs
content policy violation (implementation detail in docs/*.md)" | Chk | Auto
| `check_docs_content_policy.py` | PR | Warning | Partial | "Run against the
current corpus and scope follow-up content-migration issues from the
violation inventory; promote to default-on once the corpus is compliant."

## Compatibility considerations

No interface change — documentation registration entries only. Does not
alter any existing Automated Checks entry (1-8) or existing Governance
Verification Matrix row (including `GV-020` itself, which remains unchanged).

## Security considerations

N/A — documentation-only.

## Rollback considerations

Two-location edit (Automated Checks entry + Matrix row) under version
control; revert via `git revert` if the registration text or `GV-*` ID
proves wrong. If `GV-021` collides with another in-flight Plan's claim at
edit time, use the next actually-available ID instead — this does not
require reverting anything already landed, only choosing a different number
for this row's own edit.

## Validation plan

`uv run python tools/check_docs_quality.py
docs/00_governance_04_documentation-checks.md` — no new findings introduced.

## Completion criteria

- A new numbered Automated Checks entry exists, describing the new check and
  its report-only status.
- A new Governance Verification Matrix row exists with a unique `GV-*` ID,
  Warning severity, Partial status, and the "promote to default-on..."
  framing.

## Out of scope

Implementing the script this entry describes. Any other Automated Checks
entry or Matrix row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Sequenced after `implementations/20260905-112812_01` per Plan Phase 3 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only, no test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `check_docs_quality.py` self-check, per Validation plan |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this row's target file is itself the documentation being updated |

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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/done/20260903-200135_docscope2_build-content-policy-detection-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-102139_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-112812
- **Related target files**: docs/00_governance_04_documentation-checks.md
