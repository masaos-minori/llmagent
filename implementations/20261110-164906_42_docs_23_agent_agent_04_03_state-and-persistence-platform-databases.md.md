## Goal

State the retired-table behavior accurately in `agent_04_03`: a legacy database carrying the retired
`execution_snapshots` table now fails startup (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Exact fingerprint matching rejects any workflow database carrying the retired `execution_snapshots`
  table (UNK-02 default: fail); the "no effect" claim now conflicts with the mechanism.
- Line 80 is the retired-table statement that calls the empty table harmless.

## Design decisions
- Replace "a legacy database may still carry the empty table and a NULL column with no effect" with a
  statement that such a database fails startup under exact matching and is archived and recreated.

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`

### Procedure
1. Line 80: replace "The former `execution_snapshots` table is retired: no code path ever wrote it,
   fresh databases no longer create it or the `tool_call_state.snapshot_id` foreign key, and a legacy
   database may still carry the empty table and a NULL column with no effect." with "The former
   `execution_snapshots` table is retired: no code path ever wrote it, fresh databases no longer create
   it or the `tool_call_state.snapshot_id` foreign key, and a legacy database that still carries the
   empty table fails startup under exact fingerprint matching and is archived and recreated by the
   operator."

### Method
- Locate the clause with
  `rg -n 'may still carry the empty table and a NULL column with no effect' docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`
  before editing.

### Details
- The `task_nonce` and `tool_call_state` descriptions above line 80 are unaffected.

## Compatibility considerations
Cross-references to db_03_07 and the DB Recreation Procedure remain consistent.

## Security considerations
None beyond the existing Fail-Fast refusal narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run python tools/check_docs_consistency.py --domain agent` passes; no document claims a legacy
table is harmless.

## Completion criteria
Line 80 states that a legacy `execution_snapshots` table makes startup fail; the archive-and-recreate
consequence is named.

## Out of Scope
Deleting the retired-table history or the task-nonce descriptions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | State the retired-table behavior accurately | Completed | — | 20261111-145628 | line 80 'with no effect' claim replaced: a legacy database carrying execution_snapshots fails startup under exact fingerprint matching and is archived and recreated |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-145628 | check_docs_consistency --domain agent: No issues found; no 'no effect'/harmless claim remains in agent_04_03 |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261111-145629 | documentation-only row; task_nonce/tool_call_state descriptions untouched |

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
- **Requirement ID**: `REQ-006` — state the retired-table behavior accurately
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`