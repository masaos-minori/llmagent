## Goal

Restate the stale single-database, privileges, and re-evaluation statements in ADR-005 so they
describe the current per-process SQLite layout.

## Scope
**Release unit**: N/A: not part of a release unit

- Only the Constraints, Assumptions and Security Consequences statements are restated.

## Assumptions

- `rag.sqlite` ownership is taken from `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
  Decision Detail 1 ("Owned by the RAG layer"), which is the repository authority for the layout.

## Design decisions

- No ADR number is named in the replacement wording: ADR-008 is not in this file's front matter
  `related`, and adding a `related` entry is a decision-text change (the `AAL-009` precedent).
- The privileges statement keeps the repository's existing trust-boundary phrasing pattern ("granted
  only within each process", used by ADR-002, ADR-004 and ADR-007) instead of naming an
  authentication mechanism this ADR does not govern.

## Alternatives considered

- Naming ADR-008 and the MCP Bearer authentication boundary in the wording: rejected for this
  document because it would require a `related` entry and a pending amendment of its own.

## Implementation
### Target file
`docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`

### Procedure
Replace the Constraints single-database line, the Assumptions target-environment, trust-boundary and
re-evaluation lines, and the Security Consequences trust-boundary line.

### Method
Line-level replacement in the Constraints, Assumptions and Security Consequences sections.

### Details

- Constraints: "Multiple tables coexist in a single SQLite database" becomes "Multiple derived-index
  tables coexist in `rag.sqlite`".
- Assumptions: "Target environment: a single host, a single SQLite database" becomes "Target
  environment: a single host; the RAG layer owns `rag.sqlite` under the repository's per-process
  SQLite database separation".
- Trust boundary (Assumptions and Security Consequences, both occurrences): "Trust boundary:
  privileges are granted only within the processes of the RAG layer, not within SQLite".
- Re-evaluation line: "multi-DB configuration," is removed, leaving "distributed execution,
  integration with an external index store".

## Compatibility considerations

- Decision text, Invariants, Verification and Completion Checklist are untouched; no cited test
  changes.

## Security considerations

- N/A: wording only; the statement describes where privileges apply.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_structure.py`, `check_docs_content_policy.py`,
  `check_adr_structure.py`, `check_docs_consistency.py --domain rag`.
- `grep -n "only within SQLite\|multi-DB configuration" docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`
  returns nothing.

## Completion criteria

- No sentence in the file says the RAG derived indexes live in a single shared database, and no line
  says privileges are granted within SQLite.

## Out of Scope

- RAG code, tests, and the guide documents under `docs/21_rag/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the five statement replacements in Implementation > Details | Completed | 20261120-163733 | 20261120-163733 | Trust-boundary replacement applied to both occurrences |
| 2 | Run the docs and RAG-domain checkers in the Validation plan | Completed | 20261120-163733 | 20261120-163733 | `check_docs_consistency.py --domain rag`: no findings |

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
- **Requirement ID**: `REQ-005` (current per-process database layout), `REQ-006` (no
  privileges-only-within-SQLite statement)
- **Source issue**: issues/20261117-123016_adrchk016_adr006-boilerplate-fixes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-155214_adrchk016_adr006-boilerplate-fixes.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-162706
- **Related target files**: `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`