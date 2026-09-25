# Recognize fail-safe/fail-closed rationale in check_docs_content_policy.py

## Priority
Low

## Summary
Add "fail-safe", "fail-closed", and "fail-open" to
`tools/check_docs_content_policy.py`'s `_RATIONALE_MARKERS` allowlist so
`check_default_value_restatement()` stops flagging security-boundary/fail-safe-default
sentences as mechanical content to remove.

## Background
While investigating `docs/00_governance_01_documentation-policy.md` Docs content
policy findings for a separate cleanup issue
(`issues/20260920-154509_dcp011_agent-docs-content-policy-cleanup-batch-2.md`), three
findings were confirmed to be false positives: sentences stating a fail-safe default
(e.g. "Fail-safe: Undefined tools in `tool_safety_tiers` default to `WRITE_DANGEROUS`")
inside `## Key Constraints` sections. `skills/DESIGN.md` Docs content policy — retain
explicitly protects "security boundary ... fail-closed/fail-open default judgment"
content; the checker's `_RATIONALE_MARKERS` docstring already states its intent is to
skip exactly this kind of "explaining *why* a default was chosen" content, but its
marker list ("because", "since", "in order to", "so that", "rationale", "to avoid", "to
ensure") does not include the "fail-safe"/"fail-closed"/"fail-open" vocabulary this
project's own documents actually use for that purpose.

## Problem
`check_default_value_restatement()` in `tools/check_docs_content_policy.py`
(function docstring, and `_RATIONALE_MARKERS` definition near line 58) flags any line
matching `` `x` defaults? to `y` `` that lacks one of its current rationale markers.
Confirmed false-positive findings from a 2026-09-20 tool run:
- `docs/agent_06_02_tool-execution-and-approval-approval.md:46`, `:117`
- `docs/agent_06_03_tool-execution-and-approval-concurrency-safety.md:86`

All three are `## Key Constraints` bullets labeled "Fail-safe:" — design-intent content
per Docs content policy — retain, not mechanical restatement.

## Reason for Change
Without this fix, every future `check_docs_content_policy.py` run keeps re-flagging
legitimate, already-reviewed fail-safe-default documentation as a warning, creating
noise that makes genuine new findings harder to spot and risks a future cleanup issue
mistakenly deleting this content (as almost happened while drafting
`issues/20260920-154509_dcp011...`, before manual investigation caught it).

## Implementation Intent
Extend `_RATIONALE_MARKERS` (a `frozenset[str]`) with the missing terms. Keep the
existing conservative, substring-match design — no new regex or control flow is needed,
only additional marker strings.

## Target Files or Areas
- `tools/check_docs_content_policy.py` (`_RATIONALE_MARKERS` definition)
- `tests/tools/test_check_docs_content_policy.py` (if it exists — confirm during
  implementation; add/extend a case covering the three false positives above)

## Required Changes
1. Add `"fail-safe"`, `"fail-closed"`, and `"fail-open"` to `_RATIONALE_MARKERS`.
2. Confirm `uv run python tools/check_docs_content_policy.py` no longer flags the three
   lines listed in Problem.
3. Confirm the tool still flags genuine default-value restatements without a rationale
   marker (i.e. this change does not silence real findings) — spot-check against at
   least one still-flagged finding from the same 2026-09-20 run (e.g.
   `docs/00_governance_03_issue-and-uncertainty-management.md:451`).
4. Add or extend a unit test covering a "Fail-safe: ... default to ..." line to prevent
   regression.

## Constraints
- Keep `_RATIONALE_MARKERS` a `frozenset[str]` of lowercase substrings, matching the
  existing pattern exactly (the checker lowercases the line before matching).
- Do not change `_DEFAULT_VALUE_RE` or any other detection function in this file.

## Acceptance Criteria
- `uv run python tools/check_docs_content_policy.py` reports zero findings for the three
  lines listed in Problem, with no other findings newly suppressed.
- A test asserts a "Fail-safe: `x` defaults to `y`" line is not flagged, and a plain
  "`x` defaults to `y`" line (no rationale marker) is still flagged.

## Testing Expectations
`uv run pytest tests/tools/ -k content_policy -v` (or the equivalent test module once
located), plus `uv run python tools/check_docs_content_policy.py` full-corpus run to
confirm the net finding count only decreases by the three false positives.

## Documentation Impact
No `docs/*.md` change required — this is a `tools/` precision fix.

## Out of Scope
- Re-running or filing the `docs/05_agent_06_02`/`agent_06_03` documentation cleanup
  itself — those files require no edit; this issue only stops the tool from flagging
  them.
- Any other `check_docs_content_policy.py` detection function
  (`check_literal_port_number`, field/type table detection, etc.).
- Auditing the full corpus for other possible marker gaps beyond fail-safe/fail-closed/
  fail-open — file a separate issue if another false-positive pattern is found later.

## Dependencies
N/A: none. Referenced by
`issues/20260920-154509_dcp011_agent-docs-content-policy-cleanup-batch-2.md`'s Out of
Scope/Dependencies section as the follow-up that should land eventually, but that issue
does not block on this one.

## Unresolved Questions
N/A: none — the three false positives were confirmed by direct tool run and file read
on 2026-09-20, and the fix approach (marker-list extension) follows the function's own
documented intent.

## AI Implementation Instruction
Locate `_RATIONALE_MARKERS` in `tools/check_docs_content_policy.py` and add the three
new lowercase marker strings. Do not touch any other function in this file. Verify with
a full-corpus run that the finding count drops by exactly the three false positives
identified in Problem and no others disappear unexpectedly.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-154905
- **Related target files**: see Target Files or Areas above
