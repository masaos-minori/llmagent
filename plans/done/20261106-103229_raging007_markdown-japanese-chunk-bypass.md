# Route Markdown documents through language-aware chunking for text regions

## Goal
- Make Markdown heading chunking language-aware: heading-section extraction stays, but
  intra-section segmentation of oversized sections uses the language-appropriate chunker
  (`_chunk_japanese` for `lang == "ja"`), and Japanese Markdown chunks carry the same
  non-empty `normalized_content` pairs as the Japanese text path.

## Priority
Medium

## Scope
- **In-Scope**: language dispatch inside `_chunk_markdown_by_heading` / `_build_text_triples`;
  normalized pairs for Japanese Markdown chunks; characterization tests for English Markdown
  before the change; new Japanese Markdown tests; docs behavior update.
- **Out-of-Scope**: Markdown structure-aware splitting beyond headings (tables, code fences);
  language detection (chunkers keep using the payload `lang` field); changing
  `chunking_strategy = "heading"` labeling; English chunker behavior.
- **Dependencies**: implement after `plans/20261106-093438_raging001_japanese-chunk-merge-crash.md`
  (the Japanese path must be crash-free before Markdown traffic is routed into it; issue
  Dependencies note). Co-target coordination with
  `plans/20261106-101257_raging004_force-rechunk-stale-chunks.md` (same test file; see Design).

## Background
`_build_text_triples` (`chunk_splitter.py:218-229`; the issue names it `_split_text`) checks
`_is_markdown_source` (`:224-225`) before the `lang == "ja"` branch (`:226-229`), so any
`.md`/`.markdown`/`.mdx` URL — or heuristic Markdown match when `md_index_enable=true` —
bypasses `_chunk_japanese` entirely. `_chunk_markdown_by_heading` (`:160-177`) splits at
heading boundaries, drops sections below `min_chunk` (`:171-173`), and sends oversized
sections (> `md_snippet_max_chars`) to `_chunk_english` (`:174-176`). Markdown triples are
emitted as `("text", c, "")` — empty `normalized_content` (`:225`). Storage is safe (FTS5
triggers COALESCE NULL normalized_content to raw content, `scripts/db/schema_sql.py:78-90`),
but Japanese query recall degrades: query tokens are Sudachi `normalized_form` values
(`scripts/rag/repository.py:76-90`) matched against normalized-content index text, so raw-text
Japanese chunks match only surface forms. Markdown sources additionally carry
`chunking_strategy="heading"` (`:121`) — part of the ingester's 9-field group signature. All
verified at HEAD `bdb9bed66` in Step 2 of this cycle.

## Problem
A Japanese document whose URL ends in `.md`/`.markdown`/`.mdx` never reaches the Japanese
chunker: no Sudachi segmentation, no `normalized_content`, and English sentence heuristics
applied to Japanese text — inconsistent indexing quality in a bilingual corpus determined
solely by URL suffix.

## Reason for Change
The same content yields different chunk boundaries and normalization behavior depending only
on the URL suffix, weakening Japanese FTS recall (query tokens are normalized forms;
`repository.py:76-90`).

## Implementation Intent
Keep `_chunk_markdown_by_heading` responsible for heading-section extraction; dispatch
intra-section segmentation per section to `_chunk_japanese` (returns `(orig, norm)` pairs)
when `lang == "ja"`, else `_chunk_english`, and emit `(orig, norm)` triples for Japanese
sections instead of `(content, "")`. Language selection becomes primary *within* the Markdown
path; heading-boundary splitting itself is unchanged.

## Requirements
- `REQ-001`: `_chunk_markdown_by_heading` gains a language-aware intra-section path: sections
  longer than `md_snippet_max_chars` are segmented by `_chunk_japanese(section)` when
  `data.lang == "ja"` and by `_chunk_english(section)` otherwise; heading-boundary splitting,
  the `md_snippet_max_chars` threshold, and the drop of whole sections below `min_chunk` are
  unchanged (issue Constraints). `lang` reaches the method via a parameter or stored field —
  dispatch must not re-parse the payload.
