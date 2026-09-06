## Goal
Add a new `GV-` row to the Governance Verification Matrix registering
`tools/check_canonical_source_registry.py` (REQ-010).

## Scope
- In scope: one new row in the Governance Verification Matrix table (currently
  lines 296-316).
- Out of scope: any other row in the matrix, including the pre-existing `GV-022`
  row (`check_canonical_source_conflicts.py` — a different tool, not this Plan's
  target); `tools/TOOL_DESCRIPTIONS.md`/`routing.md` — tracked in seq 06/07.

## Assumptions
- **New ID selection**: confirmed this cycle (2026-09-06) via `grep` that `GV-022`
  is the highest existing ID in the matrix — this row's new entry is `GV-023`, not
  a reuse or renumbering of any existing ID.
- **Distinct from `GV-022`**: `GV-022` ("Canonical source conflict routing and
  deduplication", tool `check_canonical_source_conflicts.py`) already exists and
  covers semantic conflict detection across registry entries — a different concern
  than this Plan's `tools/check_canonical_source_registry.py` (schema conformance,
  path existence, `source_paths` single/multi enforcement, ADR-status, claim-type
  validation). Both tools operate on the same registry file but check different
  properties of it; `GV-023` does not duplicate or replace `GV-022`.

## Design decisions
- Follow the existing table's exact column convention: `Rule ID | Rule | Doc |
  Method | Tool/Review | Timing | Gate | Status | Follow-up`. Use `Pol` as the `Doc`
  code (the rule is registered in `docs/00_governance_01_documentation-policy.md`'s
  new Canonical Source Registry subsection, seq 04) — matching `GV-011`/`GV-012`/
  `GV-022`'s own `Pol` classification for registry-related rules.
- Mark `Status: Existing` and `Follow-up: None` only once row 02's tool actually
  exists and passes against the registry file — if this row's implementation
  executes before row 02 lands, mark `Status: Missing`/`Follow-up: Implement`
  instead, matching the table's own existing convention for not-yet-implemented
  checks (e.g. `GV-002`, `GV-003`).

## Alternatives considered
- Reuse `GV-022`'s row and just add a second tool name to its "Tool/Review" column:
  rejected — `GV-022` and this Plan's tool check genuinely different properties
  (conflict detection vs. schema/path/ADR-status conformance); conflating them under
  one Rule ID would make the "Follow-up" and "Status" columns ambiguous about which
  tool's completion they track.

## Implementation
### Target file
`docs/00_governance_04_documentation-checks.md`

### Procedure
1. Re-run `grep -n "GV-[0-9]" docs/00_governance_04_documentation-checks.md`
   immediately before editing, to reconfirm `GV-022` is still the highest ID (a
   concurrent session could have added a `GV-023`+ row in the interim).
2. Add a new row: `| GV-023 | Canonical Source Registry schema/path/ADR-status
   conformance | Pol | Auto | `check_canonical_source_registry.py` | PR | Blocking |
   {Existing or Missing, per Design decisions} | {None or Implement} |` at the end
   of the table (after the current last row, `GV-022`).

### Method
Confirmed this cycle (2026-09-06) via direct read: the Governance Verification
Matrix table is at lines 296-316 (header + 18 data rows, `GV-001` through `GV-022`,
with some IDs — `GV-004`, `GV-010`, `GV-017` — absent from the sequence, consistent
with the table's own existing non-contiguous numbering); `GV-022` (line 316) is the
highest current ID.

### Details
No change to any existing row.

## Compatibility considerations
N/A: additive new row.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if `check_docs_quality.py` flags an
issue.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_04_documentation-checks.md`
- `uv run python tools/check_docs_structure.py docs/00_governance_04_documentation-checks.md`
- Re-run `grep -n "GV-023"` to confirm exactly one new row was added, not a
  duplicate.

## Completion criteria
- A `GV-023` row exists in the Governance Verification Matrix, distinct from
  `GV-022`, registering `tools/check_canonical_source_registry.py`.

## Out of scope
- `GV-022`'s own row — unrelated tool, not modified.
- `tools/TOOL_DESCRIPTIONS.md`/`routing.md` — tracked in seq 06/07.
- `docs/00_governance_01_documentation-policy.md` — tracked in seq 04 (this same
  cycle, a sibling row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-06 | 2026-09-06 | Added GV-023 row to Governance Verification Matrix |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-06 | 2026-09-06 | N/A: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-06 | 2026-09-06 | check_docs_quality.py passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-06 | 2026-09-06 | This is the documentation update itself |

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20260903-103027_m0104_introduce-machine-readable-canonical-source-registry.md
- **Source plan**: plans/20260905-165405_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-150039
- **Related target files**: docs/00_governance_04_documentation-checks.md
