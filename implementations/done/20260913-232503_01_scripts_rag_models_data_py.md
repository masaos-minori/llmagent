## Goal

Remove the dead `CrawlTarget` dataclass and its now-unused `LanguageCode` import from `scripts/rag/models_data.py` (REQ-001).

## Scope

- Delete `CrawlTarget` dataclass (lines 23-28) from `scripts/rag/models_data.py`
- Remove the `from rag.enums import LanguageCode` import (line 12) which becomes unused once `CrawlTarget` is removed

## Assumptions

- No external caller outside this repository depends on `CrawlTarget`/`LanguageCode` — consistent with how `AGENTS.md`/`rules/ai-execution.md` scope dead-code determinations to this repository
- The actual crawler implementation (`scripts/rag/ingestion/crawler.py`) does not rely on `CrawlTarget`'s shape even indirectly (e.g. via structural typing) — confirmed in Phase 1
- `CrawlTarget` has zero references anywhere in the repository beyond its own definition (confirmed via `rg "CrawlTarget" scripts/ tests/`)

## Design decisions

1. Remove `CrawlTarget`/`LanguageCode` together rather than choosing one of the Issue's two type-unification alternatives — both alternatives would have required deciding how the currently-nonexistent `CrawlTarget` construction sites *should* validate `lang`, a speculative design question for code that has no callers; removal sidesteps that speculation entirely
2. Do not remove `enums.py`'s other unused enums (`PipelineStageName`, `HitKind`, `SearchBackend`) in this same Plan — they are unrelated to the Issue's `CrawlTarget.lang` concern; tracked as UNK-01 for a separate decision

## Alternatives considered

1. Extending enum enforcement to the live DTOs (`ChunkDocument`, `CrawlDocument`, `ChunkRecord`) — rejected because it requires non-trivial follow-on validation work for a type mismatch that currently has zero runtime impact
2. Unifying all DTOs on `str` for `lang` — rejected for the same reason; the inconsistency existed only between the dead `CrawlTarget` and the live DTOs, and removing the dead class eliminates it at its source

## Implementation

### Target file

`scripts/rag/models_data.py`

### Procedure

1. Confirm the crawler implementation does not depend on `CrawlTarget`
2. Delete `CrawlTarget` (lines 23-28) and the `LanguageCode` import (line 12)

### Method

Phase 1: Preparation — confirm evidence line numbers
- Read `scripts/rag/ingestion/crawler.py` to confirm it uses its own internal representation, not `CrawlTarget`, and re-confirm zero references remain via `rg "CrawlTarget"` across `scripts/`/`tests/` (REQ-001; `scripts/rag/models_data.py`)

Phase 2: Core Logic — delete dead code
- Delete `CrawlTarget` (lines 23-28) and the `LanguageCode` import (line 12) from `models_data.py` (REQ-001; `scripts/rag/models_data.py`)

### Details

**Phase 1:** Verify via grep/read that:
- `rg "CrawlTarget" scripts/ tests/` returns only the class definition at `models_data.py:24`
- `crawler.py` uses its own internal representation, not `CrawlTarget`

**Phase 2:** Make the following deletions:
1. Delete lines 23-28 (`@dataclass(frozen=True)\nclass CrawlTarget:\n    """URL and language specification for document crawling."""\n\n    url: str\n    lang: LanguageCode`) including its docstring
2. Delete line 12 (`from rag.enums import LanguageCode`) — no remaining references after step 1

## Compatibility considerations

Removing a public class that has zero callers means no behavioral change for any actual caller. However, if any downstream consumer of `RagPipeline` as a library depends on `CrawlTarget`, removal would be a breaking change. This risk is mitigated by the repository-wide search confirming no callers exist.

## Security considerations

No security impact — removing dead code reduces attack surface slightly by eliminating unused code paths.

## Rollback considerations

Revert the deletion commit to restore the class and import. The class's logic remains unchanged since no code depends on it.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/models_data.py | Regression — full existing RAG test suite | `pytest tests/rag/` | All existing tests pass unchanged |
| scripts/rag/models_data.py | Lint — confirm no unused imports | `ruff check scripts/rag/models_data.py` | No unused-import findings |

## Completion criteria

- [ ] `scripts/rag/models_data.py` no longer defines `CrawlTarget` or imports `LanguageCode` (REQ-001)
- [ ] All existing tests pass after changes

## Out of scope

- Any change to `ChunkDocument`/`CrawlDocument`/`ChunkRecord`'s `lang: str` fields (these are actively used and internally consistent)
- Removing other unused enums in `enums.py` (`PipelineStageName`, `HitKind`, `SearchBackend`) — tracked separately as UNK-01
- Documentation corrections (separate document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Confirm crawler does not depend on CrawlTarget | Completed | 20260914-002758 | 20260914-002758 |  |
| 2 | Phase 2: Delete CrawlTarget class | Completed | 20260914-002758 | 20260914-002758 |  |
| 3 | Phase 2: Remove unused LanguageCode import | Completed | 20260914-002758 | 20260914-002758 |  |
| 4 | Verification: run tests and lint | Completed | 20260914-002759 | 20260914-002759 |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260913-183007_type_inconsistency_crawltarget_lang.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-203930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-232503
- **Related target files**: scripts/rag/models_data.py