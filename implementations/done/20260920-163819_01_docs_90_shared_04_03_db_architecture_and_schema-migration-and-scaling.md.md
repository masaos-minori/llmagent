## Goal
Remove the three `CREATE TABLE` DDL blocks (lines 51-61, 63-71, 73-79) in
`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`'s "8b.
Incremental Migration for `eventbus.sqlite`" section, replacing them with a pointer to
`scripts/eventbus/schema.py`/`scripts/eventbus/schema.sql`, per `REQ-001` (Plan
`plans/20260920-160729_plan.md`), so `tools/check_docs_content_policy.py` reports zero
findings for this file while the "Each table serves a distinct purpose" responsibility
bullets remain unchanged.

## Scope
In scope: the three `CREATE TABLE` DDL blocks (lines 51-79) and the lead-in sentence at
line 49, which cites the same stale file path this row's canonical-source pointer
corrects (see Design decisions). Out of scope: "### 8a. Incremental Migrations for
`workflow.sqlite` Only" (lines 36-45, the `db/schema_sql.py` description, not
flagged), the "Each table serves a distinct purpose" bullets (lines 81-84, retained
unchanged), and every other section of this file — none of these were flagged by
`check_docs_content_policy.py` (re-confirmed 2026-09-20). Also out of scope: the two
pre-existing missing `## Related Documents`/`## Keywords` findings recorded in the
Plan.

## Assumptions
The three findings (lines 51, 63, 73) and the file's exact current content
(re-verified via Read during this document's creation) have not shifted since the Plan
was frozen — no commit has touched this file, `scripts/eventbus/schema.py`, or
`scripts/eventbus/schema.sql` since.

## Design decisions
Step 3a's re-verification found the lead-in sentence at line 49 itself repeats the
Plan's own corrected finding: it cites `scripts/eventbus/db.py::_migrate()` (confirmed
by the Plan, and re-confirmed here, to not exist in `db.py`) and a specific line range
in `_init_schema()` (`"line 67–70"`), violating `skills/DESIGN.md` "No source-code line
numbers" independently of the DDL-restatement finding. Since `REQ-001`'s whole purpose
is to add a pointer to the *correct* canonical source
(`scripts/eventbus/schema.py`/`schema.sql`), leaving line 49's incorrect `db.py`
citation in place immediately above that corrected pointer would be self-contradictory
within the same section. This row therefore corrects line 49's file reference and
drops its stale line-number citation as part of implementing `REQ-001`'s pointer — not
as a separate, unauthorized scope expansion, but as the minimum edit needed for the new
pointer to be internally consistent with the sentence introducing it.

## Alternatives considered
- Leave line 49 unedited and add the corrected pointer only where the DDL blocks were:
  rejected — this would produce a section stating `db.py::_migrate()` in one sentence
  and pointing to `schema.py`/`schema.sql` in the very next, an internal contradiction
  a reader would have no way to resolve.
- Also correct the analogous historical citation pattern elsewhere in this file (none
  found in "### 8a" during this row's Read) or in other files referencing
  `eventbus.sqlite` migration: rejected as exceeding this row's frozen scope — this
  Plan's `Implementation Target Files` names only this one file; a repository-wide
  stale-reference sweep is a separate task.

## Implementation
### Target file
`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Read lines 36-84 to confirm current content matches the Plan's recorded evidence.
2. Replace line 49 ("`scripts/eventbus/db.py::_migrate()` performs incremental,
   additive schema evolution on `eventbus.sqlite` at every EventBus service startup. It
   is called from `open_db()` when the `events` table already exists (see
   `_init_schema()` line 67–70).") with a corrected sentence naming
   `scripts/eventbus/schema.py::_migrate()`, called from `_init_schema()` when the
   `events` table already exists — omitting the stale line-number citation.
3. Replace the three DDL code blocks (lines 51-61, 63-71, 73-79) with one sentence: the
   base schema for `events`, `consumer_delivery`, and `consumer_offsets` is defined in
   `scripts/eventbus/schema.sql`; see `scripts/eventbus/schema.py` for the additive
   migration logic that creates `consumer_delivery`/`consumer_offsets` on existing
   databases.
4. Leave the "Each table serves a distinct purpose" bullets (lines 81-84) and every
   other line unchanged.

### Method
Single localized `Edit`, replacing lines 49-79 (the lead-in sentence through the last
DDL block) with the corrected sentence (Procedure step 2) followed by the
canonical-source pointer sentence (Procedure step 3). Do not touch lines 81-84 or any
content outside this range.

### Details
Do not restate any column name/type from the three removed `CREATE TABLE` blocks
(`seq`, `event_id`, `topic`, `payload`, `producer_id`, `created_at`, `consumer_id`,
`acked_at`, `offset`, etc.) — all are directly readable from
`scripts/eventbus/schema.sql`/`scripts/eventbus/schema.py`. Do not reintroduce a
specific line-number citation for `_init_schema()` — per `skills/DESIGN.md` "No
source-code line numbers," name the function, not a line range. Retain the "Each table
serves a distinct purpose" bullets verbatim — they are design-intent (responsibility
per table), not code-derivable schema detail.

## Compatibility considerations
`N/A: documentation-only change, no code, public interface, or data format is affected`.

## Security considerations
`N/A: no security-relevant content is touched`.

## Rollback considerations
Revert via `git checkout` on this one file. This is the Plan's only target file, so
this edit is independently revertable without affecting any other Plan.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` — confirm zero findings for
  `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` (Plan
  `AC-1`).
- `uv run python tools/check_docs_quality.py`, scoped to this file — confirm no new
  warning is introduced.
- `uv run python tools/check_docs_structure.py docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`
  — confirm the finding count does not exceed the two pre-existing findings already
  recorded in the Plan (Plan `AC-2`).
- Manual spot-check: confirm the corrected sentence cites `scripts/eventbus/schema.py`
  and `scripts/eventbus/schema.sql`, not `scripts/eventbus/db.py`.

## Completion criteria
Line 49 correctly names `scripts/eventbus/schema.py::_migrate()` (not `db.py`) with no
line-number citation; none of the three `CREATE TABLE` DDL blocks remains; the "Each
table serves a distinct purpose" bullets are unchanged; `check_docs_content_policy.py`
reports zero findings for this file.

## Out of scope
- "### 8a. Incremental Migrations for `workflow.sqlite` Only" and every other section
  of this file (see Scope) — not flagged, not part of `REQ-001`.
- The two pre-existing missing `## Related Documents`/`## Keywords` findings — tracked
  in the Plan as pre-existing, out-of-scope structural findings.
- A repository-wide sweep for other stale `scripts/eventbus/db.py::_migrate()`
  references outside this file (see Alternatives considered) — not found in this file
  during this row's investigation; not this Plan's scope to search elsewhere.
- Any other `docs/*.md` file — this is this Plan's only target-file row.
- Extending `check_docs_content_policy.py`'s detection rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-171844 | 20260920-171844 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-171844 | 20260920-171844 | N/A: documentation-only, no automated test beyond the doc checkers already listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-171844 | 20260920-171844 | Scoped to the doc checkers in Validation plan, not the full Python toolchain (no `scripts/` change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-171844 | 20260920-171844 | N/A: this document IS the documentation change |

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
- **Requirement ID**: `REQ-001` — remove the three CREATE TABLE DDL blocks and correct the stale canonical-source reference
- **Source issue**: issues/20260920-154640_dcp013_shared-db-docs-remove-ddl-restated-in-prose.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-160729_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-163819
- **Related target files**: docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md