# Register the untracked ADR-010 Decision #9 parse-error discrepancy

## Priority
High

## Summary
A verified disagreement between ADR-010 Decision #9 and `call_rag_service()`'s parse-error handling was found during the CI-004 closure review, was explicitly deferred to a new entry, and that entry was never created — leaving an ADR deviation invisible to anyone reading the active inventory.

## Background
This issue is derived from a consolidated audit of the governance documentation set recorded in `memo3.md` (repository root). No further background beyond the Summary and Reason for Change is needed.

## Problem
ADR-010 Decision #9 states that a parse error should be logged and treated as an empty result (`""`), explicitly not as a fallback trigger. `scripts/rag/pipeline_service.py::call_rag_service()` instead handles `ValueError` by returning `None`, which triggers fallback, and `tests/rag/test_rag_pipeline_service.py::test_json_parse_error_calls_set_fallback_reason` asserts that `None`/fallback behavior as correct. The CI-004 removal note that first found this explicitly deferred it to "a new, narrowly-scoped Known Issue or Needs Confirmation entry," but no such entry exists anywhere in Part 1 (CI-001 through CI-016) or Part 2 (NC-021 through NC-035).

## Reason for Change
This is kept as its own issue because it is the only finding in the current inventory review where design and implementation genuinely disagree on behavior, and where a test actively pins the implementation side as correct. Every other open item is a documentation defect or a missing test. This one is a live conformance question, and resolving it requires reading ADR-010 and the RAG pipeline service — sources not needed by any other issue.

The specifics, as recorded in the CI-004 removal note:

- ADR-010 Decision #9 states 「解析エラーはログに記録し、空結果として扱う」 — a parse error should be logged and treated as an empty result (`""`), explicitly not as a fallback trigger.
- `scripts/rag/pipeline_service.py::call_rag_service()` handles `ValueError` by returning `None`, which triggers fallback.
- `tests/rag/test_rag_pipeline_service.py::test_json_parse_error_calls_set_fallback_reason` asserts the `None`/fallback behavior as the expected outcome.

The CI-004 note itself concludes: "file a new, narrowly-scoped Known Issue or Needs Confirmation entry for this specific Decision #9 vs. `ValueError`-handling question if it is to be tracked." No such entry exists in Part 1 through CI-016, nor in Part 2 across NC-021 through NC-035.

Three things make this worth prioritizing. First, the Decision Target Canonical Source Matrix is explicit that code is canonical for current behavior but **not** for adopted design — when code contradicts an ADR, the ADR represents the intended architecture and the discrepancy must be registered. That registration did not happen. Second, the Merge Conditions and Resolution Workflow both assume discrepancies get recorded; an unrecorded one bypasses the entire governance mechanism. Third, and most significantly, a test encodes the deviating behavior as correct. That means the deviation is not drift that will surface on the next change — it is actively defended by CI, and will silently outlive any future ADR-010 review that does not think to check the tests.

## Implementation Intent
Determine which side is authoritative and record the answer, without changing behavior.

There are two plausible readings and they lead to different destinations. If returning `None` on a parse error is an intentional refinement of Decision #9 that was simply never written down — for example, because a malformed response is genuinely a technical failure in the same class as a timeout, and treating it as an empty result would mask a broken service — then ADR-010 is out of date and should be amended through the ADR Change Protocol. If it is an unintended deviation, then it belongs in Part 1 as a `document-code-mismatch` and the code should eventually be brought back into line.

The classification must come first and must not be pre-empted by changing either the code or the test. Note that Decision #4 and Decision #6 of the same ADR classify HTTP errors as technical failures that *should* trigger fallback, which is precisely why CI-004 was correctly closed; whether a parse error belongs in that same class is exactly the open question.

## Target Files or Areas
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `docs/adr/ADR-010-rag-fallback.md`
- `scripts/rag/pipeline_service.py` (read-only verification)
- `tests/rag/test_rag_pipeline_service.py` (read-only verification)

## Required Changes
- Read ADR-010 Decision #9 verbatim and confirm it says what the CI-004 note quotes.
- Determine whether the `None`/fallback behavior is an intentional but undocumented refinement, or an unintended deviation.
- If intentional: amend ADR-010 Decision #9 through the ADR Change Protocol so the ADR states the behavior that is actually implemented and tested.
- If unintended: register a Known Issue in Part 1 using the 16-field template, with `Area: RAG`, `Type: document-code-mismatch`, and `Target: docs/adr/ADR-010-rag-fallback.md`.
- If the determination requires owner input: register a Needs Confirmation entry in Part 2 with `Blocking: No` and a named `Assigned To`.
- In all cases, cite ADR-010 Decision #9, `call_rag_service()`, and the pinning test by name.

## Constraints
- Do not change `call_rag_service()` or its tests — classification precedes remediation.
- Do not revisit CI-004's closure; it is correctly resolved for its own stated premise.
- Create exactly one tracking artifact, not both a Known Issue and a Needs Confirmation entry.
- Do not assign `Unassigned` as the owner.

## Acceptance Criteria
- [ ] Exactly one tracking entry exists, or ADR-010 was amended and no entry was created.
- [ ] The entry cites ADR-010 Decision #9, `scripts/rag/pipeline_service.py::call_rag_service()`, and `test_json_parse_error_calls_set_fallback_reason` by name.
- [ ] The entry has a named owner.
- [ ] If ADR-010 was amended, the amendment follows the ADR Change Protocol and its acceptance evidence standard.
- [ ] No behavior change was made to the RAG fallback path.

## Testing Expectations
Not required beyond read-only verification — no behavior change is in scope. Confirm `test_json_parse_error_calls_set_fallback_reason` exists and currently passes (`uv run pytest tests/rag/test_rag_pipeline_service.py -k test_json_parse_error_calls_set_fallback_reason`) as evidence for the classification decision.

## Documentation Impact
Yes. Either `docs/00_governance_03_issue-and-uncertainty-management.md` (new entry) or `docs/adr/ADR-010-rag-fallback.md` (Decision #9 amendment) is updated, depending on the classification outcome.

## Out of Scope
- Changing fallback behavior.
- Revisiting CI-004.
- Reviewing other ADR-010 decisions.

## Dependencies
N/A: none. Standalone per `memo3.md`'s Consolidation Map — requires `scripts/rag/pipeline_service.py` reading not needed by any other issue in this set.

## Unresolved Questions
Whether the `None`/fallback behavior is an intentional undocumented refinement or an unintended deviation is the central open question this issue exists to resolve — see Implementation Intent for the two plausible readings and how to distinguish them.

## AI Implementation Instruction
Do not rewrite unrelated files. Delete resolved entries recorded in `docs/00_governance_03_issue-and-uncertainty-management.md` rather than retaining them with a closed-out status, per that document's Current-Specification-Only Policy. Read ADR-010 Decision #9 verbatim before classifying. Stop and report if its text differs materially from what the CI-004 note quotes, since the entire premise would then need re-establishing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260915-200218
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md, docs/adr/ADR-010-rag-fallback.md
