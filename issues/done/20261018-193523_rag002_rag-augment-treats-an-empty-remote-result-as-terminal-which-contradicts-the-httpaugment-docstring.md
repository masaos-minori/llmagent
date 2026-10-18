# RAG augment treats an empty remote result as terminal which contradicts the HttpAugment docstring

## Priority
Medium

## Summary
The `HttpAugment.run` docstring states that an empty-string result (`""`) means "caller should fall back to in-process search," but the actual behavior — and the other two docstrings in `pipeline_service.py` and `pipeline.py` — treat `""` as a valid terminal result. `RagPipeline.augment()` returns `""` without running the in-process pipeline. The `HttpAugment.run` docstring is stale and misleading, the intended empty-result contract is untested, and the behavior is ambiguous.

## Background
`call_rag_service()` in `scripts/rag/pipeline_service.py` classifies a remote HTTP 200 with an absent/None/empty `result` as kind `"empty"` with `result=""`, documented as "Not a failure." `HttpAugment.run()` maps that to `http_result_kind="remote_empty"` and returns an `HttpAugmentResult` whose `result` is `""`. `AugmentRefiner.run_http_augment()` returns that `""` to `RagPipeline.augment()`, whose `try/finally` returns it directly because `"" is not None`. So an empty remote answer terminates the augment call with `""` and never falls back to in-process search.

The three relevant documents disagree:
- `pipeline_service.py` documents `"empty"` as "Not a failure" and reserves in-process fallback for `"transient_failure"`.
- `pipeline.py` `augment()` documents the HTTP step as `str/"" (final)`.
- `http_augment.py` `HttpAugment.run` documents `""` as "valid but empty result; caller should fall back to in-process search."

The code matches the "final" sources; only the `HttpAugment.run` docstring says "fallback."

## Problem
The `HttpAugment.run` docstring contradicts both the implementation and the other two docstrings. A maintainer reading it would expect an empty remote answer to trigger in-process search; the code instead returns `""` (no answer). No test pins the empty-remote behavior at the `RagPipeline.augment()` level: `test_fallback_to_inprocess_on_http_error` covers transport-error fallback, and `test_http_result_kind_mapping_preserved` covers diagnostics mapping, but neither asserts what `augment()` returns for an HTTP 200 empty result.

Impact: a contradicting docstring in a fallback-sensitive path invites either an incorrect fix (someone "corrects" the code to fall back, changing user-facing behavior) or a missed bug (if empty-should-fallback is actually intended).

## Reason for Change
The contradiction is latent now but will surface on the next edit to this path. Aligning the docstring with the code removes the trap; resolving the underlying ambiguity prevents the wrong fix.

## Implementation Intent
Align the `HttpAugment.run` docstring with the actual behavior (an empty remote result is terminal and returned as `""`), consistent with `pipeline_service.py` and `pipeline.py`. Do not change runtime behavior unless the resolution of the open question below calls for it. If the resolution is that empty SHOULD fall back, that is a separate behavior change with its own testing.

## Target Files or Areas
- `scripts/rag/http_augment.py` — `HttpAugment.run` docstring
- Cross-reference `scripts/rag/pipeline_service.py` and `scripts/rag/pipeline.py` to confirm the intended contract.

## Required Changes
- Rewrite the `HttpAugment.run` docstring so the `""` bullet describes the actual terminal behavior (returns `""`; no in-process fallback), consistent with `pipeline_service.py` and `pipeline.py`.
- Resolve the contradiction: align all three docstrings to "terminal", or, if empty should fall back, make that an explicit behavior change (see Unresolved Questions).

## Constraints
- Do not change runtime behavior in this issue unless the open question is resolved in favor of fallback.
- Preserve the identity-vs-truthiness distinction (`""` vs `None`) accurately in the rewritten docstring.

## Acceptance Criteria
- The `HttpAugment.run` docstring no longer claims that `""` triggers in-process fallback.
- The three docstrings (`http_augment.py`, `pipeline_service.py`, `pipeline.py`) agree on the empty-result contract.
- If behavior is changed, a new test asserts the new return value; if not, existing behavior is unchanged.

## Testing Expectations
- If behavior is unchanged: a regression test asserting `RagPipeline.augment()` returns `""` for an HTTP 200 empty remote result, locking the current contract.
- If behavior changes: a unit test asserting the new fallback/return behavior.
- Run the affected test targets plus `ruff` / `mypy` before closing.

## Documentation Impact
This issue is itself the documentation correction. Keep the fix to the docstring (intent/boundary), not implementation detail. No separate `docs/*.md` change.

## Out of Scope
- Do not alter the `call_rag_service` empty/transient classification.
- Do not change auth fail-closed behavior or the `None`-means-fallback contract.
- Do not refactor the `augment()` try/finally control flow in this issue.

## Dependencies
N/A: none.

## Unresolved Questions
- Is returning `""` for an empty remote answer the intended product policy (the remote service is authoritative and an empty answer means "nothing relevant"), or should an empty remote answer fall back to in-process search? The code and two docstrings indicate "terminal"; the `HttpAugment.run` docstring indicates "fallback." Confirm before any behavior change.
- How do two-stage fetch callers (e.g. REPLAgent) treat a `""` augment result — do they present "no answer" or retry? Relevant to whether terminal-empty suppresses local retrieval.

## AI Implementation Instruction
Only correct the `HttpAugment.run` docstring to match the current terminal-empty behavior and make the three docstrings agree. Do not change runtime behavior or the `augment()` control flow unless the open question is explicitly resolved in favor of a fallback. Add a regression test locking whichever behavior is confirmed.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261018-193523
- **Related target files**: scripts/rag/http_augment.py

## Verification

Overall assessment: The issue is valid. The `HttpAugment.run` docstring genuinely contradicts both the implementation and the other two RAG docstrings on the empty-result contract. One factual claim in the issue is incorrect: the asserted test gap does not exist.

Core claim status: Holds. Against current source, `RagPipeline.augment()` returns `""` for an HTTP 200 empty remote result and never falls back to in-process search, while the `HttpAugment.run` docstring still states `""` means "caller should fall back to in-process search."

Findings by severity:

- Medium — Docstring contradiction. `HttpAugment.run` docstring (`scripts/rag/http_augment.py`) states `""` means "caller should fall back to in-process search"; the code, `call_rag_service()` docstring (`scripts/rag/pipeline_service.py`, `"empty"` documented as "Not a failure"), and `RagPipeline.augment()` docstring (`scripts/rag/pipeline.py`, HTTP step documented as `str/"" (final)`) all treat `""` as terminal. Evidence: traced the full chain `call_rag_service` -> `HttpAugment.run` -> `AugmentRefiner.run_http_augment` -> `RagPipeline.augment()`.
- Low — Testing-gap claim is false. The issue claims no test pins the empty-remote behavior at the `RagPipeline.augment()` level; `tests/rag/test_rag_http_mode.py::test_remote_empty_does_not_trigger_in_process` already asserts `augment()` returns `""` and that in-process `run()` is not invoked for an HTTP 200 empty result. Test passes; listed as CI-blocking under ADR-010 INV-03. No new test is required.

Verdict: Issue is valid; the fix is a docstring-only alignment. The plan corrects the false testing-gap claim and adds no new test.
