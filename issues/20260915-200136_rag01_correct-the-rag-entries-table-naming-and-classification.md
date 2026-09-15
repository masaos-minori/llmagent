# Correct the RAG entries: table naming, classification, and inventory placement

## Priority
High

## Summary
Three defects across the RAG entries in `docs/00_governance_03_issue-and-uncertainty-management.md`: RAG-005 names the wrong table for vector storage, DESIGN-2 conflates a test-coverage gap with a suspected live ADR-009 violation and carries a type that contradicts its content, and RAG-005 is retained as an open issue while declaring itself an accepted limitation not being worked.

## Background
This issue is derived from a consolidated audit of the governance documentation set recorded in `memo3.md` (repository root). No further background beyond the Summary and Reason for Change is needed.

## Problem
RAG-005 states that sqlite-vec's foreign-key limitation applies to `chunks_fts`, but the deletion-ordering mitigation it cites (`chunks_vec` before `documents`) is ADR-005's requirement for the `chunks_vec` table, not the ADR-009-governed `chunks_fts` full-text table — the entry names the wrong table for its own mitigation. DESIGN-2's `Type` is `missing-documentation`, but its content describes an untested code path, and its `Observed Implementation` field states a hypothesis ("may bypass the wrapper") in a field reserved for observed fact. RAG-005 is also marked `Status: open` while its own `Recommended Action` states it is an accepted architectural limitation not being worked, which the Lifecycle rules do not permit as a terminal state.

## Reason for Change
These are batched because all three require reading the same sources — the DB schema, ADR-005, and ADR-009 — and because the table-name correction is a hard prerequisite for relocating RAG-005 into ADR-005. Fixing them separately would mean reading the same three documents three times, and would risk moving an entry into an ADR while it still names the wrong table.

**RAG-005's table name is wrong in a way that breaks its own mitigation.** The entry states that sqlite-vec does not enforce foreign key constraints on "embedding vectors stored in the `chunks_fts` table," and its `Recommended Action` says the limitation is "mitigated by deletion ordering." But the deletion-ordering invariant is ADR-005's requirement that `chunks_vec` be deleted before `documents`, as CI-011 states. `chunks_fts` is the FTS5 full-text table governed by ADR-009, as CI-007 and CI-014 make clear. As written, RAG-005 claims a mitigation that applies to a different table than the one it names. Anyone implementing orphan cleanup from this entry would target the wrong table, and anyone reviewing the deletion path would be looking for an ordering constraint on a table that has none.

**DESIGN-2 hides a possible live violation inside a coverage gap.** Its `Type` is `missing-documentation`, which the type vocabulary defines as "Feature exists without documentation" — but the entry is about absent tests, and every structurally identical entry (CI-008 through CI-016, all "verified but needs test coverage") uses `operational-gap`. More seriously, its `Observed Implementation` field reads: "Grep for direct SQL references to `chunks_fts` outside the FTS wrapper module shows that some code paths **may** bypass the wrapper." That is a hypothesis placed in a field the Evidence-Required Rule reserves for observed fact. If code does bypass the wrapper, ADR-009 is being violated right now — a different problem, with a different severity and a different remedy, than the absence of a test that would have caught it. The entry currently tracks neither problem to a conclusion.

**RAG-005 should not be an open issue at all.** Its `Recommended Action` ends: "(Note: this is a known, accepted architectural limitation mitigated by deletion ordering, not an active defect being worked.)" The Lifecycle section defines the progression as "Open → Investigating → Deferred, or removed from this inventory once resolved or no longer applicable." An accepted limitation is a design constraint and belongs in the ADR that adopted the design, not in an inventory of defects awaiting work. Leaving it open means it can never progress, and permanently inflates the active count.

## Implementation Intent
Make each RAG entry state something true, verifiable, and correctly classified, then place each in the document where the governance model says it belongs.

The ordering matters. Correct the table name first, because it is a factual error that affects everything downstream. Then resolve DESIGN-2's evidence question by actually running the grep, because "may bypass" is not a state the entry can remain in — either it does or it does not, and the answer determines whether one entry or two are needed. Then relocate RAG-005 into ADR-005, following the Current-Specification-Only Policy's explicit requirement that content be transferred into the canonical document before it is removed from where it currently lives.

## Target Files or Areas
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `docs/adr/ADR-005-rag-source-derived-index-relationships.md`
- `docs/adr/ADR-009-rag-ft5-text-separation.md`
- The DB schema source defining `chunks_vec` and `chunks_fts` (Unknown exact path — confirm during implementation)
- The FTS wrapper module (Unknown exact path — confirm during implementation)

