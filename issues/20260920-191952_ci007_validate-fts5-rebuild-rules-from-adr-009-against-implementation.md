# Validate FTS5 Rebuild Rules from ADR-009 Against Implementation

## Priority
Medium

## Summary
Verify that the FTS5 rebuild logic in the RAG layer conforms to the rules defined in ADR-009's Invariants section, particularly INV-07 (identical text selection rules between triggers and manual rebuilds) and INV-09 (behavior for cases where Japanese normalization is not performed).

## Background
ADR-009 defines specific FTS5 rebuild rules that must be followed. These include INV-07 ("FTS Triggerと手動再構築で同じテキスト選択規則を使用する") and INV-09 ("Markdown見出しチャンクなど、日本語正規化を行わないケースの挙動を明記する"). CI-007 tracks that these rules have not been validated against the actual implementation. The Known Deviations section also notes DESIGN-2: no test guarantees application code never directly operates on `chunks_fts`.

## Problem
ADR-009 defines specific FTS5 rebuild rules that must be followed. However, these rules have not been validated against the actual implementation. Incorrect FTS5 rebuild could lead to inconsistent search results — different paths (trigger-based vs. manual rebuild) might produce different index contents for the same data.

## Reason for Change
Without validation, the FTS5 rebuild logic may deviate from the documented intent. This creates a risk of inconsistent search results depending on how the rebuild was triggered, which affects search quality and reliability.

## Implementation Intent
Audit the FTS5 rebuild logic by comparing the trigger-based path (`scripts/db/recovery.py::check_rag_consistency()`) and the manual rebuild path (`/session rag-rebuild-fts`) against each invariant in ADR-009's Invariants section. Focus on verifying that both paths use identical text selection rules and handle edge cases consistently.

## Target Files or Areas
- `docs/adr/ADR-009-rag-ft5-text-separation.md` — source of the rules
- `scripts/db/recovery.py::check_rag_consistency()` — trigger-based rebuild
- `scripts/rag/repository.py` — FTS operations
- `scripts/mcp_servers/mdq/` — MDQ's separate database usage (out of scope per existing analysis)
- `tests/test_rag_index_integrity.py` — existing integrity tests
- `tests/test_fts_fallback.py` — existing FTS fallback tests

## Required Changes
- Audit INV-07 compliance: verify trigger-based and manual rebuild paths use identical text selection rules
- Audit INV-09 compliance: verify behavior for Markdown heading chunks and other non-normalized cases
- Audit DESIGN-2: verify no direct `chunks_fts` manipulation outside sanctioned paths
- Add unit tests covering identified gaps
- Update `docs/00_governance_03_issue-and-uncertainty-management.md` to resolve CI-007 once implemented

## Constraints
- Must preserve existing public API behavior for valid visibility updates
- Cannot break backward compatibility with tools that legitimately update visibility within bounds
- The enforcement must not introduce blocking errors for normal operations; consider logging warnings for policy violations

## Acceptance Criteria
- [ ] INV-07 verified: trigger-based and manual rebuild paths use identical text selection rules
- [ ] INV-09 verified: Markdown heading chunks and other non-normalized cases handled correctly
- [ ] DESIGN-2 verified: no direct `chunks_fts` manipulation outside sanctioned paths
- [ ] All existing FTS-related tests continue to pass
- [ ] New tests added for identified gaps

## Testing Expectations
- Unit tests for each invariant violation scenario
- Integration test simulating FTS rebuild via both trigger and manual paths
- Regression tests confirming no breaking changes to existing FTS behavior

## Documentation Impact
Update `docs/00_governance_03_issue-and-uncertainty-management.md` to mark CI-007 as resolved. Update ADR-009's Verification section if new tests are added.

## Out of Scope
- Modifying the FTS5 schema or trigger definitions
- Adding new FTS5 indexing capabilities
- Changing the tokenizer configuration

## Dependencies
- CI-014 (normalized_content prohibition) — overlapping FTS boundary concerns
- DESIGN-2 (no direct chunks_fts operation test) — related architectural limitation

## Unresolved Questions
- Are there any undocumented edge cases in the current FTS rebuild logic?
- Should the verification include performance benchmarks for large datasets?
- How should the system behave when FTS rebuild fails mid-process?

## AI Implementation Instruction
Focus on auditing the FTS5 rebuild logic against ADR-009's invariants only. Do not rewrite unrelated files. Preserve public behavior for valid FTS operations. Stop and report open questions if requirements are unclear. Do not implement out-of-scope items like new FTS5 capabilities or schema changes.
