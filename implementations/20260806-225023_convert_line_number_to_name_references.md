## Goal
Replace all raw `<file>.py:<line>`-style line-number references across 10 `docs/03_rag_*.md` files with name-based references (function/method/class/key name) following the pattern established in `docs/03_rag_05_5-constraints-reference.md`.

## Scope
- **In-Scope**:
  - `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md`
  - `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md`
  - `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`
  - `docs/03_rag_03_04_query_pipeline-search-stages.md`
  - `docs/03_rag_03_05_query_pipeline-augment-stages.md`
  - `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`
  - `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`
  - `docs/03_rag_02_07_ingestion_pipeline-utils.md`
  - `docs/03_rag_04_04_dto-models_config.md`
  - `docs/03_rag_91_design_notes-part2.md`
- **Out-of-Scope**:
  - Modifying source code (`scripts/rag/...`, `tests/...`, `config/...`)
  - Modifying `docs/03_rag_01_system_overview-part2.md` or `docs/03_rag_05_1-configuration-reference.md` (already fixed)
  - Modifying any other `docs/*.md` files

## Assumptions
- The naming convention from `docs/03_rag_05_5-constraints-reference.md` applies: config keys use `file.toml:key_name` style; functions/classes use `<name>()` or `<ClassName>` notation; imports use module path only.
- All 15 locations listed in the requirement still exist at roughly the cited spots (source may have moved further).
- "根拠分類" annotations must be preserved exactly as they appear.

## Design decisions
- Use the same naming convention as `docs/03_rag_05_5-constraints-reference.md`:
  - Config keys → `file.toml:key_name` style
  - Functions/methods → `<name>()` notation
  - Classes → `<ClassName>` notation
  - Imports → module path only (drop line number)
- Process one file at a time to maintain context hygiene.
- Verify each converted reference by name-based grep in the source file.

## Alternatives considered
- Retaining line numbers with a note about drift — rejected because the entire purpose of this fix is to eliminate fragile line-number references.
- Using hyperlinks to GitHub commit hashes — rejected because commits shift over time and would require constant updating.

## Implementation

### Target files
10 documentation files under `docs/03_rag_*.md` (listed in Scope section).

### Procedure
1. **Phase 1: Preparation**
   - [ ] Read `docs/03_rag_05_5-constraints-reference.md` to confirm naming convention style.
   - [ ] Re-confirm each of the 15 locations still exists at roughly the cited spot.
2. **Phase 2: Conversion (process ONE file at a time)**
   - For each of the 15 locations, apply the appropriate conversion rule:
     - Function/method def → "`<name>()` 関数" / "`<name>()` メソッド"
     - Class def → "`<ClassName>` クラス"
     - Import statement → module path only (drop line number), e.g. "`rag.cache` からの `SemanticCache` のimport"
     - Docstring/comment reference → name the enclosing function/method rather than its line number
     - Config key → `file.toml:key_name` style
   - Preserve all "根拠分類" annotations exactly as they appear.
3. **Phase 3: Verification**
   - [ ] Run `grep -rnE '\.py:[0-9]+' docs/03_rag_*.md` to confirm no numeric references remain.
   - [ ] For each converted reference, grep the named symbol in the actual source file to confirm it still exists.
   - [ ] Spot-check that surrounding prose/claims were not altered beyond the locator change.

### Method
Manual Markdown editing — no code generation or tooling required.

### Details

#### Location-by-location conversions

**Location 1**: `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md:37`
- Original: `scripts/rag/repository.py:232`
- Convert to: "`RagRepository.fetch_full_document()` 関数"
- Source verification: `grep -n "def fetch_full_document" scripts/rag/repository.py`

**Location 2**: `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md:81`
- Original: `scripts/rag/pipeline.py:606-614` (docstring for `invalidate_cache`)
- Convert to: "`RagPipeline.invalidate_cache()` メソッドのdocstring"
- Source verification: `grep -n "def invalidate_cache" scripts/rag/pipeline.py`

**Location 3**: `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md:105`
- Original: `scripts/rag/http_augment.py:25-32` and `scripts/rag/pipeline.py:485-499`
- Convert to: "`HttpAugmentResult.__init__` コンストラクタ" and "`RagPipeline._run_http_augment()` メソッド"
- Source verification: `grep -n "class HttpAugmentResult" scripts/rag/http_augment.py`; `grep -n "def _run_http_augment" scripts/rag/pipeline.py`

**Location 4**: `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md:67`
- Original: `scripts/rag/pipeline.py:485-499`
- Convert to: "`RagPipeline._run_http_augment()` メソッド"
- Source verification: `grep -n "def _run_http_augment" scripts/rag/pipeline.py`

**Location 5**: `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md:69`
- Original: `scripts/rag/http_augment.py:25-32,82-90`
- Convert to: "`HttpAugmentResult.__init__` コンストラクタ" and "`HttpAugment.run()` メソッド内の `_http_result_kind` 代入ブロック"
- Source verification: `grep -n "_http_result_kind" scripts/rag/http_augment.py`