- `REQ-002`: For `lang == "ja"` Markdown sources, emitted text triples are
  `("text", orig, norm)` with the same pair semantics as the Japanese text path
  (`_chunk_japanese` returns `(orig, norm)`; `normalized_content` non-empty wherever the ja
  path produces it, including the documented empty-normalization-kept case); for non-ja
  Markdown sources the emitted triples stay `("text", c, "")`. `chunking_strategy` remains
  `"heading"` for the whole source regardless of language (group-signature stability).
- `REQ-003`: Characterize current English Markdown behavior first: tests pin today's English
  `.md` heading chunk output (section boundaries, oversized-section `_chunk_english` fallback,
  min_chunk drop, empty `normalized_content`) and stay green before and after the change.
- `REQ-004`: New tests: Japanese `.md` URL with an oversized section produces chunks following
  Japanese chunking semantics (ja sentence segmentation, overlap/min/max rules) with non-empty
  `normalized_content` matching the Sudachi normalized-form space used by the ja text path;
  Japanese Markdown sections that fit `md_snippet_max_chars` keep heading-section behavior
  but must also carry normalized pairs (design decision D2 below); English Markdown output
  byte-identical to characterization baselines.
- `REQ-005`: Update `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`: the "Japanese
  content" paragraph (line 57) — currently stating the bypass as behavior — becomes
  "Japanese Markdown sections follow Japanese chunking semantics with `normalized_content`";
  the oversized-section fallback sentence (line 52) names the language-appropriate chunker.

