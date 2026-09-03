# Define recovery policy for each SQLite persistence domain

## Priority
Medium

## Summary
Define a normative recovery policy for `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, and `eventbus.sqlite`. Separate physical corruption recovery from schema repair, logical repair, index rebuild, and normal initialization.

## Background
The system uses four SQLite persistence domains with different ownership and data-loss consequences. Existing documentation requires independent backup and recovery policies for each database, but the operational behavior is not fully specified.

## Problem
Generic use of the term `recovery` currently mixes schema initialization, migration repair, logical consistency repair, and physical file restoration. `docs/adr/ADR-008-sqlite-4db-separation.md` (confirmed by direct read) does not define `persistence-domain`, `initialization`, `schema-repair`, `logical-repair`, `derived-data-rebuild`, `physical-recovery`, or `operator-restore` as normative terms, even though the actual `scripts/db/recovery.py` implementation already distinguishes several of these concepts informally (e.g. `_classify_error()`'s `DbCondition` enum for physical-recovery classification vs. `create_schema()` for initialization).

## Reason for Change
Without one authoritative terminology and policy matrix, operators and implementers must infer which recovery category a given action belongs to from scattered code and documentation, risking a physical-recovery action being applied where only schema-repair or derived-data-rebuild was intended (or vice versa).

## Implementation Intent
Create one authoritative persistence-domain recovery matrix that defines what actions are allowed, prohibited, or operator-controlled for every database.

### Required terminology

Define and use these terms consistently:

- `initialization`: Create a database or required schema when no valid database exists.
- `schema-repair`: Correct a missing or incompatible schema through an approved migration or initialization path.
- `logical-repair`: Correct application-level inconsistencies while the SQLite file remains physically valid.
- `derived-data-rebuild`: Recreate indexes or other data that can be derived from an authoritative source.
- `physical-recovery`: Restore usability after SQLite file corruption.
- `operator-restore`: Restore a validated backup through an explicit operator-controlled procedure.

Do not use `recovery` without identifying which category is intended.

### Required policy fields

For each database, define:

- Persistence-domain identifier
- Database file
- System of record
- Derived or rebuildable data
- Owning component
- Required service stop scope
- Supported diagnosis path
- Supported recovery source
- Automatic restore allowed or prohibited
- Manual restore allowed or prohibited
- Operator approval requirement
- Backup retention requirement
- WAL checkpoint and backup consistency requirement
- Physical integrity verification
- Database-specific logical verification
- Service restart condition
- Rollback condition
- Audit requirement
- Data-loss disclosure requirement

### Required database coverage

#### `rag.sqlite`

Document the relationship among documents, chunks, FTS data, and vector data. Explicitly identify which data is authoritative and which data may be rebuilt.

#### `session.sqlite`

Document recovery impact on sessions, messages, memories, diagnostics, and links. Define how loss between the backup point and failure time is reported.

#### `workflow.sqlite`

Keep automatic physical restoration prohibited unless an approved architectural decision changes that policy (confirmed current policy: ADR-008 Decision Details #20, `no_recovery_allowed`). Define operator ownership of task, attempt, approval, artifact, and processed-event recovery.

#### `eventbus.sqlite`

Keep automatic physical restoration prohibited unless an approved architectural decision changes that policy (confirmed current policy: ADR-008 Decision Details #20, `no_recovery_allowed`). Define how events, consumer offsets, acknowledgements, delivery state, and DLQ state are reconciled.

## Target Files or Areas
- `docs/adr/ADR-008-sqlite-4db-separation.md`
- DB architecture and schema documents
- DB recovery and operations documents
- Area document guides
- `scripts/db/recovery.py`
- `scripts/db/maintenance.py`
- `scripts/db/create_schema.py`
- Workflow schema and migration code
- EventBus schema and migration code
- Backup and rotation configuration

If the paths differ, locate the corresponding original files before editing.

## Required Changes
1. Locate the canonical ADR and DB operations documents.
2. Add the persistence-domain recovery matrix to one canonical source.
3. Replace ambiguous uses of `recovery` with the defined terms.
4. Ensure schema initialization is not described as physical corruption recovery.
5. Explicitly state that startup diagnosis and restoration are separate operations.
6. Define fail-closed behavior when a policy or recovery source is missing.
7. Update related guides and references to link to the canonical policy rather than duplicating it.
8. Do not change runtime behavior in this issue unless needed to correct a direct contradiction in constants or enums that encode the policy.

## Constraints
Do not change runtime behavior in this issue unless needed to correct a direct contradiction between the new normative terminology and an existing constant or enum that encodes recovery policy.

## Acceptance Criteria
- [ ] All four SQLite persistence domains have explicit recovery policies.
- [ ] Physical recovery is clearly separated from initialization, schema repair, logical repair, and derived-data rebuild.
- [ ] Each database has an identified system of record and owning component.
- [ ] Each database has an explicit recovery source or an explicit statement that no recovery source exists.
- [ ] Automatic restore permission is explicitly defined for every database.
- [ ] `workflow.sqlite` automatic restore remains prohibited under the current approved policy.
- [ ] `eventbus.sqlite` automatic restore remains prohibited under the current approved policy.
- [ ] Operator approval requirements are explicit.
- [ ] Post-restore physical and logical verification requirements are explicit.
- [ ] Startup diagnosis is not described as automatic restoration.
- [ ] Ambiguous recovery terminology is removed from active documentation.
- [ ] Related documents reference one canonical policy instead of duplicating it.
- [ ] Documentation validation tests pass.

## Testing Expectations
Not required beyond documentation validation — run `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` against the edited documents.

## Documentation Impact
Yes — this issue's entire scope is the governance/ADR/DB documentation listed in Target Files or Areas. The new terminology and matrix become the normative vocabulary `H-07-07`, `H-07-08`, and `H-07-09` (filed alongside this issue) reference.

## Out of Scope
- Do not implement backup validation in this issue.
- Do not implement atomic replacement in this issue.
- Do not write the full Workflow or EventBus runbook in this issue.
- Do not enable automatic startup restoration.

## Dependencies
N/A: none. This issue defines the policy required by `H-07-07`, `H-07-08`, and `H-07-09`.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Read `docs/adr/ADR-008-sqlite-4db-separation.md` and `scripts/db/recovery.py` in full before drafting the matrix — confirm each policy field against the actual current implementation (e.g. `DbCondition`'s existing states, `_restore_from_backup()`'s actual sequence) rather than inventing policy from scratch. Do not restate SHARED-001/SHARED-002's already-resolved implementation details (`docs/90_shared_90_inconsistencies_and_known_issues.md`) as if they were undecided — cite them as evidence for the matrix's `physical-recovery` row instead. Do not change runtime behavior unless correcting a direct contradiction.
