## Goal

Remove the dead `LanguageCode` enum from `scripts/rag/enums.py` (REQ-002).

## Scope

- Delete `LanguageCode` enum (lines 11-15) from `scripts/rag/enums.py`

## Assumptions

- No external caller outside this repository depends on `LanguageCode` — consistent with how `AGENTS.md`/`rules/ai-execution.md` scope dead-code determinations to this repository
- `LanguageCode` is used only by `CrawlTarget.lang` (`models_data.py:28`), which is itself being removed per REQ-001 (separate document)
- `LanguageCode` has zero references beyond its own definition and `CrawlTarget.lang`'s type annotation (confirmed via `rg "LanguageCode" scripts/ tests/`)

## Design decisions

1. Remove `LanguageCode` together with `CrawlTarget` rather than keeping it as an orphaned enum — it serves no purpose without its sole user
2. Do not remove `enums.py`'s other unused enums (`PipelineStageName`, `HitKind`, `SearchBackend`) in this same Plan — they are unrelated to the Issue's `CrawlTarget.lang` concern; tracked as UNK-01 for a separate decision

## Alternatives considered

1. Keeping `LanguageCode` as an orphaned enum — rejected because it serves no purpose without its sole user and increases maintenance burden
2. Moving `LanguageCode` to a shared location for future use — rejected because there is no current need for it; the live DTOs use `str` for `lang` and are internally consistent

## Implementation

### Target file

`scripts/rag/enums.py`

### Procedure

1. Confirm `LanguageCode` has zero references beyond `CrawlTarget.lang`
2. Delete `LanguageCode` (lines 11-15)

### Method

Phase 1: Preparation — confirm evidence line numbers
- Re-confirm `rg "LanguageCode" scripts/ tests/` finds only the enum definition and `CrawlTarget.lang`'s type annotation before deleting (REQ-002; `scripts/rag/enums.py`)

Phase 2: Core Logic — delete dead enum
- Delete `LanguageCode` (lines 11-15) from `enums.py` (REQ-002; `scripts/rag/enums.py`)

### Details

**Phase 1:** Verify via grep that:
- `rg "LanguageCode" scripts/ tests/` returns only three matches: `enums.py:11` (definition), `models_data.py:12` (import), `models_data.py:28` (type annotation)
- Both `models_data.py` references will be removed per REQ-001 (separate document)

**Phase 2:** Make the following deletion:
1. Delete lines 11-15 (`class LanguageCode(StrEnum):\n    """Supported language codes for document processing."""\n\n    EN = "en"\n    JA = "ja"`) including its docstring

## Compatibility considerations

Removing a public enum that has zero callers means no behavioral change for any actual caller. However, if any downstream consumer of `RagPipeline` as a library depends on `LanguageCode`, removal would be a breaking change. This risk is mitigated by the repository-wide search confirming no callers exist.

## Security considerations

No security impact — removing dead code reduces attack surface slightly by eliminating unused code paths.

## Rollback considerations

Revert the deletion commit to restore the enum. The enum's values remain unchanged since no code depends on them.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/enums.py | Regression — full existing RAG test suite | `pytest tests/rag/` | All existing tests pass unchanged |
| scripts/rag/enums.py | Lint — confirm no unused imports | `ruff check scripts/rag/enums.py` | No unused-import findings |

## Completion criteria

- [ ] `scripts/rag/enums.py` no longer defines `LanguageCode` (REQ-002)
- [ ] All existing tests pass after changes

## Out of scope

- Any change to `ChunkDocument`/`CrawlDocument`/`ChunkRecord`'s `lang: str` fields (these are actively used and internally consistent)
- Removing other unused enums in `enums.py` (`PipelineStageName`, `HitKind`, `SearchBackend`) — tracked separately as UNK-01
- Documentation corrections (separate document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Confirm LanguageCode has zero references | Pending | — | — | |
| 2 | Phase 2: Delete LanguageCode enum | Pending | — | — | |
| 3 | Verification: run tests and lint | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260913-183007_type_inconsistency_crawltarget_lang.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-203930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-232503
- **Related target files**: scripts/rag/enums.py
