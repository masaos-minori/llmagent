## Goal

Remove the `rag_corpus_meta` seed insert from the recovery drill tests (`REQ-008`).

## Scope
**Release unit**: corpus-meta-removal

## Verification Findings (2026-11-13)
- Seed timing: the seed deletion must execute in the same cycle as seq 13 (DDL removal).
  While the seq 10 probe and the seq 13 DDL still exist, dropping the seed makes the drill's
  fail-closed logical layer report a fatal missing meta row (same failure mode proven in the
  `test_init_db_schema_gate` drill on 2026-11-13); after seq 13 the INSERT targets an absent
  table. The stale `corpus_meta_verified` kwarg and any meta-specific test edits go with the
  seq 10/11/12 cycle.
- Seed: comment at lines 101-102 plus the `INSERT INTO rag_corpus_meta` at 103-108 (Plan cites
  101-104; the current block is 101-108). The seed applies to both `prod` and non-`prod`
  fixture paths (it runs after either DDL script).
- Additional reference the Plan row does not list: `corpus_meta_verified=True,` kwarg at line
  369 in a `RagConsistencyReport(...)` fixture. The `corpus_meta_verified` field is removed
  from the DTO by seq 12; the kwarg then references a removed construct (pydantic v2 default
  `extra='ignore'` would silently drop it, and it violates AC-10 either way), so it must be
  dropped in the same cycle. The test's fail-closed behavior is driven by
  `fk_unverified=True`, not by this kwarg.

## Assumptions
- The drill inserts a row into `rag_corpus_meta` as part of its fixture setup (~lines
  101-104).

## Design decisions
- Delete the `rag_corpus_meta` seed insert; keep every other drill seed.

## Alternatives considered
N/A: removal is the decided Option B; the drill seeds a table that no longer exists.

## Implementation
### Target file
`tests/db/test_recovery_drill.py`
### Procedure
- Remove the `rag_corpus_meta` seed block (comment 101-102 and the INSERT at 103-108).
- Remove the `corpus_meta_verified=True,` kwarg (line 369).
### Method
Targeted deletions; confirm no remaining reference to `corpus_meta` in the file.
### Details
- The DDL table is removed by seq 13; delete together so the drill builds a valid schema.

## Compatibility considerations
N/A: test-only; the table is dropped from the canonical DDL by the sibling code document.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- Scoped: `rg -n "corpus_meta|unverifiable corpus" tests/db/test_recovery_drill.py` returns
  nothing. The cross-file search over `scripts tests` only passes at release-unit end.
- `uv run pytest tests/db` passes.

## Completion criteria
The `rag_corpus_meta` seed is gone; the drill tests build a valid schema and pass.

## Out of Scope
The DDL table (`REQ-008`, seq 13) and the schema test (companion, covered by seq 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113 | 20261113 | kwargs/test trims done in seq10-12 cycle 20261113; seed deletion deferred to seq 13 cycle seq13 lockstep cycle 20261113 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113 | seq13 lockstep cycle 20261113 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113 | seq13 lockstep cycle 20261113 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113 | seq13 lockstep cycle 20261113 |

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
- **Requirement ID**: `REQ-008`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `tests/db/test_recovery_drill.py`