## Implementation Target Files
**Freeze status**: Frozen (Step 8b validation passed 20261106-103229 — every row `Verified`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Language-aware intra-section dispatch in `_chunk_markdown_by_heading`; ja-aware triple emission in `_build_text_triples` (`("text", c, "")` only for non-ja) | REQ-001, REQ-002; AC-1, AC-2, AC-3 | Markdown-before-lang check at `:224-229`; fallback at `:174-176`; min_chunk drop `:171-173`; empty normalized `:225`; strategy label `:121` (checked in Step 2) | `tests/rag/ingestion/test_chunk_splitter.py` | Verified |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Add English Markdown characterization baselines before the change; add Japanese Markdown chunking/normalization tests | REQ-003, REQ-004; AC-1, AC-2, AC-3, AC-5 | `TestIsMarkdownSource` `:42-70`; en-only Markdown payload `_CRAWL_WITH_MD_HEADINGS` `:441-452` (used `:533`); ja tests `:636-663` use non-`.md` URL — no ja-md coverage (checked in Step 2) | itself | Verified |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Replace the "Japanese content bypass" paragraph and fallback wording with the language-aware behavior | REQ-005; AC-4 | Line 57 documents the bypass as behavior; line 52 describes the sentence-split fallback (checked in Step 3) | N/A: documentation file, validated by review | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/chunk_japanese.py` | `_chunk_japanese` contract: `(orig, norm)` pairs, NFKC, Sudachi (`:39-44`); the ja crash fix lands here via the 001 Plan first | REQ-001, REQ-002 |
| `scripts/rag/ingestion/chunk_english.py` | `_chunk_english` contract (`:26-30`) — must stay byte-identical for en Markdown | REQ-003 |
| `scripts/rag/ingestion/chunk_utils.py` | `merge_text_items` shared buffer helper reused by the chunkers | REQ-001 rationale |
| `scripts/db/schema_sql.py` | FTS5 `COALESCE(normalized_content, content)` triggers (`:78-90`) — why empty normalization was survivable and what the fix improves | REQ-002 rationale |
| `scripts/rag/repository.py` | Query-side Sudachi normalized-form tokens (`:76-90`) — the recall motivation | REQ-002 rationale |
| `scripts/rag/ingestion/ingester.py` | 9-field group signature includes `chunk_type` and `chunking_strategy`; the fix keeps both stable | REQ-002 constraint |
| `plans/20261106-093438_raging001_japanese-chunk-merge-crash.md` | Must be implemented first (ja path crash); co-targets `chunk_japanese.py` semantics | Dependencies |
| `plans/20261106-101257_raging004_force-rechunk-stale-chunks.md` | Co-targets `tests/rag/ingestion/test_chunk_splitter.py`; ordering in Design | REQ-003/004 sequencing |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-004): A Japanese `.md` input with an oversized section produces chunks via
  Japanese segmentation (verified by test) and the section is not routed through
  `_chunk_english` (covered by a test asserting normalized pairs).
- AC-2 (REQ-002, REQ-004): Japanese Markdown chunks carry non-empty `normalized_content`
  wherever the ja text path would; `chunking_strategy` stays `"heading"` (covered by tests).
- AC-3 (REQ-003, REQ-004): English Markdown chunking output is unchanged (characterization
  tests green before and after).
- AC-4 (REQ-005): The chunksplitter doc describes language-aware Markdown chunking; the old
  bypass paragraph no longer exists.
- AC-5 (REQ-001..005): `uv run pytest tests/rag/ingestion` passes and changed lines reach the
  `rules/toolchain.md` diff-cover threshold (≥ 90%).

## Tests
- Characterization (pre-change, REQ-003): English `.md` payload — heading sections ≤
  `md_snippet_max_chars` kept whole; oversized section split by `_chunk_english`; sub-`min_chunk`
  sections dropped; all `normalized_content` empty; snapshot the exact chunk contents.
- REQ-004 ja oversized: Japanese `.md` payload with a section > `md_snippet_max_chars` → chunk
  contents follow ja sentence-boundary semantics; every emitted chunk has non-empty
  `normalized_content` equal to the Sudachi normalized-form string the ja text path produces
  for the same text.
- REQ-004 ja in-section: Japanese `.md` payload with sections ≤ `md_snippet_max_chars` →
  sections kept whole but `normalized_content` populated (pins design decision D2).
- REQ-004 strategy pin: `chunking_strategy == "heading"` for both en and ja `.md` payloads.
- REQ-004 en regression: characterization baselines re-checked after the change, byte-equal.
- Characterization: `TestIsMarkdownSource` and all existing tests unchanged and green.

## Documentation Impact
REQ-005: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` — the "Japanese content"
paragraph (line 57) and the oversized-section fallback sentence (line 52) are rewritten to the
language-aware behavior. No other doc references the bypass (Step 3 scan).

## Assumptions
- Sudachi is available in the test environment for ja Markdown payloads (existing ja tests at
  `test_chunk_splitter.py:636-663` already exercise `_chunk_japanese` end-to-end).
- The crawl payload `lang` is trustworthy for Markdown sources (language detection out of
  scope per issue); a mislabeled `lang` degrades exactly as today's English path does.
- `md_index_enable` heuristic-Markdown sources get the same language dispatch as `.md`-suffix
  sources (single code path — verified `_is_markdown_source` returns one boolean).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether keeping in-section (≤ `md_snippet_max_chars`) ja sections whole but normalized (D2) can exceed downstream expectations — e.g. a single section longer than `max_chunk` that today is kept whole without normalization and after the fix is normalized as one chunk | No production ja Markdown corpus metrics | D2 chosen conservatively (no boundary change for in-section content, normalization added); if Phase-1 tests show a normalized string pathologically exceeding expectations, revisit with the operator | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Medium | 2 | High (single maintainer) | not applicable (rsynced) |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Low | 2 | High (single maintainer) | not applicable (rsynced) |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Low | 7 | High (single maintainer) | not applicable (rsynced) |

## Design
- Path B classification: behavior change to a shared chunking path with intentional output
  changes (normalized pairs) plus characterization-first sequencing required by the issue's
  Constraints.
- Dispatch placement — inside `_chunk_markdown_by_heading`, not in `_build_text_triples`:
  heading extraction stays intact (issue Constraint), and the language decision becomes a
  per-section delegation. Signature change to
  `_chunk_markdown_by_heading(self, text: str, lang: str) -> list[tuple[str, str | None]]`
  returning `(content, normalized)` tuples (normalized `""` for non-ja, per-pair normalized
  for ja); `_build_text_triples` then maps them to `("text", c, n)` without re-checking lang
  for the normalization column. Rejected: branching in `_build_text_triples` into two markdown
  paths (duplicates heading logic, risks drift between en/ja heading behavior).
- D2 (in-section ja sections): keep them whole but attach `normalized_content` computed with
  the same Sudachi path used by `_chunk_japanese`'s merge step (via the existing
  normalization helpers in `chunk_japanese.py` / `chunk_utils.py`) — the issue's AC requires
  "carry non-empty `normalized_content` where the Japanese text path would", and the ja text
  path would normalize these sentences. Section boundaries stay byte-identical to today.
