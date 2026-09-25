# [Governance] Implement Duplicate Related Link prohibition check

## Priority
Medium

## Summary
Add automated detection of duplicate links to the same document within a single document's `related` front-matter field or body-text Markdown links, enforcing GV-007 from the Governance Verification Matrix.

## Background
GV-007 prohibits documents from containing duplicate links to the same target document. The current `check_docs_structure.py` validates that linked files exist via `check_related_links()` and `check_links()`, but neither function deduplicates entries. A document can list the same file multiple times in its `related` field or link to the same document repeatedly in body text without any warning.

## Problem
Duplicate links create documentation structure confusion: readers may see redundant navigation options, tooling may process the same document multiple times, and the intent of having a single canonical reference is lost. For example, a document could have `related: [governance_01_documentation-policy.md, governance_01_documentation-policy.md]` or contain two identical Markdown links to the same target.

## Reason for Change
Duplicate links degrade documentation clarity and can cause issues in downstream processing (e.g., documentation generators, search indexing). The governance policy explicitly prohibits them, but there is no automated enforcement.

## Implementation Intent
Add duplicate detection in two places within `check_docs_structure.py`:

1. **Front-matter `related` field**: In `check_related_links()`, track seen basenames/resolved paths and flag duplicates. When a duplicate is found, report which document has the duplicate and which target appears more than once.

2. **Body-text Markdown links**: In `check_links()`, track seen link targets and flag duplicates within the same document. Report the duplicate target and how many times it appears.

For consistency with existing patterns, use the basename index (`basename_index`) for bare-filename comparisons and `Path.resolve()` for full-path comparisons.

## Target Files or Areas
- `tools/check_docs_structure.py`
- `.github/workflows/governance-docs-consistency.yml` (CI wiring)

## Required Changes
- Modify `check_related_links()` to detect duplicate entries in the `related` front-matter field
- Modify `check_links()` to detect duplicate Markdown links to the same target within a document
- Add error reporting with format:
  - Front-matter: `{filename}: duplicate related link -> '{target}' (appears {n} times)`
  - Body-text: `{filename}: duplicate link -> '{target}' (appears {n} times)`
- Ensure duplicate detection works alongside existing existence validation
- Wire the check into CI pipeline as a Warning-level finding (per GV-007 gate column)

## Constraints
- Must handle both bare filenames and full paths as link targets
- Must count occurrences accurately (not just binary present/absent)
- Cannot change the prohibition rule — it is defined by the governance policy
- Must not break existing broken-link detection logic

## Acceptance Criteria
- A document with duplicate entries in `related` is flagged with count
- A document with duplicate Markdown links to the same target is flagged with count
- Documents with unique links pass validation
- Existing broken-link detection continues to work correctly

## Testing Expectations
- Unit test for `check_related_links()` detecting duplicate entries in `related` field
- Unit test for `check_links()` detecting duplicate Markdown links
- Unit test for unique links passing (no false positives)
- Unit test for duplicate detection with mixed path formats (bare filename + full path to same file)

## Documentation Impact
Update `docs/00_governance/governance_04_documentation-checks.md` to update GV-007 status from "Missing" to "Existing" in the Governance Verification Matrix table.

## Out of Scope
- Detecting duplicate links across multiple documents (only intra-document duplicates)
- Auto-fixing duplicate links (report-only, like other structural checks)
- Validating duplicate links in non-Markdown files

## Dependencies
- Depends on understanding of existing `check_docs_structure.py` link resolution logic (already read)
- No external dependencies

## Unresolved Questions
- Should the check treat bare-filename and full-path references to the same file as duplicates? (Yes — using `Path.resolve()` for normalization ensures this.)
- Should the threshold be configurable (e.g., allow up to N duplicates)? Currently treating any duplicate as a violation per the strict reading of GV-007.

## AI Implementation Instruction
Modify `tools/check_docs_structure.py` to add duplicate detection. In `check_related_links()`, use a set to track seen basenames; when a basename is already in the set, report a duplicate. In `check_links()`, use a dict mapping resolved paths to occurrence counts; when a count exceeds 1, report a duplicate. Use `Path.resolve()` for consistent path comparison. Do not modify any existing document files.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-220411
- **Related target files**: tools/check_docs_structure.py
