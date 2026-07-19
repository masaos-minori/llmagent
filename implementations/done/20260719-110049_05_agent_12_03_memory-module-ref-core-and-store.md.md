# Implementation procedure: `docs/05_agent_12_03_memory-module-ref-core-and-store.md` (chunking-stage note)

Source plan: `plans/20260719-095637_plan.md` ("Enable the persistent memory layer by default and add the
missing chunking step", requirement `requires/done/20260714_15_require.md`), Implementation step 4 /
Design step 6 (first of three target docs).

No existing implementations doc under `implementations/` or `implementations/done/` matches this
specific change. `implementations/done/20260626-182012_memory_config_docs.md` and other memory-doc
edits under `implementations/done/` predate this batch and cover unrelated earlier doc corrections
(embed_dim default, KNN failure-mode wording, etc. — visible in the current file's own text as
already-applied corrections, e.g. lines 111-117). None adds a chunking-stage subsection. Flagged as
checked, not a genuine overlap.

## Goal

Add a short subsection to this doc describing the new chunking stage (Design step 6's first bullet):
what triggers it, that `memory_max_content_chars` is now a per-chunk limit rather than a total-content
cap, and that no data is discarded.

## Scope

**In scope**
- One new subsection (or a short paragraph appended to an existing subsection — see Assumption 1 for
  the placement caveat) stating the chunking behavior and the reinterpreted meaning of
  `memory_max_content_chars`.

**Out of scope**
- The retrieval-fragmentation limitation note — that belongs in
  `docs/05_agent_12_04_memory-module-ref-retrieval-and-injection.md` (separate implementation doc).
- The `08_01` config-default-table update — separate implementation doc.
- Any other section of this file (barrel-export list, `types.py`/`enums.py`/`exceptions.py`/`models.py`/
  `store.py` tables) — untouched.

## Assumptions

1. **Placement caveat, worth flagging**: this file (`12_03`) documents `__init__.py`, `types.py`,
   `enums.py`, `exceptions.py`, `models.py`, and `store.py` (confirmed by direct read — section headers
   at lines 24, 43, 54, 66, 80, 89 and the file's own `## Keywords` list at lines 130-135). It does
   **not** document `extract.py` in detail today — that lives in a **different** file,
   `docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md` (confirmed by direct read: section
   10, `extract.py`, at `12_05` line 26-39, including the exact line "`max_content_chars` は assistant
   メッセージの切り詰め長" — "truncation length for assistant messages" — at `12_05` line 30, which will
   become **stale/inaccurate** once the chunking stage ships, since `max_content_chars` will no longer
   be a truncation length but a per-chunk limit, and will also apply to user messages per the paired
   `extract.py` doc). `12_03` only mentions extraction in passing, in its barrel-export list
   ("**抽出:** `ExtractionPolicy`、`extract_memories`", line 37). **The plan names `12_03` (not `12_05`)
   as the doc to receive the new chunking subsection** — followed here as instructed, but this is a
   genuine gap worth surfacing: `12_05` is the doc that actually needs updating for full accuracy (its
   `max_content_chars` description is the one that goes stale), and it is not in the plan's three named
   target docs or Implementation steps. Not creating a `12_05` doc here since it is out of this plan's
   explicit scope, but this finding should be reported up (and may warrant a follow-up plan/requirement).
2. Given the placement caveat, the most defensible way to satisfy Design step 6's literal instruction
   ("`12_03` gets a new subsection describing the chunking stage") without duplicating `12_05`'s
   eventual detailed content is to add a **brief, cross-referencing** subsection here — enough to
   satisfy "what triggers it / per-chunk limit / no data discarded" — with an explicit pointer to `12_05`
   for the full `extract.py` method-level detail. This keeps `12_03` accurate without pre-empting
   `12_05`'s (out-of-scope, not-yet-planned) update.
3. Per `rules/coding.md`'s "Current behavior" classification table: this addition is **"Accepted current
   specification"** (once `extract.py` ships) — plain prose, no "Current behavior"/"現在の動作"
   flagged-gap framing, since it describes intentional, correct behavior rather than a bug or doc/code
   mismatch.

## Implementation

### Target file

`docs/05_agent_12_03_memory-module-ref-core-and-store.md`

### Procedure

1. Add a new subsection after "### 6. `store.py` — 読み取り専用の CRUD レイヤー" (current lines 89-117)
   and before "## Related Documents" (current line 119), e.g. titled
   "### チャンク分割ステージ（抽出時のサイズ上限）" or similar (exact Japanese heading wording is an
   editorial choice; keep it short and consistent with this file's existing `###` heading style).
2. State, in plain prose (no flagged-gap framing, per Assumption 3):
   - The chunking stage triggers when extracted content (from either assistant or user messages) exceeds
     `memory_max_content_chars` (`config_dataclasses.py:220`, default `500`).
   - `memory_max_content_chars` is now a **per-chunk** limit, not a total-content cap: over-long content
     is split into multiple chunks, each stored as an independent `MemoryEntry`/`memories` row, rather
     than being truncated and the remainder discarded.
   - No content is discarded — the full source message is preserved across the resulting chunk rows.
   - Cross-reference: full `extract.py` method-level detail (the `_split_content` helper and its
     paragraph-boundary/hard-cut splitting strategy) is documented in
     `05_agent_12_05_memory-module-ref-extraction-and-facade.md`.
3. Add a one-line pointer to the retrieval-fragmentation limitation, cross-referencing
   `05_agent_12_04_memory-module-ref-retrieval-and-injection.md` (that file carries the full limitation
   note per the paired implementation doc), so a reader of `12_03` is not left unaware that multiple
   chunks from one source may surface as independent search hits.
4. No changes to the `## Related Documents` or `## Keywords` lists are required — both already list
   `12_04` and `12_05` (confirmed at current lines 119-126 and via the `related:` front-matter at lines
   10-16).

### Method

Prose documentation addition only. No tables, no code blocks required (this doc's existing style mixes
prose and tables; a short prose subsection matches the precedent set by e.g. the `embed_dim` note at
lines 111-117, which is also prose-only).

### Details

No structural/schema claims are made beyond what's already true after the paired `extract.py` and
`config_dataclasses.py`/`config/agent.toml` changes ship — this doc update should be sequenced **after**
those land (or at minimum, reviewed against the final `extract.py` behavior) so the prose matches
shipped behavior exactly, per `rules/coding.md`'s guidance to avoid "Documentation fix required" or
"Implementation fix required" churn from a premature/inaccurate doc edit.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Docs consistency | `uv run python tools/check_agent_docs_consistency.py` | no new ERROR/WARNING |
| Cross-reference integrity | `rg -n "12_04|12_05" docs/05_agent_12_03_memory-module-ref-core-and-store.md` | both cross-references present after the edit |
| No stale truncation wording introduced | `rg -n "切り詰め" docs/05_agent_12_03_memory-module-ref-core-and-store.md` | 0 matches (this doc should describe chunking, not reintroduce truncation language) |
| Manual review | Read the new subsection alongside the shipped `scripts/agent/memory/extract.py` | prose matches actual `_split_content`/`_try_extract_from_assistant`/`_try_extract_from_user` behavior exactly |
