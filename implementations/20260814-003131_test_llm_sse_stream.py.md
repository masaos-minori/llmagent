## Goal

Add characterization tests to `TestStreamOnce` in `tests/shared/test_llm_sse_stream.py`
(currently at line 232, 463 lines total, 24 `def test_`/`async def test_` functions across
4 classes) that pin the current byte-for-byte behavior of
`LlmSseStreamHandler.stream_once`'s per-chunk loop for five edge-case combinations, written
and passing against the pre-extraction code first, so they form a behavior lock before the
companion `llm_sse_stream.py` extraction procedure runs.

## Scope

**In-scope:**
- `tests/shared/test_llm_sse_stream.py`, inside `TestStreamOnce` (lines 232-462): add tests
  for the five edge cases listed in the plan's Phase 1, confirming or extending existing
  coverage where it already exists.

**Out-of-scope (no change):**
- `TestReadNextChunk` (line 34), `TestBuildPayload` (line 131), `TestHandleStatus`
  (line 161) — unrelated to this extraction, not touched.
- Any existing assertion in `TestStreamOnce` — no existing test's behavior changes; only new
  tests are added.

## Assumptions

- `test_premature_eof_without_finish_reason_raises` (currently at line 262) already covers
  the "exhausts, `is_done=False`, `finish_reason=None`" `PREMATURE_EOF` case — confirmed by
  direct read; no duplicate test is needed, only confirmation it stays green.
- `test_parse_errors_accumulated_via_ref` (currently at line 336) already covers single-shot
  `stat_parse_errors_ref` accumulation — confirmed by direct read; a multi-chunk variant is
  the only addition needed for that edge case.
- All 24 existing tests in this file currently pass against the pre-extraction
  `scripts/shared/llm_sse_stream.py` (verified indirectly: the file matches the plan's stated
  baseline, no drift found).

## Design decisions

- Follow the existing test pattern in `TestStreamOnce`: `respx.mock` to stub the POST
  response with raw SSE byte content, then call `LlmSseStreamHandler.stream_once(...)` with
  the same fixed positional/keyword argument shape used by every existing test in this class
  (`httpx.AsyncClient()`, url, history, tool_defs, temperature, max_tokens,
  `malformed_retry=`, `heartbeat_timeout=0.0`, `llm_stream_retry_on_heartbeat_timeout=True`).
- For the "`is_done=True` from a chunk that also carries `finish_reason`" case, construct SSE
  content where the `finish_reason` and `[DONE]` sentinel arrive in the *same* chunk (single
  `data:` payload boundary or concatenated bytes fed as one chunk) to exercise the immediate
  post-processing break rather than a break on a later, separate chunk.
- For the "multiple chunks before either exit condition" case, reuse the
  `test_on_token_callback_called`-style multi-chunk SSE content (already at lines 413-438)
  as a model, but assert on `content_parts`/`finish_reason` directly rather than only the
  token callback.

## Alternatives considered

N/A — this is additive test-writing following the file's own established pattern; no
alternative test framework or mocking approach was considered.

## Implementation

### Target file
`tests/shared/test_llm_sse_stream.py`

### Procedure
Add the following to `TestStreamOnce` (after the existing tests, before line 463 EOF):

1. **Clean completion, `finish_reason` already set before exhaustion** — SSE content with a
   `finish_reason` chunk followed by `[DONE]`, confirming `break` on `is_done` does not
   spuriously raise `PREMATURE_EOF` (this is effectively the existing
   `test_successful_stream_returns_response` at line 234; add an explicit case only if it
   does not already assert the no-raise path clearly enough — otherwise reference it in the
   implementation report as already-covered).
2. **Exhausts with `is_done=True` but `finish_reason` still `None`** — SSE content with
   `[DONE]` but no `finish_reason` field ever set; assert `stream_once` returns normally with
   `finish_reason is None` (no raise), matching the `break` at line 101 (non-error `exhausted`
   path) taken because `is_done` was already `True`.
3. **Confirm `test_premature_eof_without_finish_reason_raises` (line 262) stays green** — no
   new test, just re-run it as part of the full-file `pytest -v` pass in Phase 1 and Phase 2.
4. **`is_done=True` from a chunk that also carries `finish_reason`** — SSE content where a
   single feed produces both a non-null `finish_reason` and the `[DONE]` sentinel; assert the
   loop breaks immediately (no further `read_next_chunk` call needed) and the returned
   `finish_reason` matches.
5. **Multiple chunks processed before either exit condition** — SSE content split across at
   least three separate `data:` chunks before `[DONE]`; assert all `content_parts` are
   accumulated in order and the final `finish_reason` is correct.
6. **`stat_parse_errors_ref` accumulation across multiple chunks** — extend
   `test_parse_errors_accumulated_via_ref` (line 336) or add a new test with at least two
   separate malformed-then-valid chunk pairs, asserting `stat_errors[0]` reflects the sum
   across chunks (not just the last chunk) and that `parser.stat_parse_errors` is reset to 0
   after each accumulation (verified indirectly: total matches expected count, not double- or
   under-counted).

### Method
Additive unit tests using the file's existing `respx.mock` + `httpx.Response(200,
content=...)` pattern; no test framework or fixture changes.

### Details
- Run `uv run pytest tests/shared/test_llm_sse_stream.py -v` after adding these tests and
  before the companion extraction, and confirm all tests (24 existing + new) pass against the
  current, unextracted `scripts/shared/llm_sse_stream.py`. This is the behavior lock.
- After the companion `llm_sse_stream.py` extraction lands, re-run the identical command and
  confirm the identical pass/fail outcome (no newly-failing test, no newly-passing test that
  was previously failing for an unrelated reason).

## Compatibility considerations

N/A — test-only file, no downstream callers depend on it.

## Security considerations

N/A — no production code path, no external input beyond mocked HTTP responses already used
by every other test in this class.

## Rollback considerations

- Test-only addition; revert via `git revert` of the commit removes the new tests with no
  other cleanup.

## Validation plan

- `uv run pytest tests/shared/test_llm_sse_stream.py -v` — run once before the companion
  extraction (all tests pass against current code) and once after (identical outcomes).
- `uv run coverage run -m pytest tests/shared/test_llm_sse_stream.py && uv run coverage xml
  && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` — confirm ≥90%
  diff coverage on the changed lines (new tests plus the companion extraction's changed
  lines).

## Out of scope

- Any change to `TestReadNextChunk`, `TestBuildPayload`, `TestHandleStatus`.
- Any change to `tests/shared/test_llm_reconnect.py` (checked only as an indirect-consumer
  regression gate in the companion `llm_sse_stream.py` procedure's validation plan, not
  edited here).
- Mutation testing (`mutmut`) — confirmed unavailable in this environment; not applicable to
  test-file changes in any case.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-190335_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-003131
- Related target files: test_llm_sse_stream.py
