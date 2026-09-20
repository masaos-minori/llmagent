## Goal
Remove `docs/03_rag_02_08_ingestion_pipeline-shared.md`'s hand-maintained
"Used by" Script/Functions-Used table (REQ-007), replacing it with a pointer
to each dependent script's own import statement.

## Scope
In scope: exactly the 1 location named in REQ-007 — the "Used by" table,
lines 68-75 (header "**Used by:**" at line 66).

Out of scope: the `rag.utils` import example (lines 55-63) and section 11
"Note on FTS5 Implementation" (lines 79-83) — both retained unchanged.

## Assumptions
None beyond the Plan's own — this row has no assumptions of its own.

## Design decisions
Replace the table with a one-line pointer stating that each script's own
`from rag.utils import (...)` statement is the current source of truth for
which functions it uses, rather than a hand-maintained cross-reference
table that must be updated in lockstep with 6 other files whenever any one
of them changes its imports.

## Alternatives considered
- Keep the table but add a note that it may go stale — rejected: this
  still leaves the implementation-reference table itself (REQ-007's actual
  target) in place; a staleness caveat does not satisfy "remove," only
  "annotate."

## Implementation
### Target file
docs/03_rag_02_08_ingestion_pipeline-shared.md

### Procedure
1. Replace the table (lines 68-75) with a one-line pointer: "See each
   dependent script's own `from rag.utils import (...)` statement for the
   functions it currently uses."
2. Leave the "**Used by:**" lead-in line (66) unchanged, or fold it into the
   replacement sentence if doing so reads more naturally — either is
   acceptable since it is prose, not a table.

### Method
One `Edit` call (old_string/new_string) replacing the table's header row
through its last data row (and the "**Used by:**" lead-in, if folded per
step 2).

### Details
Preserve the `rag.utils` import code block (lines 55-63) and section 11
"Note on FTS5 Implementation" (79-83) exactly as-is.

## Compatibility considerations
Documentation-only; no public interface, CLI, or data format changes. No
compatibility impact.

## Security considerations
N/A: documentation content change only.

## Rollback considerations
Revert via `git checkout` on this one file, or a follow-up commit reverting
the single Edit — no data migration or state change is involved.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/03_rag_02_08_ingestion_pipeline-shared.md`
- `uv run python tools/check_docs_structure.py docs/03_rag_02_08_ingestion_pipeline-shared.md`
- `uv run python tools/check_docs_content_policy.py` (full-tree; confirm no
  new finding appears for this file — it had 0 automated findings before
  and after, since this table was a manual-only finding; confirm removal by
  direct Read)

## Completion criteria
The "Used by" table no longer exists, replaced by the pointer described in
Design decisions; the import code block and section 11 are unchanged;
`check_docs_quality.py` and `check_docs_structure.py` report no new finding
on this file relative to this Plan's baseline.

## Out of scope
- Any `scripts/rag/**` source file (no code change).
- Any other section of this file not named in Scope above.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the 1 Edit per Procedure/Method | Pending | — | — | |
| 2 | N/A: no test suite applies to a documentation content change | Pending | — | — | |
| 3 | Run the 2 commands in Validation plan | Pending | — | — | |
| 4 | N/A: no further documentation update needed beyond this file itself | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` — remove ingestion_pipeline-shared.md's implementation-reference content
- **Source issue**: issues/20260920-084526_docref01_isolate-implementation-reference-content-from-rag-design-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-094101_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-094739
- **Related target files**: docs/03_rag_02_08_ingestion_pipeline-shared.md
