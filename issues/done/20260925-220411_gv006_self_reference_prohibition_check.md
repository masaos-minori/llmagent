# [Governance] Implement Self-reference prohibition check

## Priority
Medium

## Summary
Add automated detection of self-referencing links in documents, enforcing GV-006 from the Governance Verification Matrix. A document must not link to itself in its `related` front-matter field or in body-text Markdown links.

## Background
GV-006 prohibits documents from linking to themselves. The current `check_docs_structure.py` already resolves internal `.md` links via `_build_basename_index()` and `check_links()`, but it does not compare resolved targets against the source document's own basename. Similarly, `check_related_links()` validates that referenced files exist but does not check for self-references. This gap means circular references go undetected.

## Problem
A document can include a link to itself in either the `related` front-matter field or in body-text Markdown links. This creates confusion about the document's purpose and can cause circular reference loops in documentation navigation systems. For example, a document could have `related: [self_01_something.md]` where `self_01_something.md` is the document being checked.

## Reason for Change
Self-references degrade documentation quality by creating logical confusion and potential infinite loops in documentation traversal tools. The governance policy explicitly prohibits them, but there is no automated enforcement.

## Implementation Intent
Add self-reference detection in two places within `check_docs_structure.py`:

1. **Body-text links**: In `check_links()`, after resolving a link target, compare the resolved path against the source document's own path. If they match, report a self-reference error.

2. **Front-matter `related` field**: In `check_related_links()`, after validating that each referenced file exists, additionally check whether the referenced file is the same as the source document. If so, report a self-reference error.

Both checks should produce clear error messages indicating which document contains the self-reference and what the duplicate filename is.

## Target Files or Areas
- `tools/check_docs_structure.py`
- `.github/workflows/governance-docs-consistency.yml` (CI wiring)

## Required Changes
- Modify `check_links()` to detect self-references in body-text Markdown links
- Modify `check_related_links()` to detect self-references in the `related` front-matter field
- Add error reporting with format: `{filename}: self-reference detected -> '{target}'`
- Ensure both checks work correctly with relative paths and bare filenames
- Wire the check into CI pipeline as a Warning-level finding (per GV-006 gate column)

## Constraints
- Must handle both absolute paths (e.g., `/home/sugimoto/llmagent/docs/adr/ADR-001.md`) and relative paths (e.g., `ADR-001.md`)
- Must handle cross-directory references correctly (e.g., `../00_index.md` from a subdirectory)
- Cannot change the prohibition rule — it is defined by the governance policy
- Must not break existing broken-link detection logic

## Acceptance Criteria
- A document with a body-text link to itself is flagged: e.g., `[This doc](self_01_something.md)` in `self_01_something.md`
- A document with a `related` front-matter entry pointing to itself is flagged: `related: [self_01_something.md]` in `self_01_something.md`
- Cross-references to different documents still pass validation
- Broken-link detection continues to work correctly

## Testing Expectations
- Unit test for `check_links()` detecting self-reference in body-text link
- Unit test for `check_related_links()` detecting self-reference in `related` field
- Unit test for normal cross-references passing (no false positives)
- Unit test for self-reference with absolute path resolution
- Unit test for self-reference with relative path resolution

## Documentation Impact
Update `docs/00_governance/governance_04_documentation-checks.md` to update GV-006 status from "Missing" to "Existing" in the Governance Verification Matrix table.

## Out of Scope
- Detecting indirect circular references (A→B→A chains) — only direct self-references
- Auto-fixing self-references (report-only, like other structural checks)
- Validating self-references in non-Markdown files

## Dependencies
- Depends on understanding of existing `check_docs_structure.py` link resolution logic (already read)
- No external dependencies

## Unresolved Questions
- Should the check distinguish between intentional self-references (e.g., in a "See also" section) and accidental ones? Currently treating all as violations per the strict reading of GV-006.
- Should the check apply to ADR documents as well? They use a different naming convention but could also contain self-references.

## AI Implementation Instruction
Modify `tools/check_docs_structure.py` to add self-reference detection. In `check_links()`, after resolving a link target, compare the resolved path against `path.resolve()` of the source document. In `check_related_links()`, after resolving each `related` entry, similarly compare against the source document's resolved path. Use `Path.resolve()` for consistent comparison. Do not modify any existing document files.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-220411
- **Related target files**: tools/check_docs_structure.py
