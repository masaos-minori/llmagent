## Goal
Replace the `read_json_file` example in the removed-name bullet of `governance_04` with a description that names no symbol (REQ-005).

## Scope
- The bullet "Name that remains in source but is no longer the current production path" only.

## Assumptions
- No real example of such a name exists today (the Issue states none is known), so the text names none.
- The "Not yet implemented (follow-up)" statement stays.

## Design decisions
- Keep the bullet's requirement (check whether a current-specification section presents the name as production, not merely whether the string appears in `docs/`); replace the parenthetical example with a generic description.

## Alternatives considered
N/A: one-bullet docs edit.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`

### Procedure
1. Replace "(e.g. `read_json_file`, still defined in `scripts/rag/ingestion/pipeline_utils.py` but no longer the current production reader)" with "(a function that is still defined in source but whose purpose is now served by another mechanism)".

### Method
- Minimal in-place edit; keep the rest of the bullet and the "Name confirmed fully absent from source" bullet unchanged.
- Re-read the file before editing: other procedures of this batch edit it.

### Details
- Do not add history wording or an inventory of obsolete symbols.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`.
- `rg read_json_file docs` returns no match.

## Completion criteria
- The bullet names no symbol and still states the follow-up status; docs checkers pass.

## Out of Scope
- Implementing the context-aware check; other bullets.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the bullet | Completed | 20261022-115450 | 20261022-115450 | Changed: docs/00_governance/governance_04_documentation-checks.md |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261022-115450 | 20261022-115450 | validated; full suite 9689 passed, 14 skipped; ruff, mypy, bandit on edited tools pass; docs checkers pass |

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
- **Requirement ID**: `REQ-005` (symbol-free example in the governance check text)
- **Source issue**: `issues/20261021-104152_glossex_decouple-the-glossary-and-checks-from-removed-symbols.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101645
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md