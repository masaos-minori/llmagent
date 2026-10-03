# Implementation Procedure — Register NC-040 in the Needs Confirmation Inventory

## Goal

Add one Active Item (`NC-040`) for the `chunking_strategy` closed-value-set question
(`REQ-001`) to Part 2 of `governance_03_issue-and-uncertainty-management.md`, populated
with all fifteen documented fields, using the `#### NC-040` + `- **Field:**` bullet format
enforced by both governance checkers (`REQ-002`). Set `Source File` to the exact rel_path
the marker-checker computes for `rag_05_5-constraints-reference.md` (`REQ-003`), and keep
`check_issue_inventory_conformance.py` passing (`REQ-004`).

## Scope

Single modification to Part 2 Active Items section of
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`: insert a
`#### NC-040` heading followed by fifteen `- **Field:**` bullets, placed immediately
before `## Part 3:`.

## Assumptions

- Next free ID is `NC-040` (highest ever assigned is `NC-039`; confirmed by `git log -S 'NC-0'` on `governance_03`).
- Owner is genuinely unassigned anywhere in the repo; `Assigned To: Unknown` (+ rationale) is acceptable and satisfies `check_needs_confirmation_inventory.py` (which warns only when `Assigned To` is empty or literally `Unassigned`).
- The marker-checker matches `Source File` against a per-subdirectory `rel_path`; for `rag_05_5` that resolves to `21_rag/rag_05_5-constraints-reference.md` (verified by reading `discover_md_files` in `_docs_consistency_lib.py`).
- Conformance checker requires exactly 15 `- **Field:**` bullets for Part 2 entries (line 248 of `check_issue_inventory_conformance.py`).

## Design decisions

- Use bullet format (`#### NC-XXXX` + `- **Field:**` bullets) rather than table row, because neither governance checker parses markdown tables.
- Include all 15 documented fields as bullets, including `- **ID:** NC-040` (historical NC-021–NC-024 omitted the ID bullet and would fail the current checker).
- Leave existing table-format entries (NC-001–NC-004) untouched; mixed formats are tolerated by both checkers.

## Alternatives considered

- Table-row format for NC-040: rejected because neither checker parses markdown tables.
- Adding an ETagManager item: rejected per REQ-005 (no inline marker exists in rag_02_06; distinction is implemented in code).
- Converting entire Part 2 to bullet format: out of scope (larger, riskier change).

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

Insert a `#### NC-040` block at the end of Part 2 `### Active Items` (immediately before
`## Part 3:`) with all fifteen documented field bullets.

### Method

Edit — insert text block.

### Details

1. Confirm no `NC-040` currently exists in `governance_03` (body and git history).
2. Read `rag_05_5:30` context: the constraints-row states any non-empty string is accepted
   for `chunking_strategy` at parse time (`_validate_str`); the `"text"`/`"heading"` value
   set is a convention only, not enforced in code.
3. Insert the following block before `## Part 3:`:

```markdown
#### NC-040

- **ID:** NC-040
- **Source File:** `21_rag/rag_05_5-constraints-reference.md`
- **Section:** Constraints reference table, `chunking_strategy` row
- **Line Number:** 30
- **Question:** Whether a closed value set is intended for `chunking_strategy` (currently any non-empty string is accepted at parse time)
- **Evidence:** `rag_05_5:30` inline "(Needs confirmation: whether a closed value set is intended)" marker; prior issue `20260913-183004` and plan `20260913-203130` recorded the same question; `_validate_str` does not enforce a closed value set
- **Impact:** Without resolution, the `"text"`/`"heading"` convention may be silently treated as a requirement rather than a convention
- **Required Action:** Determine whether a closed value set is intended; if yes, implement enforcement in `_validate_str`
- **Status:** open
- **Assigned To:** Unknown (owner genuinely unassigned anywhere in the repo; `Unknown` is distinct from `Unassigned` which triggers a warning)
- **Last Reviewed:** 2026-10-02
- **Priority:** Medium
- **Related NC:** None
- **Resolution Target:** Owner decision on closed value set intent; optional follow-up issue if a value set is determined
- **Blocking:** No
```

4. Run `uv run python tools/check_needs_confirmation_inventory.py` and verify `rag_05_5-constraints-reference.md` is absent from the untracked list. If still reported, adjust `Source File` value empirically until it stops reporting.
5. Run `uv run python tools/check_issue_inventory_conformance.py` and expect "All conformance checks passed."
6. Run `uv run python tools/check_docs_structure.py "docs/00_governance/*.md"` and `uv run python tools/check_docs_quality.py`; expect no new findings.
7. Confirm `rag_02_06` is unchanged and no ETagManager item was added.

## Compatibility considerations

Mixed formats in Part 2 (existing table + new bullet block) are tolerated by both checkers.
Recommend a dedicated follow-up to unify Part 2's format.

## Security considerations

None — documentation-only change.

## Rollback considerations

Simple revert via `git checkout -- docs/00_governance/governance_03_issue-and-uncertainty-management.md`. No code impact.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| Marker sync | Verify rag_05_5 not reported as untracked | `uv run python tools/check_needs_confirmation_inventory.py` | `rag_05_5-constraints-reference.md` absent from untracked list |
| Conformance | Field count, vocabulary, referential integrity | `uv run python tools/check_issue_inventory_conformance.py` | "All conformance checks passed." |
| Docs structure/quality | No new findings | `uv run python tools/check_docs_structure.py "docs/00_governance/*.md"` and `uv run python tools/check_docs_quality.py` | No new findings |

## Completion criteria

- `AC-1`: Part 2 contains exactly one new Active Item, `NC-040`, for the `chunking_strategy` marker, with all fifteen documented fields populated.
- `AC-2`: `uv run python tools/check_needs_confirmation_inventory.py` no longer reports `rag_05_5-constraints-reference.md` as untracked.
- `AC-3`: `uv run python tools/check_issue_inventory_conformance.py` passes.
- `AC-4`: No ETagManager item is added; `rag_02_06` is unchanged.
- `AC-5`: `docs/21_rag/*.md` are unchanged.

## Out of scope

- Deciding the underlying design question (closed value set for `chunking_strategy`).
- Modifying `docs/21_rag/*.md` or the checker tools.
- Converting the existing table-format entries in Part 2.
- Adding an ETagManager/`_is_stale_update()` item (REQ-005).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261003-103134 | 20261003-103134 |  |
| 2 | Add or update tests per Validation plan | Pending | — | — | Documentation-only; no test changes required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Validators passed: conformance checker OK, marker checker OK (rag_05_5 now tracked), docs structure/quality no new findings |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation updates needed beyond this procedure |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20261001-104112_ncrag001_register-untracked-rag-needs-confirmation-items-in-central-inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-145510_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-093911
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md