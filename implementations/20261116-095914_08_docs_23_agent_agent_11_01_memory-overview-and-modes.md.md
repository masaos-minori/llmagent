## Goal

State in the memory overview that recalled memory is injected as data under a fixed framing statement on both paths, never as instructions (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the passage in `docs/23_agent/agent_11_01_memory-overview-and-modes.md` that describes injection at session start (the importance threshold and pinned entries).
- Out of scope: the rest of the document, the generated memory module reference, other documents, and any marker text beyond the existing header name.

## Assumptions

- Execute after documents `01` to `03` of this Plan so the text describes landed behavior.
- The passage describes the importance threshold and pinned entries for session-start injection without the framing (re-read in Step 3a); the per-turn path is not described there.
- The generated reference `docs/23_agent/agent_11_04_memory-module-reference-generated.md` lists classes of `snippet_filter.py`; no class is added, so it needs no change.
- Plan overlap judgment: no other Frozen Plan targets this document.

## Design decisions

- Add one or two sentences of policy after the pinned-entries bullet: recalled memory is injected into the system role as data under a fixed framing statement, on session start and on each turn, and is neutralized to single-line text; it is never an instruction. Refer to the trust-boundary document for the residual risk instead of repeating it. No limits, marker texts or file lists (`skills/DESIGN.md` Docs content policy).

## Alternatives considered

N/A: documentation-only row.

## Implementation
### Target file
`docs/23_agent/agent_11_01_memory-overview-and-modes.md`

### Procedure
1. Add the injection rule after the session-start injection bullets, in English, with a link to the trust-boundary document only if that document is already linked from this file's front matter or body; otherwise name it in plain text.
2. Run the documentation checkers named in the Validation plan and fix findings in the added text only.

### Method
- Reuse existing terms (session start, per-turn injection, memory snippet); introduce no identifiers.

### Details
- Leave front matter, the Keywords section and other bullets untouched; do not add a new related-document entry unless `check_docs_structure.py` requires it.

## Compatibility considerations

N/A: documentation-only; no document is renamed or moved.

## Security considerations

N/A: the text states a security-relevant rule; it adds no secrets or values.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_11_01_memory-overview-and-modes.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

- The document states that recalled memory is injected as data under a fixed framing statement on both paths and never as instructions (`REQ-006`, AC-6); all checkers above report no finding.

## Out of Scope

- Code, tests, the generated reference, other documents, and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the injection rule to the session-start injection passage | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` (memory overview states the injection rule)
- **Source issue**: issues/20261115-214901_startrev001_memory-prompt-injection-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-221435_startrev001_memory-prompt-injection-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095914
- **Related target files**: `docs/23_agent/agent_11_01_memory-overview-and-modes.md`
