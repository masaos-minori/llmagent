## Goal
Align the overview's "Scope of sqlite-vec Extension Application" paragraph with the amended rule (`REQ-002`).

## Scope
- The one paragraph under the heading "Scope of sqlite-vec Extension Application".

## Assumptions
- The scope rule is the one in the amended ADR-008 (sqlite-vec loaded by default for `rag` and `session`).

## Design decisions
- Change only the sentence(s) that state the scope or default; keep the surrounding structure and links.

## Alternatives considered
N/A: wording change only.

## Implementation
### Target file
`docs/01_overview/overview_01_03-arch-features.md`

### Procedure
1. Replace the passage below with the new wording using Edit.
2. Run the documentation checkers.

### Method
- Old text (exact): "`SQLiteHelper` in `db/helper.py` loads the `sqlite-vec` extension (`vec0.so`) only when `target=\"rag\"`. It is NOT applied to `session`, `workflow`, or `eventbus` databases. This intentional separation restricts vector operations to the RAG database. (Explicit in code — `db/helper.py`)"
- New text: "`SQLiteHelper` in `db/helper.py` loads the `sqlite-vec` extension (`vec0.so`) by default only for the databases that own a vec0 table: `rag` (`chunks_vec`) and `session` (`memories_vec`). It is NOT applied to `workflow` or `eventbus` databases, and an explicit `load_vec` argument overrides the default. This intentional separation restricts vector operations to the two databases that own vector tables. (Explicit in code — `db/helper.py`)"

### Details
- Write in English; no line numbers or concrete configuration values (`skills/DESIGN.md`).

## Compatibility considerations
N/A: wording change only; no other document restates the replaced sentence differently (see the Plan's Implementation Target Files rows for the sibling documents).

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit (documents and the `SQLiteHelper` default must be reverted together to stay consistent).

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py --strict`
- `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_docs_consistency.py --domain overview`

## Completion criteria
- The passage states that `rag` and `session` load sqlite-vec by default and `workflow` and `eventbus` do not.
- All documentation checkers pass.

## Out of scope
- Any file other than the target file
- Code, tests, or configuration changes

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the passage with the new wording | Completed | 20261019-101422 | 20261019-101422 |  |
| 2 | Run the documentation checkers named in `routing.md` Tools (docs quality, structure, content policy, consistency for the touched domain) | Completed | 20261019-101422 | 20261019-101422 | N/A: no tests; docs checkers passed |

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
- **Requirement ID**: `REQ-002` (align the overview)
- **Source issue**: issues/20261019-092704_mem001_session-sqlite-vec-not-loaded-at-runtime.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-094625_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-095521
- **Related target files**: docs/01_overview/overview_01_03-arch-features.md