- Oversized-section ja path: call `_chunk_japanese(section)` directly — its `(orig, norm)`
  pairs already apply NFKC, sentence splitting, min/max/overlap via the shared merge helpers,
  satisfying "reuse the shared buffer helpers so overlap and min/max rules apply uniformly".
- Stability guarantees for downstream: `chunk_type` stays `"text"`; `chunking_strategy` stays
  `"heading"` (`:121` untouched); payload key set unchanged — so `read_chunk_json`,
  `ChunkGroupingStrategy`, and `ingest_url_group` validation are unaffected. Empty-normalized
  ja pairs: the 001-cycle sibling fix (`df1ff8ed4`) already keeps sentences with empty
  normalization; the plan reuses that semantics rather than inventing a rule.
- Cross-plan coordination: 001 Plan (ja crash) must be implemented first — routing Markdown
  into `_chunk_japanese` on a crashing path would escalate issue 001 from rare payloads to
  all ja Markdown documents. `tests/rag/ingestion/test_chunk_splitter.py` is co-targeted by
  the 004 Plan (force-prune test class) and this plan (Markdown characterization + ja-md
  tests); non-overlapping regions — implement 001 → 004 → 007 to serialize same-file edits.
  Dependency paths: `plans/20261106-093438_raging001_japanese-chunk-merge-crash.md`,
  `plans/20261106-101257_raging004_force-rechunk-stale-chunks.md`.
- `scan_change_consumers.py` not run: no persisted schema, public API, or shared-constant
  change; the chunk payload key set and `chunking_strategy` values are unchanged (verified
  against `pipeline_utils.py` required keys and the ingester signature). Historical analysis
  (Step 3): churn (30d) 2/2/7; single maintainer throughout. Operational check: inherited
  from this batch's `fuser /opt/llm/db/rag.sqlite` (no holders). Persisted schema check: N/A
  — no DDL; `normalized_content` column and FTS5 COALESCE triggers already accept both shapes.
- Validation quality baseline (Step 5): `radon cc` on `chunk_splitter.py` — no C-or-worse
  grade (measured in the 004 cycle: `radon-CD-exit:1`); `vulture`/`bandit` clean on the same
  file in that cycle; re-run at implementation. `pip-audit` N/A: no dependency change.
  Diff-cover current number not measured; ≥ 90% on changed lines required at implementation
  per `rules/toolchain.md`.

## Implementation steps
1. **Phase 1: Characterization baselines (behavior lock, no production change)**
   - [ ] Add English Markdown characterization tests (exact chunk contents, fallback split,
     min_chunk drop, empty normalized, strategy label) to
     `tests/rag/ingestion/test_chunk_splitter.py` — must pass against current code (REQ-003)
2. **Phase 2: Failing Japanese Markdown tests (RED)**
   - [ ] Add ja `.md` oversized-section, in-section normalization, and strategy-pin tests
     (REQ-004; must fail against current code before Phase 3)
3. **Phase 3: Language-aware Markdown chunking (GREEN)**
   - [ ] Change `_chunk_markdown_by_heading` to language-aware per-section dispatch returning
     `(content, normalized)` pairs; update `_build_text_triples` triple mapping
     (`scripts/rag/ingestion/chunk_splitter.py`) (REQ-001, REQ-002)
4. **Phase 4: Documentation & verification & deploy hand-off**
   - [ ] Rewrite the "Japanese content" paragraph and fallback sentence (REQ-005;
     `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`)
   - [ ] Run the `rules/toolchain.md` gate sequence on the touched files (pytest targeted +
     `tests/rag/ingestion`, ruff, mypy, lint-imports, bandit, diff-cover ≥ 90%)
   - [ ] Deploy hand-off: after the change is committed and pushed, `scripts/` sync via
     `skills/deploy/SKILL.md` is the user's decision (approval gate); existing chunks are NOT
     re-split automatically — re-chunking ja Markdown sources with `--force` is an operator
     action (REQ-001)

