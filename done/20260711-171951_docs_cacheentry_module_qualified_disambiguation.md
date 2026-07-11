# Implementation: Module-qualify `CacheEntry` references where both cache types are discussed together

Source plan: `plans/20260711-171430_plan.md` (Phase 3).

## Goal

Eliminate ambiguity in documentation passages that mention both distinct `CacheEntry`
dataclasses (`rag/models_data.py`'s semantic-cache entry and `shared/tool_cache.py`'s
tool-result-cache entry) by the same bare name, by qualifying each occurrence with its module
path wherever both are discussed in the same passage.

## Scope

**In-Scope:**
- Any documentation file/passage that mentions both `CacheEntry` types together in a way that
  could be ambiguous to a reader — identify these at implementation time via a targeted search
  (see Procedure), then module-qualify each occurrence in that passage as
  `rag.models_data.CacheEntry` (semantic-cache entry) or `shared.tool_cache.CacheEntry`
  (tool-result-cache entry).

**Out-of-Scope:**
- Re-documenting `discovery_map` — already covered by `plans/20260711-165831_plan.md`.
- Re-documenting the `ToolResultCache`-vs-RAG-cache distinction as a standalone topic — already
  covered by `plans/20260711-170140_plan.md`'s Design section (module docstring for
  `scripts/shared/tool_cache.py`). This phase only addresses bare-name ambiguity where both
  `CacheEntry` types are named together in one passage; it does not restate the full
  conceptual distinction between the two caching subsystems.
- Renaming either `CacheEntry` class itself, or changing any code — this is a documentation
  wording change only.

## Assumptions

1. Confirmed by `grep -rn "class CacheEntry" scripts/`: two distinct `CacheEntry` dataclasses
   exist — `rag/models_data.py:64` (semantic-cache entry: embedding/history_context/generation
   fields) and `shared/tool_cache.py:18` (tool-result-cache entry: output/is_error/cached_at
   fields).
2. A repo-wide search for `CacheEntry` (see Procedure Step 1) is required at implementation
   time to identify which documentation passage(s), if any, mention both types close enough
   together to be genuinely ambiguous. As of this plan's authoring, no single doc passage was
   confirmed to name both types side by side; the search must be re-run at implementation time
   since sibling plans (`plans/20260711-165831_plan.md`, `plans/20260711-170140_plan.md`) may
   have already landed changes affecting doc content in this area.
3. If, after the search, no passage is found to genuinely co-mention both types ambiguously,
   this phase has no remaining action beyond confirming that absence — do not force an edit
   where no ambiguity exists.

## Implementation

### Target file

Documentation file(s) under `docs/` confirmed at implementation time to mention both
`CacheEntry` types in the same passage (candidates to check first, based on this plan's
research: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`,
`docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md`,
`docs/03_rag_04_01_dto-models_data.md`).

### Procedure

1. Run `grep -rn "CacheEntry" docs/` to enumerate every documentation file mentioning
   `CacheEntry`.
2. Read each match in its surrounding context (a few lines before/after) to determine whether
   the passage discusses only one `CacheEntry` type, or genuinely juxtaposes both types closely
   enough that a reader could conflate them.
3. For each passage found to be genuinely ambiguous (both types named without qualification in
   the same section/table/paragraph), replace each bare `CacheEntry` occurrence with its
   module-qualified form: `rag.models_data.CacheEntry` for the semantic-cache entry,
   `shared.tool_cache.CacheEntry` for the tool-result-cache entry.
4. Do not edit passages that mention only one `CacheEntry` type in isolation — qualifying those
   would add verbosity without resolving any real ambiguity.
5. Cross-check against `plans/20260711-170140_plan.md`'s already-landed changes (it should be
   in `plans/done/` by the time this phase runs) to avoid re-editing lines it already touched
   for the same reason.

### Method

Targeted, passage-scoped text edits (Markdown prose and/or table cells) in one or more
documentation files. No code changes, no schema changes, no new sections.

### Details

Example qualification style (illustrative — apply only where both types are named together):

```
- `rag.models_data.CacheEntry` — semantic-cache entry (embedding, history_context, generation)
- `shared.tool_cache.CacheEntry` — tool-result-cache entry (output, is_error, cached_at)
```

## Validation plan

Filtered to checks relevant to this file, from the plan's Validation plan table:

| Check | Tool | Target |
|---|---|---|
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
| Manual grep | `grep -rn "CacheEntry" docs/` | Every ambiguous co-mention is module-qualified; single-type mentions left as-is |
