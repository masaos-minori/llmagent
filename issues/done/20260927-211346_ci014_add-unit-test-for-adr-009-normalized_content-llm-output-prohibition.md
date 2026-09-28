# Add unit test for ADR-009 normalized_content LLM-output prohibition (CI-014)

## Priority
Medium

## Summary
Add automated test coverage for ADR-009's prohibition on `normalized_content` appearing in LLM output, currently confirmed correct only by code inspection (Known Issue CI-014 in `governance_03`).

## Background
CI-014 has been open since 2026-09-15, one of five sibling "ADR invariant verified by code inspection, no automated test" entries (CI-009, CI-010, CI-012, CI-014, CI-016), previously batched in `governance_03` as one cross-cutting initiative pending an ownership decision. A deep-dive investigation (2026-09-27) found no existing cross-cutting engineering role anywhere in this repo — only a per-area RACI model (`docs/00_governance/governance_01_documentation-policy.md`) — and recommends reverting to per-area ownership rather than creating a new role (see the Configuration Ownership Map precedent, `governance_01` line 342). This issue assigns CI-014 specifically to `@data-eng` (RAG), per that recommendation.

## Problem
`_format_chunks()` uses `c.content`, not `c.normalized_content`, when formatting chunks for LLM presentation — confirmed correct via code inspection — but no automated test covers this prohibition.

## Reason for Change
Without test coverage, a future change to `_format_chunks()` could silently reintroduce `normalized_content` (the FTS5-only, LLM-unsafe field) into LLM-facing output, violating ADR-009, with no automated signal.

## Implementation Intent
Add a focused unit test asserting `_format_chunks()`'s output never contains `normalized_content`'s value when it differs from `content`, following existing conventions in the RAG test suite. No production code change is expected.

## Target Files or Areas
- `_format_chunks()` (locate exact module via `rg`; RAG query/formatting area)
- RAG test suite (new or updated test)

## Required Changes
- Add a unit test that constructs a chunk whose `content` and `normalized_content` differ, calls `_format_chunks()`, and asserts only `content`'s value appears in the formatted output.

## Constraints
N/A: no constraints beyond standard repository test conventions.

## Acceptance Criteria
- A new test exists covering ADR-009's `normalized_content` prohibition and passes.
- Full test suite passes with no regression.

## Testing Expectations
Unit test (pytest). Run the targeted test, then the full suite once per `rules/toolchain.md`.

## Documentation Impact
Once the test lands and passes, remove the CI-014 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 (Known Issues), and update the CI-009/010/012/014/016 batching note to reflect one fewer remaining member.

## Out of Scope
- CI-009, CI-010, CI-012, CI-016 — tracked as separate issues.
- Any change to `_format_chunks()`'s actual behavior (already confirmed correct; this is a test-coverage-only gap).

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — the per-area ownership recommendation (`@data-eng` for this item) was already established via a 2026-09-27 deep-dive investigation.

## AI Implementation Instruction
Add only the missing test. Do not modify `_format_chunks()` unless the new test reveals an actual bug (none is currently expected). Keep the diff scoped to the new test file/function only.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-211346
- **Related target files**: RAG test suite (new test, exact module TBD), `_format_chunks()`'s source module (reference)
