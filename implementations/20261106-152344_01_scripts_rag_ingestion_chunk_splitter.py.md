## Goal

Make Markdown heading chunking language-aware (`REQ-001`, `REQ-002`): a Markdown
source whose `lang == "ja"` gets Sudachi normalization on both in-section and
oversized sections, while English Markdown output stays byte-identical.

## Scope
**Release unit**: markdown-language-aware-chunking (Plan Phase 3 cites this file)

## Assumptions
- `_chunk_markdown_by_heading` is called only from `_build_text_triples` (verified:
  single call site), so adding a `lang` parameter does not require touching other
  callers.
- `lang` reaches `_build_text_triples` as its `lang` parameter, so dispatch can
  re-parse nothing.
- The ja text path (`_chunk_japanese`) is crash-free (the `raging001` Plan landed
  this fix before this Plan routes Markdown traffic into it).

## Design decisions
- **Dispatch lives inside `_chunk_markdown_by_heading`, not `_build_text_triples`.**
  Heading-boundary splitting stays intact (issue Constraint), and the language
  decision becomes a per-section delegation. Change the signature to
  `_chunk_markdown_by_heading(self, text: str, lang: str) -> list[tuple[str, str | None]]`
  returning `(content, normalized)` tuples (`normalized` is `""` for non-ja,
  per-pair normalized for ja). `_build_text_triples` then maps those tuples to
  `("text", c, n)` without re-checking `lang` for the normalization column.
  Rejected: branching into two Markdown paths in `_build_text_triples` — it would
  duplicate heading logic and risk en/ja heading-behavior drift.
- **In-section ja sections (fit) stay whole but gain a normalized pair.** Attach
  `normalized_content` computed with the same Sudachi path `_chunk_japanese` uses
  (NFKC via `normalize_unicode`, collapse `\n{3,}`, then `_normalize_ja_sentence`),
  so the pair matches the ja text path's normalized-form space. Preserve the
  empty-normalization case: when Sudachi yields no normalized words, store `None`
  (not `""`) so downstream FTS5 `COALESCE` falls back to the original text, exactly
  as the ja text path does.
- **Oversized ja sections route through `_chunk_japanese`.** Call
  `_chunk_japanese(section)` directly — its `(orig, norm)` pairs already apply NFKC,
  sentence splitting, and min/max/overlap via the shared merge helpers, satisfying
  "reuse the shared buffer helpers". Non-ja oversized sections keep
  `_chunk_english(section)` (a `list[str]`); wrap each result as `(c, "")`.
- **Stability:** `chunk_type` stays `"text"`; `chunking_strategy` stays `"heading"`
  (the label in `process_file` is untouched); payload key set unchanged — so
  `read_chunk_json`, `ChunkGroupingStrategy`, and `ingest_url_group` validation are
  unaffected.

## Alternatives considered
- Branching on `lang` in `_build_text_triples` after `_chunk_markdown_by_heading`
  returns plain strings: rejected because it duplicates heading logic and cannot
  carry per-section normalized pairs without re-splitting.
- Normalizing in-section ja sections by calling the full `_chunk_japanese(section)`
  (which re-splits into sentences): rejected by design decision D2 — in-section
  content must stay byte-identical to today's single whole-section chunk; only the
  normalization column is added.

## Implementation
### Target file
- `scripts/rag/ingestion/chunk_splitter.py`

### Procedure
1. Change `_chunk_markdown_by_heading` to accept `lang` and return
   `(content, normalized)` pairs, dispatching per section.
2. Update the single call site in `_build_text_triples` to map the returned pairs
   to `("text", c, n)`.
3. Keep `chunking_strategy`, `chunk_type`, and the payload key set unchanged.

### Method
- In `_chunk_markdown_by_heading`, iterate sections exactly as today. For each
  section that fits (`<= md_snippet_max_chars`, `>= min_chunk`), append
  `(section, normalized)` where `normalized` is computed per the ja path when
  `lang == "ja"` and `""` otherwise. For an oversized section (`> md_snippet_max_chars`),
  extend with `_chunk_japanese(section)` pairs when `lang == "ja"`, else wrap
  `_chunk_english(section)` results as `(c, "")`.
- In `_build_text_triples`, replace the Markdown return expression so it consumes
  the `(content, normalized)` pairs and emits `("text", c, n)`.

### Details
- Preprocessing for the ja in-section normalized value must match `_chunk_japanese`:
  apply `normalize_unicode(section)`, collapse `\n{3,}` to `\n\n` and strip, then
  `_normalize_ja_sentence(...)`. Store the result as `None` when it is empty so the
  empty-normalization-kept semantics of the ja text path are preserved.
- The non-ja branch produces `(section, "")` for fitting sections and `(c, "")`
  for each `_chunk_english(section)` result, so English Markdown triples are
  byte-identical to today.
- Do not touch the `chunking_strategy` label in `process_file` or any code path
  outside `_chunk_markdown_by_heading` / `_build_text_triples`.

## Compatibility considerations
English Markdown output must stay byte-identical (characterization baselines in the
companion test document, `REQ-003`). ja Markdown gains `normalized_content` where it
was previously null — an intended behavior change, not a regression. Group-signature
fields (`chunk_type`, `chunking_strategy`) are unchanged, so existing chunk-group
validation is unaffected.

## Security considerations
N/A: no input handling, network, or credential change. Language dispatch reads the
already-trusted crawl payload `lang` field (language detection stays out of scope).

## Rollback considerations
Revert the commit to `chunk_splitter.py`. The signature change is local to two
private methods with a single call site.

## Validation plan
- Unit (ja Markdown): a ja `.md` oversized section is segmented by ja semantics with
  non-empty `normalized_content`; in-section ja carries a normalized pair; strategy
  stays `"heading"` (companion test document, `REQ-004`).
- Characterization (English Markdown): English `.md` chunk output is byte-identical
  before and after (`tests/rag/ingestion/test_chunk_splitter.py`, `REQ-003`).
- Regression: `uv run pytest tests/rag/ingestion` passes, incl. `TestIsMarkdownSource`.
- Static gates: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
  scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll` — clean, no new findings.

## Completion criteria
- `_chunk_markdown_by_heading` accepts `lang` and returns `(content, normalized)`
  pairs; `_build_text_triples` emits `("text", c, n)` for Markdown.
- ja Markdown `.md` sources produce non-empty `normalized_content`; English Markdown
  output is unchanged.
- `chunking_strategy` stays `"heading"` for both languages.
- All ingestion tests green; static gates clean.

## Out of Scope
- English chunker (`_chunk_english`) behavior — must stay byte-identical.
- Language detection; a mislabeled `lang` degrades exactly as today's English path.
- Changing the `chunking_strategy = "heading"` label or heading-boundary splitting.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement language-aware Markdown dispatch in `_chunk_markdown_by_heading` and remap triples in `_build_text_triples` | Pending | — | — | REQ-001, REQ-002 |
| 2 | Add or update tests per Validation plan | Pending | — | — | REQ-003, REQ-004 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A at plan creation; hard dependency on the `raging001` Plan implementation recorded in the source Plan Design | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261106-073538_raging007_markdown-japanese-chunk-bypass.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-103229_raging007_markdown-japanese-chunk-bypass.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-152344
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`
