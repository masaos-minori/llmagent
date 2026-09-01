# Step 3's "already implemented" check re-scans implementations/ per row without caching

## Priority
Low

## Summary
`skills/plan-to-implementation-procedure/workflow.md` Step 3's "already
implemented" classification scans `implementations/` and `implementations/done/`
for a matching `target_file_slug` once per row in a Plan's `Implementation Target
Files` table, with no instruction to reuse the directory listing across rows —
for a Plan with N rows, this repeats the same directory scan N times when the
directory's own contents did not change between rows.

## Background
`workflow.md` "Procedure-Specific Guidance": "In Step 3, check 'already
implemented' status by first matching `target_file_slug` against file names under
`implementations/` and `implementations/done/` as a cheap filter; only when a name
matches, read that matched file's content..." This filter step is described
per-row, with no statement that the directory listing itself may be captured once
at the start of Step 3 and reused for every row's filter check.

`rules/ai-execution.md` Tool Usage: "Do not repeat a command when neither its
input nor the environment has changed." A directory listing of `implementations/`
is exactly this case within a single Step 3 pass — the directory's contents do not
change between processing row 1 and row 2 unless this same workflow just wrote a
new file into it (which only happens for rows already processed earlier in the
same pass, and is itself a bounded, trackable change).

## Problem
As written, an agent following the literal per-row instruction re-lists
`implementations/` and `implementations/done/` for every row, which is a small but
avoidable redundant operation, and — more importantly — an agent who does cache
the listing has no stated rule for when to invalidate that cache (e.g. after this
same Step 3 pass writes a new file for an earlier row, the cache must include that
new file when checking a later row against it, in case of an unlikely
cross-row name collision).

## Reason for Change
This is the concrete, workflow-specific case that the more general finding in
`itp008` (no defined mechanism for identifying a repeated identical command) can be
resolved for once and demonstrated in a real Step.

## Implementation Intent
Add a one-time-per-pass instruction to Step 3: capture the `implementations/` and
`implementations/done/` directory listing once at the start of the row-processing
loop, and update the in-memory listing (not by re-scanning the filesystem) whenever
this pass itself writes a new file for an earlier row.

## Target Files or Areas
- `skills/plan-to-implementation-procedure/workflow.md` (Procedure-Specific
  Guidance, Step 3)

## Required Changes
- State that the directory listing is captured once per Step 3 pass, not
  re-scanned per row.
- State the invalidation rule: a file this same pass just wrote must be added to
  the in-memory listing before checking any later row.

## Constraints
This changes only how the filter step's input is obtained, not the classification
logic itself (`Already implemented` / `Partially implemented` / `Not implemented`
still requires reading the matched file's content to confirm scope, per the
existing text).

## Acceptance Criteria
- Procedure-Specific Guidance states the directory listing is captured once per
  pass, with an explicit invalidation rule for files the same pass writes.

## Testing Expectations
Manual review: confirm the added instruction does not change the classification
outcome for any row, only how many filesystem scans are performed.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing the classification criteria (`Already implemented` /
  `Partially implemented` / `Not implemented`) themselves.

## Dependencies
Related to `itp008` (the general command-repetition-identification gap this issue
resolves one concrete instance of).

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `workflow.md` Step 3 and Procedure-Specific Guidance in full before wording
the change. Keep the cached-listing instruction scoped to this one filter step —
do not generalize it into a repository-wide caching rule (that is `itp008`'s
scope, not this issue's).
