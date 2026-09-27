## Goal

Present the confirmed front-matter-`related`-vs-body-`## Related Documents` divergence to the owner and record their ruling in the `related` field description (REQ-001, REQ-002).

## Scope

In scope: presenting the divergence example and recording the ruling (intentional duality vs. drift) in the `related` field's bullet. Out of scope: reconciling any specific document's content.

## Assumptions

N/A: none — the divergence example is confirmed, re-verified this cycle.

## Design decisions

Record the ruling directly under the existing `related` bullet in "Existing Metadata Fields," rather than a separate new section — keeps it where a reader checking this field's meaning would look.

## Alternatives considered

Recording the ruling only in NC-031's entry: rejected — NC-031 is being removed (row 2 of this Plan).

## Implementation

### Target file

`docs/00_governance/governance_02_documentation-metadata.md`

### Procedure

1. Re-confirm the current `related` bullet's wording (confirmed present, unchanged, at line 24 as of this cycle) and re-confirm `governance_01_documentation-policy.md`'s divergence example (front-matter `related:` vs. body `## Related Documents`, still zero-overlap as of this cycle) immediately before editing.
2. Present the owner with the divergence example and the two readings: (a) intentional duality — front matter for tooling/navigation entry points, body heading for human-facing cross-references; (b) drift — one should be reconciled to match the other.
3. Record whichever ruling results, extending the `related` bullet's description.

### Method

Present-and-record decision task.

### Details

- Confirmed current bullet (re-verified this cycle, line 24): "- **related** — Links to related documents".
- If ruled (a) intentional: append the distinction explicitly, e.g. "Distinct in purpose from the body `## Related Documents` heading: front matter here is for tooling-facing navigation entry points; the body heading is for human-facing cross-references. The two lists are not expected to be identical."
- If ruled (b) drift: append a note stating which field is authoritative and that reconciliation across existing documents is separate, unstarted follow-up work (file a new issue for it; do not perform it in this cycle).

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

`git revert` the commit, or manually remove the added note.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_02_documentation-metadata.md` | Automated | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py` | Pass, no new findings |

## Completion criteria

- The `related` field bullet states the owner's ruling (AC-1).

## Out of scope

- Reconciling any specific document's `related`/`## Related Documents` content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-161017 | 20260927-161017 | Owner ruling obtained (via AskUserQuestion): (b) drift, front-matter `related:` authoritative. Follow-up reconciliation filed as `issues/20260927-160936_relateddocsdrift_...md` (not performed this cycle) |
| 2 | Add or update tests per Validation plan | Completed | 20260927-161017 | 20260927-161017 | N/A: documentation-only, automated checks per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-161017 | 20260927-161017 | N/A: documentation-only; docs checkers run instead |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-161017 | 20260927-161017 | N/A: this document's own target file IS the documentation being updated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `issues/20260927-160936_relateddocsdrift_reconcile-front-matter-related-field-with-body-related-documents-headings.md` | 1 | Issue | Open | Unassigned | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20260927-115902_nc031_decide-the-relationship-between-front-matter-related-and-related-documents.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121543_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-124641
- **Related target files**: docs/00_governance/governance_02_documentation-metadata.md