### Release units
**Unit**: markdown-language-aware-chunking | **Phases**: 1, 2, 3 | **Reason**: Phase 1 locks current behavior, Phase 2 adds tests that fail against it, and only Phase 3 makes the suite green; splitting any phase out leaves the suite red or the behavior unlocked.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Characterization (en Markdown) | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v` | English Markdown chunk output byte-identical before and after the change |
| `scripts/rag/ingestion/chunk_splitter.py` | Unit (ja Markdown) | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v` | ja `.md` oversized sections segmented by `_chunk_japanese`; normalized pairs non-empty; strategy stays `"heading"` |
| whole `tests/rag/ingestion` | Regression | `uv run pytest tests/rag/ingestion` | All ingestion tests green, incl. `TestIsMarkdownSource` unchanged |
| `scripts/` touched files | Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |
| changed lines | Coverage | `uv run coverage run -m pytest tests/` then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Risks
- **Risk**: routing ja Markdown into the ja path before the 001 crash fix escalates a rare
  crash to all ja Markdown documents → **Mitigation**: hard ordering 001 → 007 in Design and
  Dependencies; Phase 3 must not start before the 001 Plan is implemented.
- **Risk**: English Markdown output drifts through shared-code edits → **Mitigation**:
  Phase 1 characterization baselines run before any production change and are re-run byte-equal
  after Phase 3 (AC-3).
- **Risk**: D2 normalization changes payload bytes for existing ja in-section chunks on
  re-chunk (empty → normalized) → **Mitigation**: intended fix semantics; old chunks only
  change when the operator force-re-chunks (deploy hand-off note); group validation treats a
  new run as a new generation (003 Plan drains residue).
- **Risk**: Sudachi unavailable in some test environments breaks the new ja Markdown tests →
  **Mitigation**: existing ja tests already require Sudachi; no new skip logic added (same
  dependency profile as current suite).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | English Markdown characterization tests | In Progress | — | — | REQ-003 |
| 2 | ja Markdown failing tests (RED) | In Progress | — | — | REQ-004 |
| 3 | Language-aware Markdown chunking (GREEN) | In Progress | — | — | REQ-001, REQ-002 |
| 4 | Docs update + gate sequence + deploy hand-off | In Progress | — | — | REQ-005 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A at plan creation; hard dependency on the 001 Plan implementation recorded in Design | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261106-152344_01_scripts_rag_ingestion_chunk_splitter.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261106-152344_02_tests_rag_ingestion_test_chunk_splitter.py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261106-152344_03_docs_21_rag_rag_02_03_ingestion_pipeline-chunksplitter.md.md` | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-073538_raging007_markdown-japanese-chunk-bypass.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-103229
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`,
  `tests/rag/ingestion/test_chunk_splitter.py`,
  `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes bullet 1 + Constraints bullet 1; dispatch points verified at `:224-229`, `:174-176` (checked in Step 2) | `scripts/rag/ingestion/chunk_splitter.py` | Phase 3 | AC-1 | Phase 2 ja oversized test | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes bullet 2 + Problem bullet 4; verified at `:225`, strategy label at `:121`, storage fallback at `schema_sql.py:78-90` (checked in Step 2) | `scripts/rag/ingestion/chunk_splitter.py` | Phase 3 | AC-2 | ja normalized-pair tests + strategy pin | Confirmed by repository evidence |
| REQ-003 | Issue Constraints bullet 2 + Testing Expectations; en-only Markdown coverage verified in Step 2 | `tests/rag/ingestion/test_chunk_splitter.py` | Phase 1 | AC-3 | Characterization baselines | Explicit in issue |
| REQ-004 | Issue Testing Expectations bullets 2-3 | `tests/rag/ingestion/test_chunk_splitter.py` | Phase 2 | AC-1, AC-2, AC-3, AC-5 | New ja Markdown test class | Explicit in issue |
| REQ-005 | Issue Documentation Impact; bypass documented at `rag_02_03...md:57` and fallback at `:52` (checked in Step 3) | `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Phase 4 | AC-4 | Review of updated paragraphs | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261106-152344 -->