**Location 6**: `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md:71`
- Original: `scripts/rag/pipeline.py:482-483`
- Convert to: "`RagPipeline._run_http_augment()` メソッド内の `self._http_result_kind` 代入行"
- Source verification: `grep -n "self._http_result_kind = result.http_result_kind" scripts/rag/pipeline.py`

**Location 7**: `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md:76`
- Original: `scripts/rag/pipeline.py:544` for `get_diagnostics()`
- Convert to: "`RagPipeline.get_diagnostics()` メソッド"
- Source verification: `grep -n "def get_diagnostics" scripts/rag/pipeline.py`

**Location 8**: `docs/03_rag_03_04_query_pipeline-search-stages.md:59`
- Original: `scripts/rag/stages/search.py:56-65`
- Convert to: "`SearchStage._search_all_queries()` メソッド内の `try/except` ブロック"
- Source verification: `grep -n "def _search_all_queries" scripts/rag/stages/search.py`

**Location 9**: `docs/03_rag_03_04_query_pipeline-search-stages.md:85`
- Original: `pipeline.py:294` for `FusionStage(...)` instantiation passing `use_rrf`
- Convert to: "`RagPipeline.__init__()` 内の `FusionStage` インスタンス化箇所"
- Source verification: `grep -n "FusionStage(" scripts/rag/pipeline.py`

**Location 10**: `docs/03_rag_03_05_query_pipeline-augment-stages.md:46`
- Original: `scripts/rag/stages/augment.py:11` and "pipeline.py 461行目付近"
- Convert to: "`_format_chunks()` 関数" and "`RagPipeline._augment_format_chunks()` 呼び出し箇所"
- Source verification: `grep -n "def _format_chunks" scripts/rag/stages/augment.py`; `grep -n "_augment_format_chunks" scripts/rag/pipeline.py`

**Location 11**: `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md:34`
- Original: `rag/cache.py:31` and `rag/pipeline.py:29`
- Convert to: "`SemanticCache` クラス定義" and "`rag.cache` からの `SemanticCache` のimport"
- Source verification: `grep -n "class SemanticCache" scripts/rag/cache.py`; `grep -n "from rag.cache import SemanticCache" scripts/rag/pipeline.py`

**Location 12**: `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md:88`
- Original: `scripts/rag/llm_client.py:49`
- Convert to: "`llm_client.py` モジュール内の `logger` グローバル変数定義"
- Source verification: `grep -n 'logger = logging.getLogger(__name__)' scripts/rag/llm_client.py`

**Location 13**: `docs/03_rag_03_02_07_ingestion_pipeline-utils.md:69`
- Original: `crawler_utils.py:31-40` for the `file://`-scheme note
- Convert to: "`_validate_target_url()` 関数のdocstring内の `file://` スキーム注釈"
- Source verification: `grep -n "def _validate_target_url" scripts/rag/ingestion/crawler_utils.py`

**Location 14**: `docs/03_rag_04_04_dto-models_config.md:93`
- Original: `scripts/rag/models_result.py:102` for `SearchDiagnostics.result_source`
- Convert to: "`SearchDiagnostics.result_source` プロパティ"
- Source verification: `grep -n "result_source" scripts/rag/models_result.py`

**Location 15**: `docs/03_rag_91_design_notes-part2.md:130`
- Original: `tests/test_rag_index_integrity.py:298` for `test_consistency_check_detects_fts_gap`
- Convert to: "`test_consistency_check_detects_fts_gap()` テスト関数"
- Source verification: `grep -n "def test_consistency_check_detects_fts_gap" tests/test_rag_index_integrity.py`

## Compatibility considerations
N/A — documentation-only change. No API or behavioral compatibility impact.

## Security considerations
N/A — no security-relevant changes.

## Rollback considerations
Simple revert: restore original line-number references from git history. No database migration or config rollback needed.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All Target Docs | Manual Review | `grep -rnE '\.py:[0-9]+' docs/03_rag_*.md` | No output (no numeric references found) |
| Each Converted Reference | Name-based existence check | `grep -n "<symbol>" scripts/rag/<file>.py` | Symbol found in source |

## Out of scope
- Source code modifications in `scripts/rag/...`, `tests/...`, `config/...`
- Changes to `docs/03_rag_01_system_overview-part2.md` or `docs/03_rag_05_1-configuration-reference.md`
- Changes to any other `docs/*.md` files

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260806-223205_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-225023
- Related target files: docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md, docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md, docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md, docs/03_rag_03_04_query_pipeline-search-stages.md, docs/03_rag_03_05_query_pipeline-augment-stages.md, docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md, docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md, docs/03_rag_02_07_ingestion_pipeline-utils.md, docs/03_rag_04_04_dto-models_config.md, docs/03_rag_91_design_notes-part2.md
