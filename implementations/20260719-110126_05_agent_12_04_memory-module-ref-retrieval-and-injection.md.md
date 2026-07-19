# Implementation procedure: `docs/05_agent_12_04_memory-module-ref-retrieval-and-injection.md` (fragmentation-limitation note)

Source plan: `plans/20260719-095637_plan.md` ("Enable the persistent memory layer by default and add the
missing chunking step", requirement `requires/done/20260714_15_require.md`), Implementation step 4 /
Design step 6 (second of three target docs).

No existing implementations doc under `implementations/` or `implementations/done/` matches this
specific change. Prior memory-doc edits under `implementations/done/` (e.g. the KNN-failure-mode
correction already reflected in this file's current text, lines 79-83) predate this batch and address
unrelated corrections. None adds a retrieval-fragmentation limitation note. Flagged as checked, not a
genuine overlap.

## Goal

Add a short note to this doc's retrieval section stating the accepted, documented limitation that
multiple chunks from one long source event may surface as independent hits in search results, since
chunk rows carry no parent/grouping metadata.

## Scope

**In scope**
- One short paragraph/note under the `### 7. retriever.py` section (or its "スコアリングの数式"/
  "失敗モード" subsection boundary — see Procedure) stating the limitation.

**Out of scope**
- Any change to the documented `retriever.py`/`rrf.py` method tables, scoring formula, or failure-mode
  text (lines 25-105) — these describe unchanged code (per the plan's explicit "Out of scope: no change
  to `retriever.py`/`rrf.py`") and must not be edited.
- The `12_03` chunking-stage subsection — separate implementation doc.
- The `08_01` config-default-table update — separate implementation doc.
- `### 8. injection.py` and `### 9. ingestion.py` sections (lines 107-149) — untouched; neither module
  changes under this plan.

## Assumptions

1. Confirmed by direct read: this file's `### 7. retriever.py` section spans lines 25-105 and documents
   `FtsRetriever`/`VectorRetriever`/`HybridRetriever`, the RRF merge (`rrf.py`, lines 99-105), and branch
   filtering (lines 85-97) — none of this describes any per-source grouping or chunk-awareness today,
   consistent with the plan's own investigation (`retriever.py:84-186`, `rrf.py:10-29` dedup only by
   `memory_id`) that this is a real, currently-true gap, not a doc/code mismatch to "fix" by changing
   code — it is being **accepted and documented**, not resolved, per the plan's explicit scope.
2. Per `rules/coding.md`'s "Current behavior" classification table: this note is explicitly the
   **"Accepted current specification"** category, since the plan's Risks section states the user has
   confirmed this tradeoff is acceptable. Per the classification rule, this must be written as **plain
   prose in the normal section — no special heading/framing, no "Current behavior"/"現在の動作" label** —
   it is not a flagged bug or doc-vs-code inconsistency.
3. `rrf.py`'s dedup-by-`memory_id` behavior (documented at current lines 101-103: "同じ `memory_id` が
   複数リストに出現した場合...") already explains *within-hybrid-search* dedup across FTS/KNN result
   lists for the *same* `memory_id`. The new note is a **different, additional** point: multiple
   **distinct** `memory_id`s (one per chunk, from the same original long source message) are not
   deduplicated or grouped by *source* today — `rrf_merge`'s dedup key is `memory_id`, and each chunk has
   its own independently-generated `memory_id` (per the paired `extract.py` doc's Assumption 1: every
   `_make_entry_with_importance` call mints a new `uuid.uuid4()`). This distinction should be made
   explicit in the note so it is not confused with the existing dedup-by-`memory_id` text right above it.

## Implementation

### Target file

`docs/05_agent_12_04_memory-module-ref-retrieval-and-injection.md`

### Procedure

1. Add a short paragraph immediately after the existing `rrf.py` bullet list (current lines 99-105,
   ending "根拠: Explicit in code（`rrf.py` `rrf_merge()`）。") and before
   "### 8. `injection.py` — ライフサイクル注入サービス" (current line 107).
2. State, in plain prose (no flagged-gap framing, per Assumption 2):
   - Long source messages that are split into multiple chunks at extraction time (see
     `05_agent_12_03_memory-module-ref-core-and-store.md`'s chunking-stage note and
     `05_agent_12_05_memory-module-ref-extraction-and-facade.md`'s `extract.py` detail) are stored as
     independent `memories` rows, each with its own `memory_id`.
   - `retriever.py`/`rrf.py` treat every row independently; there is no chunk-to-source grouping or
     parent/child linkage in the schema (per the paired `extract.py` doc — no DB schema change in this
     plan).
   - Consequence: a single long source event split into N chunks may surface as up to N independent
     hits in `search()`/`top_semantic()` results, rather than being merged or deduplicated as one logical
     unit. This is distinct from `rrf_merge`'s existing same-`memory_id` dedup described above, which
     does not apply across different chunks' distinct `memory_id`s.
   - This is a known, accepted limitation of the current chunk-mapping strategy (one row per chunk, no
     linkage), not a bug; a future requirement could add `chunk_index`/`parent_id` schema support and
     retrieval-side grouping if it proves problematic in practice.
3. No changes to any existing table, heading, or method description in this file.

### Method

Prose documentation addition only, placed at a section boundary to avoid disturbing existing table
formatting. Matches this file's existing precedent of appending explanatory prose after a bulleted
"根拠: Explicit in code" block (e.g. the branch-awareness note at lines 85-97, and the KNN failure-mode
correction at lines 79-83).

### Details

No structural/schema claims beyond what's already true after the paired `extract.py` change ships (no
schema change occurs in this plan, so this note's factual content — "no parent/child linkage" — is
already true today and remains true after the change; only the *frequency* of the described scenario
increases, since chunking is new).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Docs consistency | `uv run python tools/check_agent_docs_consistency.py` | no new ERROR/WARNING |
| Cross-reference integrity | `rg -n "12_03|12_05" docs/05_agent_12_04_memory-module-ref-retrieval-and-injection.md` | both cross-references present after the edit |
| No unlabeled "Current behavior" framing | `rg -n "Current behavior|現在の動作" docs/05_agent_12_04_memory-module-ref-retrieval-and-injection.md` | new note does not use this framing (per Assumption 2 — it is Accepted current specification, plain prose) |
| Existing tables untouched | `git diff docs/05_agent_12_04_memory-module-ref-retrieval-and-injection.md` | diff shows only an added paragraph; no changes inside the `retriever.py`/`rrf.py` method tables |
| Manual review | Read the new note alongside the shipped `extract.py`/`ingestion.py`/`retriever.py` | prose accurately describes post-chunking retrieval behavior |
