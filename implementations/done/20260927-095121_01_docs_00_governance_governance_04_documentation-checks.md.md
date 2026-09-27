## Goal

Resolve the GV-020/GV-021 Governance Verification Matrix status/Follow-up inconsistency confirmed during Plan verification: GV-020's `Partial` status and Follow-up text are accurate (no change needed); GV-021's `Existing` status and "Promoted to default-on after corpus compliance" Follow-up text are confirmed **false** — `check_docs_content_policy.py` is not wired into any CI workflow — and must be corrected (REQ-004).

## Scope

In scope: the GV-021 row of the Governance Verification Matrix table and its corresponding Follow-up Work Needed entry, both in `docs/00_governance/governance_04_documentation-checks.md`. Out of scope: the GV-020 row (confirmed accurate, no change); `tools/check_compat_shims.py`/`tools/check_docs_content_policy.py`'s functionality (Reference Files only, read for evidence, not modified, per REQ-005).

## Assumptions

- The Plan's own confirmed evaluation outcome (recorded in its Background section) is authoritative: GV-020 needs no change; GV-021's Matrix Status must change from `Existing` to `Partial` and its Follow-up text must be corrected to accurately describe the still-pending CI wiring, per REQ-004.
- A concurrent process was observed (via `git status`/`git diff`) to have made large, unrelated-but-uncommitted edits to this same file's Governance Verification Matrix and Follow-up Work Needed sections (GV-011/012/016/018/019 reclassification, Follow-up renumbering) during this session. Re-confirm the exact current line numbers/row content immediately before editing (adversarial re-verification is mandatory here, more so than usual, given this observed concurrent activity) — do not assume this document's cited line numbers remain exact.

## Design decisions

- Change only the GV-021 row's `Status` cell (`Existing` → `Partial`) and `Follow-up` cell (correct the false completed-action claim), and update/add its corresponding entry in the "Follow-up Work Needed" ordered list to match — do not touch the GV-020 row or any other row.

## Alternatives considered

- Wiring `check_docs_content_policy.py` into a CI workflow now, to make the "Promoted to default-on" claim true rather than correcting the claim to be false: rejected — out of scope per the Plan (`Out-of-Scope`: "Modifying the tools' functionality"; wiring a new CI step is a functional/infrastructure change beyond this Plan's documentation-only scope, and would need its own separate issue/plan with CI-workflow-file evidence).

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Re-confirm the current GV-020 and GV-021 rows' exact content and line numbers via `grep -n "GV-020|GV-021" docs/00_governance/governance_04_documentation-checks.md` (adversarial re-verification — this file was observed under concurrent, uncommitted edit during this session; do not assume prior line-number citations still hold).
2. Re-confirm via `grep -rln "check_docs_content_policy" .github/workflows/` that the tool is still not wired into any CI workflow (re-verify this specific finding at implementation time, since CI wiring could change independently of this Plan).
3. In the Governance Verification Matrix table, change GV-021's `Status` cell from `Existing` to `Partial`.
4. In the same row, change the `Follow-up` cell from `Promoted to default-on after corpus compliance` to an accurate description, e.g. `Not yet wired into CI (.github/workflows/); promote to default-on (PR-gated) once wired`.
5. **Correction (Step 4a finding, re-verified at implementation time)**: GV-021 has no corresponding entry in the "Follow-up Work Needed" ordered list — `grep -n "GV-021" docs/00_governance/governance_04_documentation-checks.md` confirms it appears only in the Matrix table (line 310) and two prose mentions (lines 62, 171), not in the ordered list; item 8 (GV-020) is the list's last entry, with no item 9. Add a new item 9 for GV-021 after item 8, rather than updating a non-existent entry — do not renumber items 1-8.
6. Do not modify the GV-020 row or its Follow-up Work Needed entry (confirmed accurate — no change).

### Method

Targeted 2-cell table edit (GV-021's Status/Follow-up columns) plus a matching update to its corresponding ordered-list entry — no other row/entry touched.

### Details

- Before (GV-021 row): `| GV-021 | Docs content policy violation (implementation detail in docs/*.md) | Chk | Auto | \`check_docs_content_policy.py\` | PR | Warning | Existing | Promoted to default-on after corpus compliance |`
- After: `| GV-021 | Docs content policy violation (implementation detail in docs/*.md) | Chk | Auto | \`check_docs_content_policy.py\` | PR | Warning | Partial | Not yet wired into CI (.github/workflows/); promote to default-on (PR-gated) once wired |`
- Confirmed via this Plan's investigation: `grep -rln "check_docs_content_policy" .github/workflows/` returns no results (across all 10 workflow files in `.github/workflows/`).
- GV-020's row/entry must remain byte-for-byte unchanged — confirmed accurate: `check_compat_shims.py` lines 168-175 explicitly document the context-aware detection case as unimplemented, matching the current `Partial` status and Follow-up text exactly.

## Compatibility considerations

- Documentation-only change; no code/CI behavior change. If a reader previously relied on GV-021's `Existing` status to assume the check is CI-enforced, this correction removes that (already-false) assumption rather than introducing a new one.

## Security considerations

N/A: documentation accuracy correction, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually restore the prior `Existing`/"Promoted to default-on after corpus compliance" text. Given a concurrent process is independently editing this same file, coordinate any rollback with awareness that the file's surrounding content may have changed further since this edit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Manual verification | Read the GV-021 row and its Follow-up Work Needed entry | Status=`Partial`, Follow-up text accurately states CI wiring is still pending |
| `.github/workflows/` (evidence, not modified) | Re-confirm via `grep -rln "check_docs_content_policy" .github/workflows/` | Command | No results (confirms the correction's premise still holds) |

## Completion criteria

- GV-021's Matrix Status reads `Partial` and its Follow-up text accurately describes the still-pending CI wiring, with no false completed-action claim.
- GV-020's row and Follow-up entry remain unchanged.
- The corresponding "Follow-up Work Needed" ordered-list entry for GV-021 matches the corrected Matrix Follow-up text.

## Out of scope

- GV-020's row/entry (confirmed accurate).
- Any other Governance Verification Matrix row (e.g. the concurrently-observed GV-011/012/016/018/019 edits — not this Plan's concern).
- `tools/check_compat_shims.py`, `tools/check_docs_content_policy.py` (Reference Files only, not modified).
- Wiring either tool into CI (a separate, functional change beyond this documentation-only Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-104525 | 20260927-104525 | Step 4a finding: GV-021 had no existing Follow-up Work Needed list entry to update — added new item 9 instead (procedure document corrected, see Procedure step 5); GV-021 row changed `Existing`→`Partial` |
| 2 | Add or update tests per Validation plan | Completed | 20260927-104525 | 20260927-104525 | N/A: documentation-only, manual verification per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-104525 | 20260927-104525 | N/A: documentation-only change; ran `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` per `routing.md` docs row instead — all passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-104525 | 20260927-104525 | N/A: this document's own target file IS the documentation being updated |

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
- **Requirement ID**: REQ-004: update GV-021's Matrix Status and Follow-up text
- **Source issue**: issues/20260926-183302_gov020_021_status_followup_mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-200011_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-095121
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
