## Goal
Change `tools/check_docs_structure.py` so the Related Documents section is required for ADR documents only, leftover Related sections in non-ADR documents are flagged, and ADR front matter must cover body references (REQ-003: align the checker with the single-source model).

## Scope
- In: `check_tail_sections`, one new check function, and its wiring in `validate_file`; module docstring wording.
- Out: link reachability, size, H1, front matter field checks, and the `check_related_links` logic.

## Assumptions
- Apply this change only after the migration rows (Steps 4 and 5) so the repository passes its own check at every step; before migration, the new rule would report every non-ADR document.
- ADR detection by path: `10_adr` among the path parts (the existing `main()` uses a substring test on the path string).
- `## Keywords` stays required for every document.

## Design decisions
- Keep one tail-section function and branch on ADR versus non-ADR.
- Add a separate coverage check for ADR documents instead of folding it into `check_related_links`, which validates entries rather than comparing against the body.
- Compare by basename; ADR body references come from the `## Related Documents` block (including `###` sub-blocks), backtick and link forms, with fenced code ignored.

## Alternatives considered
- Warn instead of error for leftover sections: rejected; the migration is meant to be complete and the checker is the guard.
- Drop the Related requirement everywhere: rejected; ADR sections are mandated by the documentation policy and read by `check_known_deviation_sync.py`.

## Implementation
### Target file
`tools/check_docs_structure.py`

### Procedure
1. Update `check_tail_sections` to require `## Related Documents` only for ADR documents, keep the `## Keywords` rule, and report any `## Related Documents`, `## Related Docs`, or `## Related Chapters` heading in non-ADR documents.
2. Add a new ADR coverage check function taking the path, content, and basename index (named after the check, following the existing `check_*` convention) and call it from `validate_file`.
3. Update the module docstring's section list.

### Method
- Finding text for a non-ADR leftover: names the heading and says to use front matter `related:`.
- Finding text for ADR coverage: names each referenced document missing from front matter.
- Self-references and unresolved targets are not reported by the coverage check (other checks already report them).

### Details
- `validate_file` already computes the stripped body; reuse it.
- Keep message prefix format `{path.name}: ...` as the other checks do.
- Do not change `MAX_SIZE` or link checks.

## Compatibility considerations
- Behavior change by design: non-ADR documents with a body Related section now fail; this is why the change follows migration.
- ADR documents keep their required section.

## Security considerations
- Read-only checker; no new I/O beyond reading the documents it already reads.

## Rollback considerations
- Revert the commit; the checker returns to requiring the section everywhere, which would then fail on migrated documents, so revert together with the migration commits if needed.

## Validation plan
- `uv run ruff format tools/check_docs_structure.py` and `uv run ruff check tools/check_docs_structure.py --fix`, then confirm clean.
- `uv run mypy tools/check_docs_structure.py` (explicit path) and `uv run bandit tools/check_docs_structure.py`.
- `uv run pytest tests/tools/test_check_docs_structure.py`.
- `uv run python tools/check_docs_structure.py` over all of `docs/` reports "All checks passed" after migration.

## Completion criteria
- ADR documents without the section are reported; non-ADR documents without it are not.
- Any Related-type body section in a non-ADR document is reported.
- An ADR whose front matter lacks a body-referenced document is reported.
- The full-tree run passes after the migration rows.

## Out of scope
- Changing which front matter fields are required.
- Changing `check_related_links` or `check_links`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change `check_tail_sections` and add the ADR coverage check with wiring | Completed | 20261004-125120 | 20261004-125120 | changed: tools/check_docs_structure.py |
| 2 | Add or update tests per Validation plan (row 006) | Completed | 20261004-125120 | 20261004-125120 | tests are row 006's target; existing tests pass |
| 3 | Run ruff, mypy (explicit path), bandit, tests, and the full-tree run | Completed | 20261004-125120 | 20261004-125120 | ruff, mypy, bandit clean; diff coverage 100%; full suite 8092 passed, 6 failed (same unrelated baseline); full-tree run: only ADR-003 size finding (see report) |
| 4 | Update the module docstring | Completed | 20261004-125120 | 20261004-125120 | module docstring updated |

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
- **Requirement ID**: `REQ-003` (change the Related section rules and add the ADR coverage check)
- **Source issue**: issues/done/20261004-111518_relateddocsmerge_consolidate-front-matter-related-and-body-related-documents.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-111806_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-112553
- **Related target files**: tools/check_docs_structure.py