# Implementation: Document tool-error vs transport-error counter split

## Goal

Add one sentence to `docs/04_mcp_03_03_transport-and-health.md` that explicitly
separates "tool-level error -> `record_success()` + `stat_tool_errors` counter" from
"transport-level error -> `record_failure()` + `stat_transport_errors` counter",
since this distinction already exists correctly in code but is not yet stated this
precisely in the doc.

## Scope

**In-Scope:**
- `docs/04_mcp_03_03_transport-and-health.md`: add one sentence immediately after the
  existing retry paragraph (around line 31) describing the two-counter split.

**Out-of-Scope:**
- `scripts/shared/tool_executor.py::_record_success()` / `_record_transport_error()` —
  no code change; both already implement the described behavior correctly (confirmed
  by direct read, lines 169-176 and 178-186 per the plan's Assumption 3).
- Retry timing, retryable-status documentation, timeout-as-non-retryable — confirmed
  already fully documented elsewhere in this same file (lines 28-32); no edit needed
  for those topics.
- `LifecycleProtocol` consolidation and `repeated_tool_error_threshold` removal —
  handled in separate phases/documents; unrelated to this doc file.

## Assumptions

1. `docs/04_mcp_03_03_transport-and-health.md:28-32` already documents retryable
   statuses (429/502/503/504), the retry max/delay sequence (4, 2, 1 seconds), and the
   non-exponential-backoff clarification — confirmed complete and accurate by direct
   read during plan research. This document only adds the one missing sentence about
   the counter split; it does not touch the surrounding retry documentation.
2. `scripts/shared/tool_executor.py::_record_success()` (lines 169-176) and
   `_record_transport_error()` (lines 178-186) already correctly implement: tool-level
   errors (`result.is_error and result.error_type == "tool"`) call
   `self._health_registry.record_success(server_key)` (transport succeeded; only the
   tool itself reported an error) and increment `self.stat_tool_errors[server_key]`;
   transport-level errors call `self._health_registry.record_failure(server_key)` and
   increment `self.stat_transport_errors[server_key]`. This document's content must
   match this existing, already-correct code behavior exactly — it is a documentation
   catch-up, not a description of new behavior.
3. Both counters (`stat_tool_errors`, `stat_transport_errors`) already exist and are
   already correctly separated in code; no code change accompanies this doc edit.

## Implementation

### Target file

`docs/04_mcp_03_03_transport-and-health.md`

### Procedure

1. Locate the existing retry paragraph ending around line 31
   (`grep -n "retry\|retryable" docs/04_mcp_03_03_transport-and-health.md` to find the
   exact current line number, since prior phases in this session may have shifted line
   numbers in this file).
2. Immediately after that paragraph, add one new sentence (or short two-clause
   sentence) stating the tool-vs-transport error counter split, in English, matching
   the doc's existing tone and formatting conventions (prose paragraph style, not a
   new table row, unless the surrounding context is already table-formatted — confirm
   the exact local formatting at implementation time before choosing).
3. Do not alter any other paragraph, table row, or diagram in the file.

### Method

Add a sentence equivalent in content to (English, per `rules/coding.md`'s
comments/docs-in-English rule — do not use the plan's Design section's Japanese
draft verbatim; translate to English for the doc):

> A tool-level error (`error_type == "tool"`) is treated as a successful transport
> call: it triggers `record_success()` on the health registry and increments the
> `stat_tool_errors` counter. A transport-level error instead triggers
> `record_failure()` and increments the `stat_transport_errors` counter. Both counters
> are tracked independently on `ToolExecutor`.

### Details

- The plan's own Design section drafts this sentence in Japanese; per
  `rules/coding.md`'s "comments and log output: English only" convention and this
  workflow's instruction to write all output documents in English, the actual doc
  edit at implementation time must be in English, not a direct copy of the plan's
  Japanese draft. This document already reflects that translation.
- This is a docs-only change: no source file, test file, or code behavior is modified.
- Locate insertion point precisely via `grep -n` before editing rather than assuming
  the line number, since earlier phases in this session's broader doc-editing pattern
  have shifted line numbers in adjacent sections of the same file in the past.
- Keep the added text concise (one to two sentences) and consistent with the
  surrounding paragraph's level of detail — do not introduce a new subsection heading
  for this addition.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Docs | `uv run check-mcp-docs` (or `uv run python tools/check_docs_consistency.py`, whichever is confirmed present in `tools/` at implementation time) | Passes |
| Manual | Re-read the edited paragraph in context | Sentence accurately reflects `_record_success()` / `_record_transport_error()`'s actual behavior (lines 169-186 of `scripts/shared/tool_executor.py`) with no code changes needed |
