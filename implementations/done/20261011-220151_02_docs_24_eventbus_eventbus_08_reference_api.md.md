## Goal
- Refresh the auto-generated block in `docs/24_eventbus/eventbus_08_reference_api.md` so the `nack_event` row matches the corrected docstring (`REQ-003`).

## Scope
- The block between the `AUTO-GENERATED` and `END AUTO-GENERATED` markers, refreshed by the generator only.
- No hand edit inside or outside the block.

## Assumptions
- Depends on the previous procedure (`01`, `scripts/eventbus/delivery_repo.py`): the generator reads the docstring, so it must be edited first.
- Verified in the current document: the `nack_event` row reads "Increment delivery_failure_count and cycle_failure_count for an event."
- The generator may refresh other rows if live code drifted again; accept only changes that match live code and report them.

## Design decisions
- Use `uv run python tools/generate_reference_table.py --type eventbus` so the block stays reproducible.

## Alternatives considered
- Edit the single row by hand: rejected; the next regeneration would diverge.

## Implementation
### Target file
`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure
1. Confirm procedure `01` is applied (the docstring no longer says the events-level counters are incremented).
2. Run `uv run python tools/generate_reference_table.py --type eventbus`.
3. Review `git diff` for this file: the `nack_event` row must show the new summary and no other row should change; report any other change.
4. Run `uv run python tools/generate_reference_table.py --type eventbus --dry-run` and confirm no difference; run the documentation checkers.

### Method
- Let the generator write the file; do not edit manually.
- If the generator changes text outside the markers, stop and report.

### Details
- Expected change: only the description cell of the `nack_event` row.

## Compatibility considerations
- Documentation only; marker lines and table layout are unchanged.

## Security considerations
N/A: documentation only.

## Rollback considerations
- Revert with `git revert` of the implementing commit, or `git checkout -- docs/24_eventbus/eventbus_08_reference_api.md` before it is committed.

## Validation plan
- A second `--dry-run` shows no difference from the file.
- Run `tools/check_docs_quality.py`, `tools/check_docs_structure.py` with `--schema schemas/doc_front_matter.json`, `tools/check_docs_content_policy.py`, and `tools/check_needs_confirmation_inventory.py` with explicit paths.

## Completion criteria
- The `nack_event` row matches the new docstring summary and equals the generator output; nothing outside the markers changed; the checkers report no findings.

## Out of scope
- Hand edits, other documents, code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the block and review the diff | Completed | 20261011-220342 | 20261011-220342 | — Block regenerated; only the nack_event row changed |
| 2 | Add or update tests per Validation plan | Completed | 20261011-220342 | 20261011-220342 | N/A: documentation only N/A: documentation only |
| 3 | Run the generator dry-run and the documentation checkers | Completed | 20261011-220342 | 20261011-220342 | — Second generation identical; four doc checkers no findings |

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
- **Requirement ID**: `REQ-003` (reference API block)
- **Source issue**: issues/20261011-215944_eb015nackdoc_correct-stale-nack_event-docstring-and-generated-reference-description.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261011-220109_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-220151
- **Related target files**: docs/24_eventbus/eventbus_08_reference_api.md