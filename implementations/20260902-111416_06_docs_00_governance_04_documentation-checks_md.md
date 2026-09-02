## Goal
Fix `REQ-005`: update GV-014's `Implementation Status` column in
`docs/00_governance_04_documentation-checks.md` to reflect the new checks, and narrow
Follow-up Work item #9 accordingly.

## Scope
Modify exactly `docs/00_governance_04_documentation-checks.md`: the GV-014 row (line 286)
and Follow-up Work item #9 (line 304). No other section is modified.

## Assumptions
- GV-014's row currently reads (confirmed): `| GV-014 | Code is NOT canonical for adopted
  design decisions | Pol | Auto | \`check_compat_shims.py\` | PR | Warning | Missing |
  Implement |` — the `Missing` status and `Implement` follow-up are updated once seq 01-04
  land; the `Tooling` column already correctly lists `check_compat_shims.py` and should be
  extended to also name `check_adr_invariant_matrix.py` and `check_adr_reference.py`.
- Follow-up Work item #9 ("Add ADR-vs-code contradiction detection to CI") should be removed
  or narrowed once the three scoped checks (seq 01-03) ship, since full semantic
  contradiction detection remains explicitly out of scope (per this Plan's Implementation
  intent) — the item should be reworded to reflect what remains, not deleted outright if any
  narrower follow-up work remains (e.g. the optional test-execution sub-step, UNK-02 in the
  Plan).

## Design decisions
Per `skills/DESIGN.md` Avoid implementation-reference duplication: update only the
`Implementation Status`/`Tooling` columns and the Follow-up Work item text — do not restate
the three checks' internal logic here (that lives in each tool's own module docstring and
`tools/TOOL_DESCRIPTIONS.md`, per this repository's existing convention for `tools/check_*.py`
scripts).

## Alternatives considered
N/A: this is a status-field update following the document's own existing table format; no
architectural alternative applies.

## Implementation
### Target file
`docs/00_governance_04_documentation-checks.md`

### Procedure
Update the GV-014 row's `Tooling`, `Status`, and `Follow-up` cells; reword Follow-up Work
item #9 to reflect what remains after seq 01-04 ship (or remove it if nothing narrower
remains — confirm against the Plan's UNK-02 disposition before deciding).

### Method
1. Re-read the GV-014 row (line 286) and Follow-up Work item #9 (line 304) in full context
   before editing.
2. Update `Tooling` to list all three tools (`check_compat_shims.py`,
   `check_adr_invariant_matrix.py`, `check_adr_reference.py`).
3. Update `Status` from `Missing` to a value consistent with this document's own Status
   vocabulary (confirm the exact allowed values used elsewhere in the Governance
   Verification Matrix before choosing one — e.g. `Implemented` if that value is already
   used elsewhere in the same table, do not invent a new status word).
4. Update `Follow-up` from `Implement` to reflect remaining work, if any (per Assumptions).
5. Reword or remove Follow-up Work item #9 consistent with step 4's decision.

### Details
Re-confirmed against current source: GV-014's row and Follow-up Work item #9 exist exactly
as the Plan's Background describes (`docs/00_governance_04_documentation-checks.md:286,304`).
No Plan-level inconsistency was found for this row.

## Compatibility considerations
N/A: documentation-only status update; no code, schema, or runtime behavior change.

## Security considerations
N/A: no security-relevant content is touched.

## Rollback considerations
Trivially revertable: `git checkout -- docs/00_governance_04_documentation-checks.md`.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_04_documentation-checks.md`
  — no new issues.
- Manual review: confirm the `Status` value used matches this document's own existing
  vocabulary (no newly-invented status word).

## Completion criteria
GV-014's row accurately reflects the shipped tooling and status; Follow-up Work item #9 no
longer claims work as outstanding that seq 01-04 already completed.

## Out of scope
`tools/check_adr_invariant_matrix.py`, `tools/check_compat_shims.py`,
`tools/check_adr_reference.py`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml` — each
covered by its own implementation procedure document for this same Plan. GV-016 (a related
but separately tracked governance rule, per the Plan's own Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update GV-014 row (`Tooling`/`Status`/`Follow-up`) | Pending | — | — | |
| 2 | Reword or remove Follow-up Work item #9 | Pending | — | — | |
| 3 | Run `check_docs_quality.py` | Pending | — | — | |

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
- **Requirement ID**: REQ-005 (GV-014 status update)
- **Source issue**: `issues/20260901-183941_gv014ci_adr-compliance-ci-check-for-gv-014.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-220712_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-111416
- **Related target files**: `docs/00_governance_04_documentation-checks.md`
