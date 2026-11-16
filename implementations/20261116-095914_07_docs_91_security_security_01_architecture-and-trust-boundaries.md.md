## Goal

State in the trust-boundary table that memory content is untrusted data, how it is framed and neutralized, and the residual risk (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the "Agent → LLM" row of the trust-boundary table in `docs/91_security/security_01_architecture-and-trust-boundaries.md`.
- Out of scope: other rows and sections, other documents (document `08` covers the memory overview), and any marker text beyond the existing header name.

## Assumptions

- Execute after documents `01` to `03` of this Plan so the text describes landed behavior.
- The row lists memory snippets as "PII-redacted and length-limited by `snippet_filter.py`" and nothing else (re-read in Step 3a); it already cites `snippet_filter.py` as code evidence.
- Plan overlap judgment: no other Frozen Plan targets this document.

## Design decisions

- Extend the row with policy only: memory snippets are untrusted data in addition to being PII-redacted and length-limited; they are neutralized to single-line text and placed under a fixed framing statement that marks them as recalled data and not instructions; the framing lowers but does not remove the chance that a model follows instruction-like recalled text, which is an accepted residual risk. No limits, no marker texts other than the existing header name, no file lists (`skills/DESIGN.md` Docs content policy).

## Alternatives considered

N/A: documentation-only row.

## Implementation
### Target file
`docs/91_security/security_01_architecture-and-trust-boundaries.md`

### Procedure
1. Edit the "Agent → LLM" row so the memory-snippet description adds the untrusted-data rule, the neutralization and framing, and one clause on the residual risk, keeping the row on a single table line.
2. Run the documentation checkers named in the Validation plan and fix findings in the changed row only.

### Method
- Keep the existing evidence citation and the second kind of content (MDQ/RAG routing hints) unchanged; keep the table column count.

### Details
- Leave front matter, the Keywords section and all other rows untouched.

## Compatibility considerations

N/A: documentation-only; no document is renamed or moved.

## Security considerations

N/A: the text states a security boundary; it adds no secrets or values.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/91_security/security_01_architecture-and-trust-boundaries.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

- The "Agent → LLM" row states the untrusted-data rule, the neutralization and framing, and the residual risk (`REQ-006`, AC-6); all checkers above report no finding.

## Out of Scope

- Code, tests, other rows or documents, and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the "Agent → LLM" row with the untrusted-data rule, framing and residual risk | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (trust-boundary documentation states the untrusted-data rule)
- **Source issue**: issues/20261115-214901_startrev001_memory-prompt-injection-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-221435_startrev001_memory-prompt-injection-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095914
- **Related target files**: `docs/91_security/security_01_architecture-and-trust-boundaries.md`
