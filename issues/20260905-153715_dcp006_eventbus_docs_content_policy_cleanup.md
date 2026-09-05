# Remove the literal port number from the EventBus configuration doc

## Priority
Low

## Summary
Remove the single hand-written literal port number flagged in
`docs/06_eventbus_05_configuration-and-operations.md`, per `skills/DESIGN.md`
Docs content policy — remove/retain.

## Background
`docscope1`/`docscope2` (in `issues/done/`) established the policy and the
`check_docs_content_policy.py` detection tool (`GV-021`).

## Problem
`uv run python tools/check_docs_content_policy.py` reports one finding:
`06_eventbus_05_configuration-and-operations.md:95: literal port number`.

## Reason for Change
A literal port number in prose duplicates `config/agent.toml` (or the
relevant EventBus config surface) and goes stale the moment the port
changes — the same failure mode the policy targets elsewhere in this
cleanup effort.

## Implementation Intent
Read line 95 and its surrounding paragraph, remove the literal port number,
and confirm the surrounding sentence still reads coherently — describing
what the setting controls rather than its current value, per
`skills/DESIGN.md` "No concrete configuration values."

## Target Files or Areas
- `docs/06_eventbus_05_configuration-and-operations.md`

## Required Changes
1. Remove the literal port number at line 95 (and any other occurrence in
   the same paragraph/section not caught by the single-line finding).
2. Confirm the surrounding prose remains grammatically coherent after
   removal.

## Constraints
- Do not alter any other content in this file beyond the flagged port
  number and its immediate sentence.

## Acceptance Criteria
- `uv run python tools/check_docs_content_policy.py` reports zero findings
  for this file.
- The surrounding sentence remains coherent and still describes what the
  setting controls.

## Testing Expectations
Documentation-only, single-line change.
`uv run python tools/check_docs_content_policy.py` and
`uv run python tools/check_docs_consistency.py --domain agent` (EventBus is
not a separate `check_docs_consistency.py --domain`; confirm no domain flag
covers it before skipping this step — see Unresolved Questions) are
sufficient; no `pytest`/`mypy`/`ruff` run required.

## Documentation Impact
Yes — trivial, single-sentence edit to remove the flagged port number.

## Out of Scope
- Any other file or section of `06_eventbus_05_configuration-and-operations.md`.

## Dependencies
N/A: none.

## Unresolved Questions
- `tools/check_docs_consistency.py --domain` accepts
  `agent|mcp|rag|deployment|overview` — EventBus has no dedicated domain
  flag. Confirm during implementation whether this file falls under one of
  the existing domain checks (e.g. `overview`) or has no consistency-check
  coverage at all; if the latter, note it as a pre-existing gap rather than
  blocking this issue on it.

## AI Implementation Instruction
Single-line edit. Remove only the literal port number at line 95; do not
touch any other content in the file. Confirm the sentence still reads
coherently after removal.
