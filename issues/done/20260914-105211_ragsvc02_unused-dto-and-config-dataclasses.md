# Resolve unused RAG DTO and configuration dataclass status

## Priority
Low

## Summary
`scripts/rag/models_data.py`'s `RegisteredDocument` and seven dataclasses in `scripts/rag/models_config.py` (`MqeConfig`, `FusionConfig`, `RerankConfig`, `SearchConfig`, `ChunkSplitterConfig`, `IngesterConfig`, `PipelineConfig`) have zero references outside their defining module — this issue obtains an owner decision on whether each is a required future component or removable dead code, then acts on that decision, rather than removing them speculatively.

## Background
`docs/00_governance_03_issue-and-uncertainty-management.md` `RAG-003` ("Unresolved usage status of `RegisteredDocument` DTO") and `RAG-004` ("Unresolved usage status of `models_config.py` configuration dataclasses") already track these exact gaps (both Status: open, Severity: Low, both explicitly requiring owner confirmation before action per their `Recommended Action` fields). This issue re-confirms the zero-reference finding against current code and turns it into an actionable task.

## Problem
Re-verified by direct search (word-boundary match, excluding the defining module itself): `RegisteredDocument` has zero references anywhere in `scripts/`. `MqeConfig`, `FusionConfig`, `RerankConfig`, `SearchConfig`, `ChunkSplitterConfig`, and `IngesterConfig` likewise have zero references outside `models_config.py`. Configuration is currently handled via raw `dict` access from TOML files rather than through these dataclasses. Whether this is intentional forward-looking scaffolding (e.g. for a future typed-config migration) or genuinely removable dead code has not been confirmed with a design/implementation owner.

## Reason for Change
Per `RAG-003`/`RAG-004`'s own stated Impact: potential accumulation of dead code or confusion regarding intended data structures/configuration mechanism if left unresolved indefinitely.

## Implementation Intent
Obtain an explicit owner decision for `RegisteredDocument` and each of the six confirmed-unused `models_config.py` dataclasses (`PipelineConfig` was re-checked and is also zero-referenced outside its own module, contrary to what an unqualified string search might suggest — see Unresolved Questions). Remove what is confirmed removable; document what is confirmed intentional scaffolding (with a target usage/migration note); do not guess at intent.

## Target Files or Areas
- `scripts/rag/models_data.py`
- `scripts/rag/models_config.py`
- `docs/03_rag_04_01_dto-models_data.md`
- `docs/03_rag_04_04_dto-models_config.md`
- `docs/00_governance_03_issue-and-uncertainty-management.md`

## Required Changes
- Obtain owner confirmation on whether `RegisteredDocument` is a required future component or removable dead code.
- Obtain owner confirmation on whether each of `MqeConfig`, `FusionConfig`, `RerankConfig`, `SearchConfig`, `ChunkSplitterConfig`, `IngesterConfig`, and `PipelineConfig` is required future scaffolding or removable dead code — these may not all have the same answer, confirm per-class rather than as one block.
- For each class confirmed removable: remove the class and update `docs/03_rag_04_01_dto-models_data.md`/`docs/03_rag_04_04_dto-models_config.md` to drop any reference to it.
- For each class confirmed as intentional scaffolding: add a code comment stating its intended future use and update the corresponding doc to say so explicitly (not leave it undocumented and unused indefinitely).
- Update `RAG-003`/`RAG-004` in `docs/00_governance_03_issue-and-uncertainty-management.md` to reflect the resolution (removed if resolved by removal or explicit scaffolding documentation, per that document's removal policy).

## Constraints
This issue must not remove or repurpose any class without an explicit owner decision recorded — per `RAG-003`/`RAG-004`'s own `Recommended Action`, this is not a unilateral cleanup.

## Acceptance Criteria
- Each of the 8 classes (`RegisteredDocument` + 7 in `models_config.py`) has an explicit, recorded decision: removed, or documented as intentional scaffolding with a stated future-use note.
- No class remains in an undocumented, unreferenced, undecided state after this issue closes.
- `RAG-003` and `RAG-004` are removed from the active Known Issues inventory once resolved.

## Testing Expectations
Not required beyond running the standard lint/type-check suite after any removal, to confirm no residual references were missed by the word-boundary search performed for this issue.

## Documentation Impact
Update `docs/03_rag_04_01_dto-models_data.md` and `docs/03_rag_04_04_dto-models_config.md` to either drop removed classes or explicitly document retained ones as intentional scaffolding, and update `RAG-003`/`RAG-004` in the governance inventory accordingly — only after the owner decision is obtained.

## Out of Scope
- Migrating actual TOML-based configuration handling to use these dataclasses, even if a class is confirmed as intended scaffolding for that purpose — that migration, if decided, is a separate, larger issue.
- Unrelated refactoring of `models_data.py`/`models_config.py`.

## Dependencies
N/A: none.

## Unresolved Questions
Whether `SearchConfig` and `PipelineConfig` specifically (out of the 7 `models_config.py` classes) might have a planned but not-yet-wired consumer, given their generic-sounding names risk collision with unrelated classes of similar name elsewhere in the codebase (`WebSearchConfig`, `RagPipelineConfig`) that were initially mistaken for them during this issue's own verification via a loose string search — the word-boundary-confirmed zero-reference count for the actual `models_config.py` classes stands, but an owner may have additional context a code search cannot surface. This is exactly why an owner decision (not further automated search) is this issue's Required Change.

## AI Implementation Instruction
Do not remove any of the 8 classes without an explicit recorded owner decision — per `RAG-003`/`RAG-004`'s own Recommended Action, this is a confirmation-then-action issue, not a unilateral cleanup. If no owner decision channel is available in this session, stop after documenting the re-confirmed zero-reference finding and report `Blocked: owner decision required` rather than guessing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-105211
- **Related target files**: scripts/rag/models_data.py, scripts/rag/models_config.py, docs/03_rag_04_01_dto-models_data.md, docs/03_rag_04_04_dto-models_config.md, docs/00_governance_03_issue-and-uncertainty-management.md
