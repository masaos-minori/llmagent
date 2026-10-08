# Fix ADR-015 scope and generator domain description

## Priority
Low

## Summary
Correct how ADR-015 identifies its target documents and which generator domains it names, and remove a historical reference.

## Background
Source: local investigation notes (memo2.md, ADR-015 section; review finding M17).

## Problem
- Scope targets documents with "class: Reference", but no document carries a class field in its front matter, so the ADR applies to nothing.
- Verified: only governance_02 contains a line starting with "class:"; no ADR-governed document declares it.
- Context names rag/mcp/deployment as generator domains while Implementation Notes name mcp/deployment/agent/eventbus/memory.
- Alternative C's rejection reason refers to "the source issue", a historical reference.

## Reason for Change
An ADR whose scope matches no document cannot be verified or enforced.

## Implementation Intent
- Define scope by the presence of a generated guarded block (AUTO-GENERATED comment), with class: Reference as a recommended declaration.
- Apply the Context, Assumptions, Scope, Alternative C, Rationale 3, and Completion Checklist replacements from memo2.md.

## Target Files or Areas
- `docs/10_adr/ADR-015-reference-document-class-disposition.md`
- `tools/generate_reference_table.py` (read-only check of DOMAIN_GENERATORS)

## Required Changes
- Apply every ADR-015 replacement listed in memo2.md.

## Constraints
- Do not list concrete domain counts or names that would become stale (documentation content policy); refer to the generator as the source.

## Acceptance Criteria
- Scope is decidable from the document content alone.
- No "source issue" wording remains; doc checkers pass.

## Testing Expectations
Run the doc checkers listed in `routing.md`. No code change.

## Documentation Impact
Documentation only: ADR-015.

## Out of Scope
- Adding class fields to other documents.
- Changing the generator.

## Dependencies
- N/A: none.

## Unresolved Questions
- N/A: none recorded in memo2.md. Whether the Completion Checklist item (documents declare class: Reference) should be performed in this change is not stated.

## AI Implementation Instruction
Edit only the listed sections. Do not add class fields to other documents in this issue. Run the doc checkers before finishing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-094501
- **Related target files**: `docs/10_adr/ADR-015-reference-document-class-disposition.md`, `tools/generate_reference_table.py`
