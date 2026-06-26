# Implementation: Add rag.llm and PipelineStageResult migration note to RAG document guide

Steps covered: Plan 20260626-100120 — Step 1

---

## Goal

Add a migration note section to `docs/03_rag_00_document-guide.md` showing the before/after import changes for the removed `rag.llm` module and `PipelineStageResult` type.

---

## Scope

- **In scope**: `docs/03_rag_00_document-guide.md` — migration note section
- **Out of scope**: runtime code changes

---

## Implementation

### Target file
`docs/03_rag_00_document-guide.md`

### Procedure
1. Add "Migration Notes" section (or append):
   ```
   ## Migration Notes

   ### rag.llm re-export (removed 2026-06-26)

   ```python
   # Before:
   from rag.llm import RagLLM, get_embedding          # compat re-export (removed)
   from rag.llm import RagExpansionError               # compat re-export (removed)

   # After:
   from rag.llm_client import RagLLM, get_embedding   # canonical
   from rag.llm_prompts import RagExpansionError       # canonical
   ```

   ### PipelineStageResult (removed 2026-06-26)

   ```python
   # Before:
   from rag.types import PipelineStageResult  # removed

   # After:
   from rag.stage import StageResult          # canonical
   ```
   ```

### Method
Documentation-only change.

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — markdown lint must pass.
- Confirm: `grep -n "Migration Notes" docs/03_rag_00_document-guide.md` shows the section.
