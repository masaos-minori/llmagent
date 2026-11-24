## Goal
Amend ADR-008 into "Separation and Lifecycle Policy for Six SQLite Stores": consistent six-store wording, lifecycle matrix, Repository Context and Episodic Memory, no memory JSONL, and EventBus retention referred to ADR-006 (REQ-004 six stores; REQ-005 memory design; REQ-006 EventBus data and retention; REQ-009 invariants; REQ-007 pending bullets).

## Scope
**Release unit**: adr-amendment

- Edits only `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`; the file name does not change (deferred rename, UNK-04).
- Part of the release unit with the ledger, ADR-006, index, authority, and guide documents.

## Assumptions
- New entry AAL-039 (Repository Context and Episodic Memory) exists after the ledger document (06) is applied; AAL-024 is updated there to "six SQLite stores"; AAL-026 and AAL-027 are removed there.
- Episodic Memory table names are not fixed by the Plan, so the ADR uses the generic names "Episodic Memory events" and "Episodic relations" and does not name tables.
- New invariants start at INV-19 (current maximum INV-18); existing invariants INV-02, INV-04, INV-09 are reworded in place.
- Needs confirmation (UNK-03): AAL-025 stays pending; only its `/memory rebuild` and JSONL wording in Decision Detail 22 and the matrix schema-mismatch row is removed.

## Design decisions
- Retention for `eventbus.sqlite` is stated once, in ADR-006; the matrix cell and INV-09 refer to it, so ADR-008 and ADR-006 do not define it twice.
- Unresolved lifecycle policies are recorded as Known Deviations rather than left as ambiguous matrix cells.

## Alternatives considered
N/A: the old memory model and the accepted-growth risk are being withdrawn, not weighed again here.

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. Title: change the H1 (line 25) and front matter `title` to `ADR-008: Separation and Lifecycle Policy for Six SQLite Stores`; align Summary, Scope, Review Triggers, and Verification wording (for example the "four-database boundary" test row text) with six stores, keeping "four platform-domain databases" only where it names them.
2. State the four platform-domain databases and the two non-domain stores; add a Decision Detail prohibiting physical-path sharing, cross-store `ATTACH`, cross-store foreign keys, and schema-qualified cross-store access.
3. Decision Detail 2 and the matrix `session.sqlite` cells: authoritative data is sessions, messages, conversation state, session diagnostics, Episodic Memory events, and Episodic relations; Episodic FTS and Vector indexes are derived. Remove `memories`, `memory_links`, `memories_fts`, `memories_vec`, and `memories.jsonl`.
4. Replace Decision Details 22 (JSONL and `/memory rebuild` part), 23, and 24: 22 keeps the archive-and-recreate rule without the memory JSONL precondition; 23 states per-store retention with EventBus retention defined by ADR-006 and no accepted unbounded-growth risk; 24 becomes Repository Context (configured repository files are the source of truth, not stored in SQLite or JSONL, no persistent FTS or Vector index) and Episodic Memory (the only persistent Agent long-term memory, generated internally, no user-facing CRUD, recoverable only from verified SQLite backup). Remove Semantic Memory, User Semantic, pin state, manual memory writes, and `/memory` data from the policy.
5. Recovery Policy Matrix: update the System of record, Derived data, Schema-mismatch, and Retention rows; add Capacity monitoring, Failure mode, and Verification rows for all six stores so every lifecycle field the Issue lists is answered per store (Owning component already exists); remove `events.jsonl`, JSONL writers, JSONL recovery, and JSONL count comparisons.
6. Invariants: reword INV-02 (Episodic Memory in `session.sqlite`), INV-04 (EventBus authoritative data per ADR-006), INV-09 (retention policy per store; no accepted unbounded growth); append INV-19 (six-store separation and prohibited cross-store access), INV-20 (Repository Context is not persisted), INV-21 (Episodic Memory is stored only in `session.sqlite` and recovered only from verified backup), INV-22 (no JSONL memory path and no EventBus JSONL path).

### Method
- Edit section by section with the Edit tool; keep existing Decision Detail numbers (22 to 24 are rewritten in place, new details are appended).
- Verification: keep the existing test rows that still hold (`tests/tools/test_check_db_separation.py`, `tests/db/test_db_recovery.py`, `tests/db/test_create_schema.py`); mark INV-20 to INV-22 Not verified with expected evidence and cadence (Manual until the implementation issues land). Do not cite a test that does not exist.
- Data Ownership and Persistence and Implementation References: remove the memory table list and add Episodic Memory by generic name.

### Details
- Known Deviations: replace the SHARED-002 `memories_vec` entry, which no longer applies once Semantic Memory is removed (its governance entry is settled by document 06); add deviations for current code (`scripts/agent/memory/` still has the old design and JSONL; the session schema still creates `memories` and `memory_links`) and for lifecycle policies left undecided (for example the Session DB schema-mismatch policy for Episodic Memory).
- Approval Record: keep the AAL-010, AAL-011, AAL-024, AAL-025, and AAL-028 bullets (reword the AAL-024 bullet to "six SQLite stores" to match the updated entry); remove the AAL-026 and AAL-027 bullets; add one pending bullet citing AAL-039. Do not write an approver, a date, or an approval sentence.
- `related` front matter and Related ADRs keep ADR-006 and the existing items; no file name changes.

## Compatibility considerations
N/A: documentation only; behavior differences with current code are recorded in Known Deviations.

## Security considerations
N/A: no authentication or data-exposure change; diagnostics still exclude row-level content (existing Audit row).

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_reference.py`, `uv run python tools/check_adr_invariant_matrix.py` (after the index document is applied).
- `uv run python tools/check_db_separation.py` and `uv run pytest tests/tools/test_check_db_separation.py -q`.
- `uv run python tools/check_adr_preservation.py --base HEAD docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`: only intended findings (UNK-06).

## Completion criteria
- Title, Summary, Scope, body, index entry, and verification scope consistently say six stores; the four platform-domain databases and two non-domain stores are named.
- No Semantic Memory, User Semantic, memory JSONL, pin, manual write, `/memory`, or `events.jsonl` appears as current policy or as a recovery source.
- The matrix answers all lifecycle fields for all six stores, with undecided items under Known Deviations; the Approval Record cites AAL-024, AAL-025, AAL-028, AAL-039 and contains no approval sentence.

## Out of Scope
- Renaming the file; code, schema, and test changes; ledger edits (document 06); other `docs/` files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit ADR-008 title, matrix, Decision Details, invariants, Known Deviations, and Approval Record per Implementation | Pending | — | — | |
| 2 | Run the ADR and DB-separation checks per Validation plan | Pending | — | — | Checkers pass only after documents 01 to 06 are applied (release unit) |

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
- **Requirement ID**: REQ-004 (six stores), REQ-005 (Repository Context and Episodic Memory), REQ-006 (EventBus data and retention), REQ-007 (pending approval bullets), REQ-009 (invariants and Known Deviations)
- **Source issue**: issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-094324_adrdoc001_adr-eventbus-memory-amendment.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-094801
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
