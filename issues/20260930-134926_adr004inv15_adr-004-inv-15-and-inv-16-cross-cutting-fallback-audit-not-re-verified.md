# ADR-004 INV-15/INV-16 cross-cutting fallback audit not re-verified

## Priority
Low

## Summary
`ADR-004-environment-failure-handling-policy.md`'s Verification Matrix marks the test
verifying INV-15/INV-16 ("Fallback occurs only in scenarios ADR-010 explicitly
defines") as `Needs confirmation（本タスクでは個別に再実行していない）`. Confirm
whether a test (or documented Manual Review procedure) actually covers this
cross-cutting invariant, and if not, establish one.

## Background
`ADR-004-environment-failure-handling-policy.md` defines:
- INV-15: Fallbackは、他のAccepted ADRが明示的に定義する場合に限り許可される。
- INV-16: ADR-010は、承認済みRAG Fallbackの権威であり続ける。

Its Verification Matrix lists one Integration test for both invariants ("ADR-010で定義される場面以外でFallbackが発生しないこと"), `Blocking: Yes`, but the recorded
Status is `Needs confirmation（本タスクでは個別に再実行していない）` — i.e. the last
document update did not re-run whatever verification exists for this row. No
existing issue, plan, or implementation procedure in this repository targets INV-15
or INV-16 specifically (confirmed by repository-wide search).

## Problem
Unlike the other rows in the same Verification Matrix (which cite a specific test
file and class, e.g. `tests/agent/services/test_mcp_tool_discovery.py`), this row
cites no concrete test. It is unclear whether:
- a cross-cutting test already exists somewhere in `tests/` that was simply not
  re-run, or
- no such test exists at all, and the invariant has only ever been verified by
  ad hoc manual reasoning.

INV-15/16 are cross-cutting by nature (they constrain "no fallback anywhere in the
codebase outside what ADR-010 defines"), so a single unit test is unlikely to fully
cover them — this makes the gap harder to close than a typical missing-test finding.

## Reason for Change
This is the same class of gap as `CI-014` (an ADR invariant with no automated
verification, tracked in `governance_03`'s Known Issues) — an ADR marks a Blocking
invariant but the tracking document itself records the verification status as
unconfirmed. Left as-is, a future change could introduce a fallback path outside
ADR-010's defined scope without being caught by any test or documented review step.

## Implementation Intent
1. Search the codebase (RAG pipeline, MCP servers, Agent) for every existing
   fallback code path and cross-check each one against ADR-010's defined scope.
2. Determine whether an existing test already exercises this cross-cutting check;
   if one exists, cite it in the Verification Matrix and update Status to
   `Confirmed`.
3. If no such test exists, decide with the owner whether a cross-cutting automated
   test is feasible, or whether a documented Manual Review checklist item is the
   more practical verification mechanism for this kind of invariant (an ADR
   invariant that spans the whole codebase, similar in spirit to the
   `CI-014`/cross-cutting-role open question already recorded in `governance_03`).
4. Update the ADR-004 Verification Matrix row's Status to reflect the outcome.

## Target Files or Areas
- `docs/10_adr/ADR-004-environment-failure-handling-policy.md` (Verification Matrix row for INV-15/INV-16)
- `docs/10_adr/ADR-010-rag-fallback.md` (defines the scope INV-15/16 must be checked against)
- Fallback implementation sites: Unknown — requires a repository-wide search as Step 1 of Implementation Intent

## Required Changes
- Enumerate ADR-010's defined fallback scenarios.
- Enumerate every fallback code path currently implemented in the repository.
- Confirm no fallback path exists outside ADR-010's defined scope, or file a
  follow-up if one is found.
- Add or cite the verification mechanism (test or Manual Review procedure) in
  ADR-004's Verification Matrix and update its Status.

## Constraints
N/A: no known technical constraint beyond investigation scope.

## Acceptance Criteria
- ADR-010's defined fallback scenarios are enumerated.
- Every fallback code path in the repository is identified and checked against that
  enumeration.
- The Verification Matrix row for INV-15/INV-16 cites a concrete test or a
  documented Manual Review procedure, and its Status is no longer `Needs
  confirmation`.

## Testing Expectations
Add an automated test if a cross-cutting check is feasible; otherwise document a
Manual Review procedure explicitly (not a bare `Needs confirmation` marker) and
record why automation was not chosen.

## Documentation Impact
Yes. `ADR-004-environment-failure-handling-policy.md`'s Verification Matrix Status
for the INV-15/INV-16 row must be updated to reflect the outcome (Confirmed, or a
documented Manual Review procedure with a re-review cadence).

## Out of Scope
- Changing fallback behavior itself — this issue is about establishing/confirming
  verification, not about whether current fallback logic is correct.
- Resolving `CI-014`'s own cross-cutting-role-ownership question (a related but
  separate open item already recorded in `governance_03`).

## Dependencies
N/A: none.

## Unresolved Questions
Whether a cross-cutting automated test for "no fallback outside ADR-010's scope" is
technically feasible at all, or whether this class of invariant is better served by
a documented Manual Review checklist — this needs an owner decision before
Implementation Intent Step 3 proceeds.

## AI Implementation Instruction
Do the repository-wide fallback-path search first; do not assume no test exists
without searching `tests/` explicitly. Do not modify any fallback implementation as
part of this issue. If concluding that only Manual Review is feasible, state the
reason explicitly in the ADR-004 update rather than leaving the Status ambiguous.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260930-134926
- **Related target files**: docs/10_adr/ADR-004-environment-failure-handling-policy.md, docs/10_adr/ADR-010-rag-fallback.md