## Required Changes

**Table naming**
- Confirm against the schema generator or DDL which table sqlite-vec backs.
- Replace `chunks_fts` with `chunks_vec` in RAG-005's `Summary`.
- Review RAG-005's `Current Description`, `Observed Implementation`, and `Impact` for the same confusion and correct every occurrence.

**DESIGN-2**
- Run `grep -rn "chunks_fts" scripts/` and classify every hit as wrapper-internal or bypass.
- Replace the speculative `Observed Implementation` text with the literal result, citing the command.
- Change `Type` to `operational-gap` to match CI-008 through CI-016.
- If bypasses exist: file a separate Known Issue with `Type: document-code-mismatch` or `implementation-bug` for the live ADR-009 violation, and reduce DESIGN-2 to the test-coverage gap alone.
- If no bypasses exist: record that as the observed result and keep DESIGN-2 as the coverage gap.

**RAG-005 placement**
- Add the sqlite-vec FK-enforcement limitation to `docs/adr/ADR-005-rag-source-derived-index-relationships.md` as a consequence or constraint of the adopted design, stating that deletion ordering is the mitigation.
- Remove RAG-005 from the active inventory, replacing it with a prose placeholder pointing to ADR-005.
- Alternatively, if orphan cleanup is genuinely planned, set `Status: deferred` and record the trigger for revisiting it.

## Constraints
- Do not change any schema or code.
- Do not implement the ADR-009 enforcement lint rule or test in this issue.
- Do not fix any bypass found — file it, do not repair it here.
- Apply the ADR Change Protocol when amending ADR-005.
- Transfer the RAG-005 constraint into ADR-005 in a separate commit before removing the inventory entry, per the transfer-then-remove ordering in the Current-Specification-Only Policy.
- Complete the table-name correction before relocating RAG-005.

## Acceptance Criteria
- [ ] RAG-005 contains no reference to `chunks_fts`.
- [ ] RAG-005's table naming is consistent with CI-011's description of ADR-005.
- [ ] The table-name correction is verified against the schema, not inferred from surrounding prose.
- [ ] DESIGN-2's `Observed Implementation` states a verified result with no "may" or "could."
- [ ] The grep command and its literal output are cited in DESIGN-2.
- [ ] DESIGN-2's `Type` is `operational-gap`.
- [ ] If bypasses were found, a separate entry exists for the live violation and DESIGN-2 no longer describes it.
- [ ] ADR-005 documents the FK-enforcement limitation and its mitigation.
- [ ] RAG-005 is either a placeholder pointing to ADR-005, or has `Status: deferred` with a stated revisit trigger.
- [ ] No inventory entry remains `open` while describing itself as not being worked.

## Testing Expectations
Not required beyond verification commands — documentation-only change. Run `grep -rn "chunks_fts" scripts/` and record the literal output. Verify the table-name correction against the live schema (DDL or schema generator output), not against prose. Run `uv run python tools/check_docs_quality.py` against both edited documents after the change.

## Documentation Impact
Yes. `docs/00_governance_03_issue-and-uncertainty-management.md` (RAG-005, DESIGN-2) and `docs/adr/ADR-005-rag-source-derived-index-relationships.md` (new FK-enforcement limitation) are both edited.

## Out of Scope
- Implementing orphan-vector cleanup.
- Migrating to a vector store with FK support.
- Implementing the ADR-009 enforcement lint rule or integration test.
- Retuning RAG retrieval behavior.

## Dependencies
N/A: none. `memo3.md`'s Execution Order places this after the governance/EventBus issues (position 6) since it requires schema and ADR access not needed elsewhere, but no other issue's content blocks it.

## Unresolved Questions
Whether DESIGN-2's grep will find zero or nonzero bypasses is unknown until the command is run — if bypasses are found, a decision is needed on whether the resulting live-violation entry is `document-code-mismatch` or `implementation-bug`, per the Required Changes branch.

## AI Implementation Instruction
Do not rewrite unrelated files. Delete resolved entries recorded in `docs/00_governance_03_issue-and-uncertainty-management.md` rather than retaining them with a closed-out status, per that document's Current-Specification-Only Policy. Verify table names against the schema generator or DDL before editing. Run the grep and record its literal output before editing any DESIGN-2 field. Stop and report if the schema shows sqlite-vec actually backing `chunks_fts`, or if bypasses are found in more than three files, since either finding indicates a larger architectural problem than this issue's scope.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260915-200136
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md, docs/adr/ADR-005-rag-source-derived-index-relationships.md
