## Goal

Expand `docs/03_rag_05_4-error-handling-reference.md`'s Implementation Notes section to explain *why* the RAG layer's exception hierarchy is fragmented (three independent refactoring commits each introduced their own exception class without unifying under `RagLayerError`), and add a non-binding future-unification note, without implementing the actual hierarchy consolidation (REQ-001, REQ-002).

## Scope

- Add to the existing Implementation Notes bullet (line 79 of `docs/03_rag_05_4-error-handling-reference.md`) an explanation of why the fragmentation exists (citing the three originating commits) and a brief note on what a future unification would involve
- Do NOT actually consolidate `RagRerankError`/`RagPipelineError`/`RagExpansionError` under `RagLayerError` (a source-code change affecting exception handling across `scripts/rag/llm_prompts.py`, `scripts/rag/pipeline.py`, and every `except` clause catching these types — confirmed non-trivial and explicitly out of scope per the user's direction for this Plan)

## Assumptions

- The three `git log -S` searches performed this cycle found each exception class's true introduction point (not a later rename or re-definition that would make an earlier commit the more accurate citation) — confirmed by each search returning the class definition's first appearance with matching context
- No ADR or other design document already explains this fragmentation's rationale (confirmed via `grep -rL` scoped to `docs/adr/` for all 4 exception class names)
- The Issue's claim that the note is not "clearly connected to the main error handling tables" is only partially accurate: the `RagPipeline` table (lines 66-73) does reference `RagRerankError` directly (line 73), and the Implementation Notes bullet about it (line 77) explains how it's caught — so a connection exists for that one exception

## Design decisions

1. Cite the actual originating commits rather than write a generic "this happened over time" note — concrete evidence (commit hashes, what each was actually refactoring) is more useful to a future reader deciding whether unification is worth pursuing than a vague acknowledgment
2. Keep the unification note brief (what it would require, not a scheduled plan) — per user direction, this Plan documents the situation rather than committing the project to a future migration; a full migration plan would need its own Issue→Plan cycle once someone decides to pursue it

## Alternatives considered

1. Actually consolidating `RagRerankError`/`RagPipelineError`/`RagExpansionError` under `RagLayerError` — rejected because it is a source-code change affecting exception handling across `scripts/rag/llm_prompts.py`, `scripts/rag/pipeline.py`, and every `except` clause catching these types — confirmed non-trivial and explicitly out of scope per the user's direction for this Plan
2. Writing a detailed, scheduled migration plan — rejected because this Plan adds a brief forward-looking note, not a project plan with target files/timeline — per Design decision above

## Implementation

### Target file

`docs/03_rag_05_4-error-handling-reference.md`

### Procedure

1. Confirm the three originating commits are still accurate
2. Expand the Implementation Notes bullet with fragmentation cause and unification note

### Method

Phase 1: Preparation — confirm evidence line numbers
- Re-run `git log -S "class RagLayerError"`/`"class RagRerankError"`/`"class RagPipelineError"` to reconfirm the commit hashes and messages are still accurate before citing them (REQ-001; `docs/03_rag_05_4-error-handling-reference.md`)

Phase 2: Core Logic — expand the Implementation Notes bullet
- Add the fragmentation's cause (3 commits, what each was refactoring) to the existing bullet at line 79 (REQ-001; `docs/03_rag_05_4-error-handling-reference.md`)
- Add a brief unification-requirements note (REQ-002; `docs/03_rag_05_4-error-handling-reference.md`)

### Details

**Phase 1:** Verify via read/grep that:
- `RagLayerError` at `exceptions.py:11` — base class with 6 subclasses (`EmbeddingSchemaError`, `PipelineValidationError`, `SearchQueryError`, `ChunkFormatError`, `TokenizationError`, `UnknownMetadataError`)
- `RagRerankError` at `llm_prompts.py:56` — inherits from `RuntimeError`, NOT under `RagLayerError`
- `RagExpansionError` at `llm_prompts.py:52` — inherits from `RuntimeError`, NOT under `RagLayerError`
- `RagPipelineError` at `pipeline.py:59` — inherits from `RuntimeError`, NOT under `RagLayerError`
- Originating commits confirmed via `git log --reverse --oneline -S`:
  - `afbfe2915 refactor(rag): Phase 1-3 — backward-compat removal, foundation files, dataclass migration` — introduced `RagLayerError` and its 6 subclasses
  - `b20e136d8 refactor(rag): split llm.py (413→42+260+245 lines) into prompts + client` — introduced `RagRerankError` and `RagExpansionError`
  - `e4152f361 refactor(rag): pipeline/stages fail-fast — remove expand_queries_safe, except Exception fallbacks, add RagPipelineError` — introduced `RagPipelineError`
- No ADR references any of the 4 exception classes (confirmed via `grep -rl` across `docs/adr/` returning no match)

**Phase 2:** Extend the existing Implementation Notes bullet at line 79:

Replace:
```markdown
- The actual exception classes defined in `scripts/rag/exceptions.py` are 7 types: `RagLayerError` (base) / `EmbeddingSchemaError` / `PipelineValidationError` / `SearchQueryError` / `ChunkFormatError` / `TokenizationError` / `UnknownMetadataError`. `RagRerankError` and `RagPipelineError` are not included here (both are individually defined in `llm_prompts.py` and `pipeline.py` respectively). The exception hierarchy is not unified under a single base class across the entire rag layer.
  [Explicit in code]
```

With:
```markdown
- The actual exception classes defined in `scripts/rag/exceptions.py` are 7 types: `RagLayerError` (base) / `EmbeddingSchemaError` / `PipelineValidationError` / `SearchQueryError` / `ChunkFormatError` / `TokenizationError` / `UnknownMetadataError`. `RagRerankError` and `RagPipelineError` are not included here (both are individually defined in `llm_prompts.py` and `pipeline.py` respectively). The exception hierarchy is not unified under a single base class across the entire rag layer. **Cause**: This fragmentation arose from three independent refactoring efforts at different times, each introducing its own exception class without referencing the others':
  - `afbfe2915 refactor(rag): Phase 1-3 — backward-compat removal, foundation files, dataclass migration` — introduced `RagLayerError` and its 6 subclasses as the foundational error hierarchy.
  - `b20e136d8 refactor(rag): split llm.py (413→42+260+245 lines) into prompts + client` — introduced `RagRerankError` and `RagExpansionError` (both inherit from `RuntimeError`, not `RagLayerError`).
  - `e4152f361 refactor(rag): pipeline/stages fail-fast — remove expand_queries_safe, except Exception fallbacks, add RagPipelineError` — introduced `RagPipelineError` (inherits from `RuntimeError`, not `RagLayerError`).
  No ADR or design document records a rationale for keeping them separate; the fragmentation is a byproduct of independently-scoped refactors, not a deliberate architectural decision. **Future unification** would require touching every `except` clause across `scripts/rag/` that currently catches `RagRerankError`/`RagPipelineError`/`RagExpansionError`/`RuntimeError` by name — a cross-cutting change outside the scope of a documentation fix.
  [Explicit in code]
```

## Compatibility considerations

This is a documentation-only expansion. No backward compatibility concerns.

## Security considerations

No security impact — documentation correction/expansion only. However, accurately documenting the state of the exception hierarchy is important for readers who may rely on it to understand the pipeline's error handling posture.

## Rollback considerations

Simple revert: restore the original Implementation Notes bullet text. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_05_4-error-handling-reference.md | Manual — verify cited commits against `git log` | `git log -1 --format="%H %s" <hash>` for each cited commit | Each citation matches the actual commit |

## Completion criteria

- [ ] The Implementation Notes cite all 3 originating commits and what each was actually refactoring (REQ-001)
- [ ] The Implementation Notes state the fragmentation is a byproduct of independent refactors, not a deliberate design decision, and that no ADR documents a rationale for the separation (REQ-001)
- [ ] The Implementation Notes include a brief statement of what unification would require (touching every relevant `except` clause across `scripts/rag/`), without a schedule or numbered migration plan (REQ-002)

## Out of scope

- Actually consolidating `RagRerankError`/`RagPipelineError`/`RagExpansionError` under `RagLayerError` (a source-code change affecting exception handling across `scripts/rag/llm_prompts.py`, `scripts/rag/pipeline.py`, and every `except` clause catching these types — confirmed non-trivial and explicitly out of scope per the user's direction for this Plan)
- Writing a detailed, scheduled migration plan (this Plan adds a brief forward-looking note, not a project plan with target files/timeline — see Design)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Confirm three originating commits | Pending | — | — | |
| 2 | Phase 2: Expand Implementation Notes bullet | Pending | — | — | |
| 3 | Verification: manual review | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260913-183013_missing_error_handling_ref_impl_notes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-205453_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-071717
- **Related target files**: docs/03_rag_05_4-error-handling-reference.md
