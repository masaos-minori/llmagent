# Decide repo-wide policy: unused `logger = logging.getLogger(__name__)` declarations — keep as placeholder or remove until first use

## Priority
Low

## Summary
Several `scripts/shared/*.py` modules declare a module-level `logger` that is never invoked
anywhere in the file: at least `token_estimation.py`, `llm_client.py`, `llm_sse_stream.py`,
`mcp_config.py`, and `tool_registry.py` (list may be incomplete — re-verify with `vulture`/`rg`
before acting).

## Reason for Change
Found during a behavior-preserving refactor cycle on `scripts/shared/token_estimation.py`
(2026-08-13). Not removed there because the same pattern recurs across multiple sibling
modules, indicating an established repo-wide convention (logger reserved for near-future use)
rather than file-local dead code — removing it in one file alone would be inconsistent with
surrounding modules (Evidence label: Strongly implied by code — the repeated pattern across
5 files suggests intent, but this has not been confirmed against any written convention
document).

## Implementation Intent
This is a policy decision, not a mechanical fix. Either:
- **Option A**: confirm this is an intentional convention (logger declared ahead of anticipated
  use) and document it explicitly in `rules/coding.md` so future refactor cycles don't flag it
  repeatedly.
- **Option B**: decide unused loggers should be removed until first use, and remove them
  across all affected files in one consistent pass (not per-file, to avoid inconsistency).

## Target Files or Areas
- `scripts/shared/token_estimation.py`
- `scripts/shared/llm_client.py`
- `scripts/shared/llm_sse_stream.py`
- `scripts/shared/mcp_config.py`
- `scripts/shared/tool_registry.py`
- (re-run `uv run vulture scripts/shared/ --min-confidence 60 | grep logger` to get the current
  complete list before acting — the list above may be stale by the time this is picked up)

## Required Changes
- Decide Option A or B.
- If A: add a short note to `rules/coding.md` documenting the convention.
- If B: remove the unused `logger` declaration from every affected file in one pass, confirming
  via `rg "logger\."` per file that it is genuinely never called first.

## Acceptance Criteria
- A single, explicit, documented policy exists (not a per-file ad-hoc decision).
- If Option B: `vulture` no longer flags unused `logger` declarations in `scripts/shared/`.

## Testing Expectations
Not required for Option A (documentation only). For Option B: run the full `tests/shared/`
suite after each file's logger removal to confirm no hidden dependency (e.g. test mocking
`shared.<module>.logger`) breaks.

## Documentation Impact
Option A requires a `rules/coding.md` addition. Option B requires no documentation beyond the
commit message.

## Out of Scope
- Do not touch loggers that ARE used in their file, even if usage looks sparse.
- Do not conflate this with the unrelated `context_view.py` token-ratio duplication issue.

## AI Implementation Instruction
Re-run the `vulture`/`rg` sweep to get a current, complete file list before acting — do not
trust the list above without re-verification, since other refactor cycles may have already
touched some of these files. If choosing Option B, remove loggers in one PR covering all
affected files together, not incrementally, to keep the codebase consistent.
