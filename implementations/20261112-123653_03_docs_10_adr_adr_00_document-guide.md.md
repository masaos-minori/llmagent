## Goal
Make the guide's finding-code list match `tools/check_adr_authority.py` plus `FRONTMATTER_DIVERGENCE`, and state where each check runs (`REQ-003` / `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The guide's list (about line 71) names `DUP_PRIMARY`, `DANGLING_ADR`, `AUTHORITY_CYCLE`, `FRONTMATTER_DIVERGENCE`; `check_adr_authority.py` emits five codes including `ASSUMPTION_DRIFT` and `EDGE_UNKNOWN_TYPE` (checked against `routing.md` and the tool docstring).
- Read `tools/check_adr_authority.py` and `tools/check_adr_reference.py` for the exact code names before writing.

## Design decisions
- State the five authority codes as reported by `check_adr_authority.py` (CI `lint` job) and `FRONTMATTER_DIVERGENCE` as reported by `check_adr_reference.py` through the `adr-reference-scoped` pre-commit hook, which CI runs via `pre-commit run --all-files`.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_00_document-guide.md`

### Procedure
1. Locate the bullet listing the finding codes.
2. Rewrite it to list all six codes and which tool reports each.

### Method
- Keep one bullet; do not copy tool output; name tools by path.

### Details
- Do not change the surrounding rules about the generated sections.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.

## Completion criteria
- The guide lists the same six finding codes as the tools and states where each runs.

## Out of Scope
- Changing checker behavior; CI and pre-commit configuration.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` — guide finding-code list matches the tools
- **Source issue**: issues/20261109-113248_adrrev016_adr-authority-format.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104605_adrrev016_adr-authority-format.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123653
- **Related target files**: `docs/10_adr/adr_00_document-guide.md`
