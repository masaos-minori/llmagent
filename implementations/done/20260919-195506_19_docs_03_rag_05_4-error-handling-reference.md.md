## Goal
Classify `docs/03_rag_05_4-error-handling-reference.md`'s 3 real `## Implementation
Notes` bullets against `docs/00_governance_02_documentation-metadata.md`'s Decision
Categories and apply the corresponding action (REQ-002, REQ-003).

## Scope
In scope: the 3 confirmed real bullets in this file's `## Implementation Notes` section.
Out of scope: this file's other sections; any other file.

## Assumptions
Confirmed 20260919 (`plan-to-implementation-procedure` Step 3a): this file's
`## Implementation Notes` section (line 118) contains exactly 3 real bullets:
1. `RagRerankError` is defined in `scripts/rag/llm_prompts.py` (not
   `scripts/rag/exceptions.py`), is a `RuntimeError` subclass, and is caught as
   `RuntimeError` in `pipeline.py`'s exception tuple.
2. An extended explanation (with 3 named commit hashes/messages) of why the RAG
   exception hierarchy is fragmented across `exceptions.py`, `llm_prompts.py`, and
   `pipeline.py` — three independent refactors, no ADR/design document records a
   rationale for the split, and unifying them would require a cross-cutting change
   outside a documentation fix's scope.
3. `RagPipeline.__init__()` runs `RagConfigValidator().validate()` at startup, raising
   `ValueError` on failure (aborting construction) while warnings only log and allow
   continuation.

## Design decisions
Per the Decision Categories table: bullet 1 is a code-location/behavior fact —
`Delete`/`Compress`. Bullet 2 is the strongest `Retain` candidate in this entire audit's
29-bullet set: it is explicitly "the absence of a documented rationale, when that
absence is itself operationally significant" (a Decision Categories `Retain` example
verbatim) — the fragmentation IS a real design gap, already investigated and explained
with concrete evidence (3 commit hashes). This belongs in a design/rationale-bearing
location, not Implementation Notes, since it documents a *known architectural
inconsistency* a future refactorer needs to know about — arguably it is closer to `Move
to Known Issues` than `Retain`, since it describes current implementation not matching a
clean, unified design (no single base class), and per its own text, fixing it is
explicitly out of scope for a documentation fix. Bullet 3 is a startup-validation
behavior fact with a real failure-mode distinction (`ValueError` abort vs. warning-only
continuation) — per "Design decisions regarding error handling," this is `Retain`
material.

## Alternatives considered
For bullet 2, `Retain` (promote into this file's main body as design context) was
considered against `Move to Known Issues` (file as a tracked architectural gap). `Move
to Known Issues` is preferred: the bullet's own text states "No ADR or design document
records a rationale for keeping them separate" and explicitly scopes unification as
future, cross-cutting work — this is closer to an acknowledged inconsistency awaiting
resolution than to settled design rationale worth stating as fact in the main body.

## Implementation
### Target file
docs/03_rag_05_4-error-handling-reference.md

### Procedure
1. Re-verify bullet 1's claim (which exceptions `pipeline.py`'s catch tuple includes)
   and bullet 2's claim (the 3 named commits, and that no ADR still records this
   rationale — check `docs/adr/*.md` again since 20260919's original check) against
   current source, since this file's classification depends on these facts still
   holding.
2. Classify each of the 3 bullets per the Design decisions reasoning above.
3. Apply each bullet's action: delete/compress bullet 1; file a Known Issues entry for
   bullet 2 (per `docs/00_governance_03_issue-and-uncertainty-management.md` Part 1)
   and replace with a cross-reference; retain bullet 3's error-handling behavior in the
   main body.
4. Re-run the Validation plan's checkers.

### Method
`Edit` tool — direct text edit within `## Implementation Notes` and this file's main
body; `docs/00_governance_03_issue-and-uncertainty-management.md` Part 1 (new entry for
bullet 2 — see that file's own procedure document, row 21).

### Details
Preserve bullet 2's full evidentiary detail (the 3 commit hashes and their messages) in
the new Known Issues entry — this is exactly the kind of concrete evidence that entry
template's own fields expect; do not compress it away when moving it.

## Compatibility considerations
This row modifies `## Implementation Notes` and this file's main body. It also
contributes one new entry to `docs/00_governance_03_issue-and-uncertainty-management.md`
Part 1 — that file's own procedure document (row 21) performs that side of the edit.

## Security considerations
N/A: documentation-only, no credentials or runtime behavior change.

## Rollback considerations
`git checkout -- docs/03_rag_05_4-error-handling-reference.md` reverts this row
independently.

## Validation plan
- `uv run python tools/check_docs_quality.py` — confirm no new finding for this file.
- `uv run python tools/check_docs_structure.py` — confirm no new finding for this file.

## Completion criteria
All 3 bullets are classified into exactly one Decision Categories bucket and the
corresponding action applied; bullet 2's full evidentiary detail is preserved in its new
Known Issues entry, not lost or compressed away; the checkers above report no new
finding.

## Out of scope
This file's other sections beyond `## Implementation Notes` and its main body; actually
unifying the RAG exception hierarchy (explicitly out of scope per bullet 2's own text);
any other design doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260919-220649 | 20260919-220649 | Classify and apply action for 3 real bullets; bullet 2 expected Known Issues Re-verified all 3 bullets against current source (RagRerankError/RagPipelineError locations, pipeline.py catch tuple, exceptions.py's 7 classes, no ADR documents the rationale) -- all still accurate. Bullet 1: Delete. Bullet 2: Move to Known Issues, reserved CI-018 (created by row 21); full evidentiary detail (3 commit hashes) handed to row 21's entry; found this file's main body 'Known hierarchy deviation' subsection already cross-referenced the old Implementation Notes line number -- corrected that cross-reference to point to CI-018 instead. Bullet 3: Retain, promoted into the ## RagPipeline table as a new row. |
| 2 | Add or update tests per Validation plan | Completed | 20260919-220649 | 20260919-220649 | N/A: documentation-only, no test to add N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260919-220649 | 20260919-220649 | check_docs_quality.py, check_docs_structure.py check_docs_quality.py: no issues found; check_docs_structure.py: all checks passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260919-220649 | 20260919-220649 | N/A: this document's own Target file IS the documentation being updated Edited this file's own Implementation Notes + main body only; governance-doc counterpart entry filed by row 21 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-003, REQ-004 (classify 3 real bullets; bullet 2 expected Move to Known Issues)
- **Source issue**: issues/20260919-193722_impln01_audit-and-reclassify-docs-implementation-notes-items-per-existing-decision-categories.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-194628_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-195506
- **Related target files**: docs/03_rag_05_4-error-handling-reference.md