# Fallback-like paths not defined by any Accepted ADR (INV-15/INV-16 audit)

## Priority
Medium

## Summary
The INV-15/INV-16 audit found two production paths that substitute a degraded mode when a component fails, and no Accepted ADR explicitly defines either of them. Get an owner decision on whether each is an ADR-004-scope fallback (needs an Accepted ADR) or accepted current behavior.

## Background
ADR-004 Decision 25-27 prohibit fallback unless an Accepted ADR defines trigger, destination, eligibility, restrictions, result semantics, and observability. ADR-010 is the only ADR that defines one (external RAG to in-process RAG). The audit performed for the INV-15/INV-16 Verification Matrix row (`implementations/20261001-125741_01_docs_10_adr_ADR-004-environment-failure-handling-policy.md.md`) classified every fallback-named path in `scripts/`; most are defensive patterns, but these two were not classifiable.

## Problem
1. `scripts/agent/orchestrator.py`: when `WorkflowLoader().load()` raises `WorkflowLoadError` or `FileNotFoundError`, the REPL continues in "fallback mode" with a sentinel workflow definition. ADR-004 INV-03 states that a missing or invalid Workflow definition aborts startup. Whether this path is reachable in a way that contradicts INV-03, and whether another Accepted ADR sanctions it, is Needs confirmation.
2. `scripts/agent/memory/retriever.py` (`MemoryRetriever.search()`): when the embedding is absent, the vector search raises `sqlite3.OperationalError`, or it returns no hits, retrieval degrades to FTS-only and increments `fts_fallback_count`. No Accepted ADR defines this degradation. It substitutes a retrieval mode inside the same database rather than a Destination, so whether it is in ADR-004 scope is Needs confirmation.

## Reason for Change
Without a recorded decision, these paths can be read either as sanctioned or as unreviewed fallbacks, which is exactly the ambiguity INV-15 exists to prevent.

## Implementation Intent
Get an owner decision per path: (a) classify as accepted current behavior and document the rationale, (b) define it in an Accepted ADR (or amend an existing one) with the six elements required by ADR-004 Decision 26, or (c) change the behavior. Do not invent a rationale; resolve via owner confirmation.

## Target Files or Areas
- `scripts/agent/orchestrator.py` (Workflow loader failure handling)
- `scripts/agent/memory/retriever.py` (`MemoryRetriever.search()`)
- `docs/10_adr/ADR-004-environment-failure-handling-policy.md` (INV-15/INV-16 Manual Review item)
- Other docs or ADRs that would carry the decision: Unknown

## Required Changes
- Obtain the owner decision for each of the two paths.
- Record each decision (ADR text, or a documented accepted-behavior note).
- Update the ADR-004 Manual Review item so the two paths are no longer listed as open.

## Constraints
Changing runtime behavior of either path is out of scope until the owner decision exists.

## Acceptance Criteria
- Each path has a recorded classification (sanctioned by an Accepted ADR, or accepted current behavior with rationale).
- The ADR-004 INV-15/INV-16 Manual Review item no longer lists either path as open.

## Testing Expectations
Documentation-only unless the owner chooses to change behavior; then add regression tests for the changed path. Run `uv run python tools/check_docs_quality.py` after doc edits.

## Documentation Impact
Yes: ADR-004 Manual Review item, and the ADR or doc that records each decision.

## Out of Scope
Changing the ADR-010 RAG fallback; resolving the cross-cutting owner question tracked in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.

## Dependencies
N/A: none

## Unresolved Questions
- Does the Workflow-loader fallback mode contradict INV-03, and is it reachable at startup?
- Is vector-to-FTS degradation in memory retrieval an ADR-004-scope fallback?

## AI Implementation Instruction
Do not change behavior before an owner decision is recorded; verify each claim against current source first.

## Traceability
- **Workflow phase**: code-implementation
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20260930-212727_plan.md
- **Source implementation procedure**: implementations/20261001-125741_01_docs_10_adr_ADR-004-environment-failure-handling-policy.md.md
- **Generated at**: 20261001-165722
- **Related target files**: scripts/agent/orchestrator.py, scripts/agent/memory/retriever.py, docs/10_adr/ADR-004-environment-failure-handling-policy.md
