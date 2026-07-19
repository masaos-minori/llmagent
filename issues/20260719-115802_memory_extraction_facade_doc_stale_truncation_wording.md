# `docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md` still describes chunking as truncation

**RESOLVED (2026-07-19).** `docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md:30`'s
`extract_memories()` row now describes `max_content_chars` as a per-chunk split
limit applied to both assistant and user extraction (cross-referencing
`05_agent_12_03_memory-module-ref-core-and-store.md`'s "チャンク分割ステージ"
section), matching corrected behavior — no code change required, doc-only fix.

Discovered while implementing `plans/done/20260719-095637_plan.md` (memory-layer
chunking), specifically during the `implementations/done/20260719-110049_...md`
cycle (adding the chunking-stage section to `docs/05_agent_12_03_...md`).

## Problem

`docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md:30` reads:

```
max_content_chars は assistant メッセージの切り詰め長
```

("`max_content_chars` is the truncation length for assistant messages")

This is now inaccurate on two counts, following the chunking implementation
in `scripts/agent/memory/extract.py`:

1. `max_content_chars` is a **per-chunk split limit**, not a truncation
   length — content over the limit is split into multiple stored chunks, not
   cut and discarded (see `docs/05_agent_12_03_memory-module-ref-core-and-store.md`'s
   new "チャンク分割ステージ" section for the corrected description).
2. It also applies to `_try_extract_from_user` now (a genuinely new
   size-bounding behavior for that path — previously it had none), not just
   assistant messages as this line claims.

## Why this wasn't fixed inline

This doc is not one of `requires/done/20260714_15_require.md` /
`plans/done/20260719-095637_plan.md`'s three named target docs
(`docs/05_agent_12_03_...`, `docs/05_agent_12_04_...`,
`docs/05_agent_08_01_...`), so the implementation cycle that found it
deliberately did not edit it, per this repo's scope discipline (only touch
files named in the active implementation doc's own scope).

## Recommended action

Update `docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md:30` to
match the corrected description now in `docs/05_agent_12_03_...`'s "チャンク
分割ステージ" section: `max_content_chars` is the per-chunk size limit applied
to both assistant and user message extraction via `_split_content()`, with no
content discarded.
