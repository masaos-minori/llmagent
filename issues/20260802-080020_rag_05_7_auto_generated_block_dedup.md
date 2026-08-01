# Remove docs/03_rag_05_7 AUTO-GENERATED duplicate block and fix gen_rag_reference.py OPS_DOC constant

## Priority
Medium

## Summary
`docs/03_rag_05_7-rag-index-consistency-checks.md` contains an AUTO-GENERATED block duplicating content in the canonical `docs/03_rag_05_1-configuration-reference.md`. The generator, `tools/gen_rag_reference.py`, has an `OPS_DOC` constant that still points to the pre-file-split document structure, meaning auto-regeneration of this block is currently broken/stale.

## Reason for Change
A duplicated, auto-generated block that isn't actually being regenerated correctly combines the worst of both worlds: maintenance burden and staleness. Fixing the generator constant restores the intended single-source-of-truth workflow; consolidating to `05_1` removes the duplication in the meantime.

## Implementation Intent
Remove the AUTO-GENERATED block from `05_7`, consolidating its content into `05_1` (already canonical for this information). Fix `tools/gen_rag_reference.py`'s `OPS_DOC` constant to point to the correct current file structure so future regeneration (if still needed) targets the right file.

## Target Files or Areas
`docs/03_rag_05_7-rag-index-consistency-checks.md`, `docs/03_rag_05_1-configuration-reference.md`, `tools/gen_rag_reference.py`

## Required Changes
- Remove the AUTO-GENERATED block from `05_7`; verify `05_1` already contains equivalent information, or merge in any missing detail.
- Fix `tools/gen_rag_reference.py`'s `OPS_DOC` constant to reference the current (post-split) file structure, so it no longer targets a stale pre-split layout.

## Acceptance Criteria
`05_7` no longer contains a duplicated AUTO-GENERATED block; `05_1` contains the equivalent (verified) information; `gen_rag_reference.py`'s `OPS_DOC` constant correctly reflects current file structure.

## Testing Expectations
Not required for the documentation change. If `tools/gen_rag_reference.py` is modified, run it (if it has a dry-run or test mode) to confirm it generates against the correct file before finalizing.

## Documentation Impact
`docs/03_rag_05_7` shortened; `docs/03_rag_05_1` verified as complete; a small tooling-script fix in `tools/`.

## Out of Scope
Do not perform a broader refactor of `tools/gen_rag_reference.py` beyond fixing the `OPS_DOC` constant.

## AI Implementation Instruction
Verify `05_1` genuinely contains the equivalent information before deleting the block from `05_7` — do not delete based on this review's claim alone without re-confirming. Since this touches a `tools/` script rather than `scripts/`, follow the lighter-weight expectations for one-off tooling scripts per `AGENTS.md`.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §2 削除候補 item 9
- Generated at: 2026-08-02
