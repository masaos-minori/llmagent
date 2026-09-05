## Goal

Record the decision made in `implementations/20260905-113050_01`
(deprecate / narrow / keep pending) and its rationale in
`docs/00_governance_04_documentation-checks.md`'s existing Domain
Consistency Check description (REQ-002, REQ-004).

## Scope

- In-scope: this file's existing "### 2. Domain Consistency Check
  (`check_docs_consistency.py`)" description only.
- Out-of-scope: implementing the code change itself
  (`implementations/20260905-113050_01`); any other Automated Checks entry
  or Governance Verification Matrix row (including the `docscope2`-owned
  `GV-021`/new entry, a separate Plan's target).

## Assumptions

- **Blocking precondition**: same as
  `implementations/20260905-113050_01` — this row's rationale text should be
  written only after that row's option is confirmed, since the text must
  state which option was chosen and why.
- No `docscope2`-owned edits to this same file (the new Automated Checks
  entry / Governance Verification Matrix row for
  `tools/check_docs_content_policy.py`, covered by
  `implementations/20260905-112812_02`) are touched by this row — both rows
  target the same file but different sections (this row: existing entry 2's
  description; `_02` above: a new entry 9 and a new Matrix row) — no overlap.

## Design decisions

Add the decision and its one-paragraph rationale as a new sub-bullet or
paragraph within the existing "### 2. Domain Consistency Check" section,
immediately after its existing "Port drift (documented ports match actual
configuration)" bullet (re-confirmed present this cycle, within the
"**Checks performed per domain:**" list) — keeping the note adjacent to the
exact bullet it qualifies, not in a disconnected location.

## Alternatives considered

Adding the rationale as a new, separate top-level section — rejected: the
source Plan requires the decision to be "recorded directly in
`docs/00_governance_04_documentation-checks.md`'s existing description of
these checks, so the decision is visible alongside the checks themselves"
(Plan Implementation intent) — a disconnected new section would not satisfy
"alongside the checks themselves."

## Implementation

### Target file

`docs/00_governance_04_documentation-checks.md`

### Procedure

1. Confirm the existing "Port drift (documented ports match actual
   configuration)" bullet is still present within "### 2. Domain Consistency
   Check"'s "**Checks performed per domain:**" list (re-confirmed present
   this cycle).
2. Immediately after that bullet, add a note recording the confirmed option
   (from `implementations/20260905-113050_01`) and its one-paragraph
   rationale.

### Method

Direct `Edit`: insert one new bullet or short sub-paragraph after the
existing "Port drift" bullet.

### Details

Note content depends entirely on which option
`implementations/20260905-113050_01` confirms:
- If option (c) (provisional default): note that `check_port_drift()`/
  `check_port_range_claim()` remain active pending a documented, explicit
  exemption list, since content-migration work removing port numbers from
  `docs/*.md` has not yet landed as of this decision — re-evaluate once that
  migration work completes.
- If option (a): note that both functions were deprecated because the
  violation inventory confirmed no remaining `docs/*.md` file states a port
  number.
- If option (b): note that both functions were narrowed to a specific,
  enumerated exempt file set, and name that set (or reference where it is
  enumerated).

## Compatibility considerations

No interface change — documentation note addition only. Does not alter any
other content in "### 2. Domain Consistency Check" (domain list, other
checks-performed bullets, usage examples).

## Security considerations

N/A — documentation-only.

## Rollback considerations

Single-bullet/paragraph edit under version control; revert via `git revert`
if the recorded rationale needs correction after the fact (e.g. if a later
re-evaluation changes the option).

## Validation plan

`uv run python tools/check_docs_quality.py
docs/00_governance_04_documentation-checks.md` — no new findings introduced.

## Completion criteria

The chosen option and its one-paragraph rationale are recorded immediately
adjacent to the existing "Port drift" bullet within "### 2. Domain
Consistency Check".

## Out of scope

Implementing the code change this note describes. Any other section of this
file, including the separate `docscope2`-owned new entry/Matrix row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260905 | 20260905 | `implementations/done/20260905-113050_01` confirmed option (c). Added the decision and rationale (13 files / 62 findings still affected, per `GV-021`'s corpus run) immediately after the existing "Port drift" bullet in "### 2. Domain Consistency Check". |
| 2 | Add or update tests per Validation plan | Completed | 20260905 | 20260905 | N/A: documentation-only, no test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260905 | 20260905 | `check_docs_quality.py` — 0 issues; `check_docs_structure.py` — all checks passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260905 | 20260905 | N/A: this row's target file is itself the documentation being updated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `implementations/20260905-113050_01`'s option confirmation, which itself is blocked on sibling Plans `docscope1`/`docscope2` | Yes | 20260905 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/done/20260903-200135_docscope3_reconcile-port-drift-checks-with-new-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-102436_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-113050
- **Related target files**: docs/00_governance_04_documentation-checks.md
