# Fix missing adr-index.md path references across governance documents

## Priority
High

## Summary
Fix broken references to `adr-index.md` across multiple governance documents. The file exists at `docs/10_adr/adr-index.md` but is referenced via incorrect paths (`10_adr/adr-index.md` from `00_index.md`, `adr-index.md` from `00_governance_01_documentation-policy.md`). These broken links cause pre-commit hook failures (`adr-invariant-matrix`, `adr-reference-scoped`) and prevent successful commits that touch governance documents.

## Background
The ADR Index file resides at `docs/10_adr/adr-index.md`. Multiple governance documents reference it using relative paths that do not resolve correctly:

1. `docs/00_governance/00_index.md` line 27: `[ADR Index](10_adr/adr-index.md)` — resolved relative to `00_governance/`, this looks for `docs/00_governance/10_adr/adr-index.md` which does not exist.
2. `docs/00_governance/00_governance_01_documentation-policy.md` line 545: `[ADR Index](adr-index.md)` — resolved relative to `00_governance/`, this looks for `docs/00_governance/adr-index.md` which does not exist.

The pre-commit hooks `adr-invariant-matrix` and `adr-reference-scoped` both fail because they cannot locate `docs/10_adr/adr-index.md` when processing these governance documents.

## Problem
Two governance documents contain broken internal `.md` links to `adr-index.md`:
- `00_index.md` uses a path relative to its own directory rather than the correct cross-area path
- `00_governance_01_documentation-policy.md` uses a bare filename that resolves against the wrong directory

This causes:
1. Pre-commit hook failures blocking commits that modify governance documents
2. Broken navigation links for human readers
3. Automated ADR invariant matrix checks failing due to unreachable index

## Reason for Change
Broken links violate the documentation structure validation rules (check #8 in `00_governance_04_documentation-checks.md`) and block the commit pipeline. Cross-area references must use full filenames with path per the link rules in `00_governance_02_documentation-metadata.md` (line 130: "For cross-area references, use full filenames with path").

## Implementation Intent
Fix the two broken link references to point to the correct relative path from each document's directory to `docs/10_adr/adr-index.md`. From `docs/00_governance/`, the correct relative path is `../10_adr/adr-index.md`.

## Target Files or Areas
- `docs/00_governance/00_index.md`
- `docs/00_governance/00_governance_01_documentation-policy.md`

## Required Changes
- In `docs/00_governance/00_index.md` line 27: change `[ADR Index](10_adr/adr-index.md)` to `[ADR Index](../10_adr/adr-index.md)`
- In `docs/00_governance/00_governance_01_documentation-policy.md` line 545: change `[ADR Index](adr-index.md)` to `[ADR Index](../10_adr/adr-index.md)`
- Verify both links resolve correctly by checking that `../10_adr/adr-index.md` exists from each document's directory

## Constraints
- Only fix the `adr-index.md` link references; do not modify other links in these files
- Use relative paths (not absolute `/10_adr/adr-index.md`) to maintain portability
- Do not modify any files under `docs/10_adr/`
- Do not create `adr-index.md` in any location other than its existing path

## Acceptance Criteria
- [ ] `docs/00_governance/00_index.md` line 27 uses `[ADR Index](../10_adr/adr-index.md)`
- [ ] `docs/00_governance/00_governance_01_documentation-policy.md` line 545 uses `[ADR Index](../10_adr/adr-index.md)`
- [ ] Both links resolve to the existing file `docs/10_adr/adr-index.md`
- [ ] Pre-commit hooks `adr-invariant-matrix` and `adr-reference-scoped` pass when run against these files
- [ ] No other links or content in either file modified

## Testing Expectations
Run `uv run python tools/check_docs_structure.py docs/00_governance/00_index.md docs/00_governance/00_governance_01_documentation-policy.md` to verify link reachability. Confirm pre-commit hooks pass: `git add docs/00_governance/ && git commit --allow-empty -m "test: verify adr-index links" --no-verify` followed by manual hook invocation if needed.

## Documentation Impact
This is a link correction in governance documents. No new content is added.

## Out of Scope
- Creating or modifying `docs/10_adr/adr-index.md` itself
- Fixing other potentially broken links in the repository
- Adding automated link-checking to CI (out of scope for this issue)
- Modifying ADR files or their section headers

## Dependencies
- None

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Perform two targeted edits:
1. In `docs/00_governance/00_index.md`: replace `(10_adr/adr-index.md)` with `(../10_adr/adr-index.md)`
2. In `docs/00_governance/00_governance_01_documentation-policy.md`: replace `(adr-index.md)` with `(../10_adr/adr-index.md)`
Do not modify any other lines. After editing, verify `../10_adr/adr-index.md` resolves from both directories. Run `uv run python tools/check_docs_structure.py docs/00_governance/00_index.md docs/00_governance/00_governance_01_documentation-policy.md`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-120301
- **Related target files**: docs/00_governance/00_index.md, docs/00_governance/00_governance_01_documentation-policy.md
