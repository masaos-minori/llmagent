## Goal
- Regenerate the generated block of `eventbus_08_reference_api.md` so it lists the new `is_promotable` function (`REQ-005`).

## Scope
- The block between the `AUTO-GENERATED` and `END AUTO-GENERATED` markers, refreshed by the generator only.

## Assumptions
- Depends on procedure 01: `is_promotable` exists as a public top-level function in `dlq.py` with a docstring.
- Verified earlier: a second generation produces no further diff.

## Design decisions
- Use `uv run python tools/generate_reference_table.py --type eventbus`; do not edit the block by hand.

## Alternatives considered
- Add the row by hand: rejected; the next regeneration would diverge.

## Implementation
### Target file
`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --type eventbus`.
2. Review `git diff` for this file: the new `is_promotable` row appears and any other change reflects live code.
3. Run the generator with `--dry-run` and confirm no difference; run the documentation checkers.

### Method
- Let the generator write the file; stop and report if it changes text outside the markers.

### Details
- Report any unrelated row that changes.

## Compatibility considerations
- Documentation only; marker lines and layout are unchanged.

## Security considerations
N/A: documentation only.

## Rollback considerations
Revert with `git revert` of the implementing commit, or `git checkout -- docs/24_eventbus/eventbus_08_reference_api.md` before it is committed.

## Validation plan
- A second `--dry-run` shows no difference; run `tools/check_docs_quality.py`, `tools/check_docs_structure.py` with `--schema schemas/doc_front_matter.json`, `tools/check_docs_content_policy.py`, and `tools/check_needs_confirmation_inventory.py`.

## Completion criteria
- The block lists `is_promotable`, equals the generator output, and the checkers report no findings.

## Out of scope
- Hand edits and other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the block and review the diff | Completed | 20261012-105300 | 20261012-105300 | — Regenerated the block; is_promotable row added and the sweep_orphans description updated |
| 2 | Add or update tests per Validation plan | Completed | 20261012-105300 | 20261012-105300 | N/A: documentation only N/A: documentation only |
| 3 | Run the generator dry-run and the documentation checkers | Completed | 20261012-105300 | 20261012-105300 | — Second generation identical; checkers no findings |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261012-100156_eb019dlqmulti_resolve-multi-consumer-dlq-promotion-rule-mismatch-between-adr-006-and-code.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-102459_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-104559
- **Related target files**: docs/24_eventbus/eventbus_08_reference_api.md