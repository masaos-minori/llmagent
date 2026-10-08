# Fix ADR-010 scope, result vocabulary, and consequences

## Priority
Medium

## Summary
Correct ADR-010's target processes, add AUTH_ERROR to the result vocabulary, remove a consequence that contradicts a rejected alternative, and drop a stale checklist note.

## Background
Source: local investigation notes (memo2.md, ADR-010 section; review findings M13, G06).

## Problem
- Scope names "Agent and ingester" as targets, but the Agent does not call RagPipeline directly (rag_03_01) and the ingester does not use augment().
- INV-10's result vocabulary lacks auth_error and the AUTH_ERROR enum value.
- Negative Consequence "corpus synchronization costs arise" contradicts rejected Alternative C (separate corpus).
- The Completion Checklist keeps a stale note.

## Reason for Change
The ADR misstates which processes the fallback applies to, which misleads impact analysis.

## Implementation Intent
- Apply the revised Scope, Decision item 12, Consequences replacement, INV-10, and the checklist change from memo2.md.

## Target Files or Areas
- `docs/10_adr/ADR-010-rag-fallback.md`

## Required Changes
- Apply every ADR-010 replacement listed in memo2.md.
- Confirm the claim that no production caller uses HTTP mode before writing it.

## Constraints
- The claim "no other production caller of the HTTP mode is documented" must be checked against Agent-side RagPipeline construction sites.

## Acceptance Criteria
- Scope, vocabulary, and consequences are consistent with rag_03_01 and the rejected alternatives.
- Doc checkers pass.

## Testing Expectations
Run the doc checkers listed in `routing.md`. No code change.

## Documentation Impact
Documentation only: ADR-010.

## Out of Scope
- Fixing RAG-001.
- Changing code.

## Dependencies
- Related: `issues/20261007-153933_ragauth01_add-rag-http-delegation-authentication-and-fail-closed-responses.md`.

## Unresolved Questions
- Whether a production caller that constructs RagPipeline with a non-empty rag_service_url really does not exist (memo2.md: confirm by searching the Agent for RagPipeline construction).

## AI Implementation Instruction
Search for RagPipeline construction sites first; if a caller exists, stop and report instead of writing the Scope text. Run the doc checkers before finishing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-094457
- **Related target files**: `docs/10_adr/ADR-010-rag-fallback.md`
