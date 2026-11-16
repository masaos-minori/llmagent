## Goal

State in the lifecycle design document what a later start does with a process whose failed start was not confirmed stopped (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `### Implementation Note (Shutdown Termination)` paragraph of `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`.
- Out of scope: any other section, any code, and any concrete value (timeouts, ports, counts).

## Assumptions

- Execute after document `01` of this Plan, so the text describes landed behavior.
- The paragraph already documents `TerminationOutcome` and the retained tracking for an unconfirmed exit and says nothing about a later start (re-read in Step 3a). The Issue named another document; the Plan corrected the target to this file.
- Plan overlap judgment: no other Frozen Plan targets this document.

## Design decisions

- Add policy only: a process left by a failed start with an unconfirmed exit stays tracked, is re-terminated by a later start and is never reused, a start proceeds fresh only after a confirmed exit, and otherwise raises the startup failure again (`skills/DESIGN.md` Docs content policy: no values, no file lists, no counts, no implementation-location mapping beyond what the paragraph already has).

## Alternatives considered

N/A: documentation-only row.

## Implementation
### Target file
`docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`

### Procedure
1. Append two or three sentences to the end of the `Implementation Note (Shutdown Termination)` paragraph describing the later-start rule above, in English.
2. Run the documentation checkers named in the Validation plan and fix any finding in the added text only.

### Method
- Keep the paragraph's existing terms (`TerminationOutcome`, unconfirmed exit, tracking kept) and add no new identifiers.
- Mark the statement as explicit in code only if the file's existing convention does so for this paragraph (it uses plain prose here).

### Details
- Do not touch the Keywords section or front matter; no new link is added.

## Compatibility considerations

N/A: documentation-only; no document is renamed or moved.

## Security considerations

N/A: no secrets or values are added.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain mcp`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

- The paragraph states that a process left by a failed start with an unconfirmed exit is not reused by a later start (`REQ-005`, AC-5), and all checkers above report no finding.

## Out of Scope

- Code and tests, other documents, and wording changes outside the one paragraph.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the later-start rule to the shutdown termination note | Pending | — | — | |
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
- **Requirement ID**: `REQ-005` (lifecycle document states the later-start rule)
- **Source issue**: issues/20261115-214903_startrev003_retry-reuses-unconfirmed-process.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-220300_startrev003_retry-reuses-unconfirmed-process.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-094943
- **Related target files**: `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`
