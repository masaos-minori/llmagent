## Goal

Document `merge-related` as a one-time migration aid (or strengthen it to any-level per owner decision); ensure its description matches the new rule. (REQ-005 / AC-5)

## Scope

- Document `merge-related` as a one-time migration aid (preserving existing tested tooling)
- Ensure its description matches the new rule text
- Update tests for the `merge-related` decision

## Assumptions

- UNK-04 recommendation: document `merge-related` as a one-time migration aid (preserve existing tested tooling)
- The strengthened check catches any heading level, so `merge-related` does not need to be strengthened for symmetry
- The existing `merge-related` subcommand (default `--dry-run`, `--fix` writes) remains functional

## Design decisions

- Adopt the recommended option: document `merge-related` as a one-time migration aid
- Preserve the existing tested tooling — do not strengthen it to any-level
- Update the tool's description to clarify its one-time-use nature

## Alternatives considered

- Strengthen `merge-related` to detect any heading level (symmetry with the strengthened check) — rejected because UNK-04 recommends documenting it as a one-time migration aid; the strengthened check catches any level

## Implementation

### Target file

`tools/manage_frontmatter.py`

### Procedure

1. Document `merge-related` as a one-time migration aid in its docstring
2. Ensure the tool's description matches the new rule text
3. Update tests for the `merge-related` decision

### Method

- Edit the docstring and description directly
- Update tests to cover the one-time-aid behavior

### Details

**Before:**
The `merge-related` subcommand description does not clarify its one-time-use nature or its limitation to `## ` level headings only.

**After:**
The updated description states:
- `merge-related` is a one-time migration aid for migrating body `## Related Documents` blocks into front matter `related:`
- It detects `## Related Documents` / `## Related Docs` / `## Related Chapters` headings (second-level only)
- For deep `### ` blocks, authors should manually migrate entries to front matter
- The strengthened `check_docs_structure.py` catches any heading level

## Compatibility considerations

- This is a documentation-only change to the tool's description — no behavioral change
- The tool's existing functionality is preserved
- Tests must be updated to cover the one-time-aid behavior

## Security considerations

- No security implications — this is a tool description update
- The one-time-aid documentation helps prevent misuse of the tool

## Rollback considerations

- Reverting would restore the ambiguous description
- If the owner later chooses to strengthen `merge-related` to any-level, this documentation would need revision

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/manage_frontmatter.py` | Unit: `merge-related` one-time-aid behavior | `uv run pytest tests/tools/test_manage_frontmatter.py -q -p no:cacheprovider -p no:randomly` | Passes |
| Changed tool files | Static analysis | `uv run ruff`, `uv run mypy`, `uv run bandit` (per `routing.md`) | Clean |
| Full docs-tooling suite | Integration: repo passes its own checks | `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py` | All pass |

## Completion criteria

- `merge-related` documented as a one-time migration aid
- Description clarifies second-level heading detection only
- Manual migration note for deep `### ` blocks included
- Tests updated for the one-time-aid behavior
- Static analysis clean

## Out of scope

- Any change to ADR documents or ADR rules (handled by `rel002`)
- Changing contextual links inside ordinary prose
- Removing `Reading Order`, `Related ADRs` or other purpose-specific navigation sections
- Reorganizing or renaming documents
- Changing front matter fields other than `related:`
- Adding a local gate to `.pre-commit-config.yaml`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document `merge-related` as one-time migration aid | Completed | 20261006-223050 | 20261006-223050 | REQ-005 |
| 2 | Update tests for the `merge-related` decision | Completed | 20261006-223050 | 20261006-223050 | REQ-006 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-223050 | 20261006-223050 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261006-223050 | 20261006-223050 |  |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261005-143453_rel001_consolidate-related-document-information-into-front-matter-related.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-073642_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-122547
- **Related target files**: tools/manage_frontmatter.py