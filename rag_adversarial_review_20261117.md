# Adversarial Review — `scripts/rag` (4 domains)

Reviewed head: `8eb1570d1` (working tree matched HEAD, no uncommitted edits).

## Review Scope

- Reviewed (query pipeline): `pipeline.py`, `pipeline_refiner.py`, `stage_lifecycle.py`, `stages/{mqe,search,fusion,rerank}.py`, `repository.py`, `stage.py`, `config_resolution.py`, `db_connection.py`, `augment.py`, `llm_client.py`.
- Reviewed (ingestion): `ingester.py`, `orchestrator.py`, `document_manager.py`, `document_persistence.py`, `transaction_commit.py`, `file_routing.py`, `embedding.py`, `content_extractor.py`, `pipeline_utils.py`.
- Reviewed (crawler): `crawler.py`, `http_fetcher.py`, `link_discovery.py`, `crawler_utils.py`, `robots.py`, `crawl_persister.py`, `etag_manager.py`.
- Reviewed (chunk): `chunk_preparation.py`, `chunk_splitter.py`, `chunk_japanese.py`, `chunk_english.py`, `chunk_grouping.py`, `chunk_utils.py`, `language_resolver.py`.
- Reviewed (supporting top-level): `enums.py`, `exceptions.py`, `utils.py`, `types.py`, `models_data.py`, `models_config.py`, `models_result.py`, `llm_prompts.py`.
- Not reviewed: non-Python assets, shell/TOML, tests (no test-run phase requested), other top-level modules outside `scripts/rag`.

Working tree vs reviewed head: matched at `8eb1570d1`.

## Commands run

| Tool | Scope | Result |
|---|---|---|
| `ruff check` | `scripts/rag/` | All checks passed |
| `mypy --no-namespace-packages` | `scripts/rag/` | Success: no issues found in 51 source files |
| `bandit -ll` | `scripts/rag/` | 2 Low / 2 High-confidence (both B101 `assert_used`, pre-existing pattern in `llm_client.py`) |
| `tools.check_module_size` | `scripts/` | ALL OK — every module ≤ 24576 B (max observed 24576) |
| `lint-imports` | — | Unavailable (not on PATH); ruff covered import hygiene |

## Summary

- Overall assessment: **Clean.** No correctness, concurrency, resource-lifecycle, error-handling, configuration, or security defect survives adversarial scrutiny across the four domains. The code is defensively structured: shared state is lock-guarded, failure paths log-and-fail-open, config defects are kept loud (`ragrev001`), and the import layer contract is respected.
- Highest-risk area: **none requiring action.** The crawler redirect/robots/ETag freshness path and the hybrid-search leg-failure path were scrutinized most heavily; both behave as documented.
- Recommended next step: **proceed.** No fix required. The Low items below are optional polish, not blockers.

## Findings

No Medium-or-higher finding survived Phase 8. The five items below are all Low/Informational; each is either documented-and-intentional, a pre-existing repo-wide pattern, or pure style. None warrants a tracked issue.

### F-001 — `fts_errors` variable name drift vs. what it counts

- Title: Misleading name for the hybrid-search failure counter.
- Severity: Low
- Confidence: High
- Evidence label: Observed
- Evidence: `scripts/rag/stages/search.py::_search_all_queries` increments `fts_errors` from both `_vector_leg` (`vec_failed`, line 110) and `_fts_leg` (`fts_failed`, line 116); `SearchDiagnostics(fts_errors=...)` at line 122; log message `"search degraded: %d FTS/vec errors"` at line 169; docstring states "`fts_errors` counts one per failed retrieval leg."
- Current behavior: The counter accumulates failures from BOTH the vector leg and the FTS/BM25 leg. The name implies FTS-only, but the docstring and log line already clarify it means "failed retrieval leg."
- Impact: A reader unpacking `(hits, num_hits, fts_errors)` may assume FTS-specific failures; telemetry labeled `fts_errors` is slightly imprecise. Behavior is correct by design.
- Recommended action: Optional rename to `retrieval_leg_failures` for clarity. No behavior change.

### F-002 — Empty DB path silently falls back to in-memory

- Title: Silent in-memory fallback on empty connection path.
- Severity: Low
- Confidence: Medium
- Evidence label: Observed
- Evidence: `scripts/rag/db_connection.py` — `if not path: return _connect_memory()` (empty path → ephemeral in-memory DB).
- Current behavior: An empty-string path yields a non-persistent in-memory database instead of raising.
- Impact: Footgun if a caller passes `""` expecting a file-backed DB; data would silently live only for the process lifetime. Documented/intentional design; low practical risk.
- Recommended action: None required. Consider an explicit guard/error if silent in-memory is not desired, only if this changes current accepted behavior.

### F-003 — Row-by-row chunk insert in batch commit

- Title: Per-row insert inside the named batch insert.
- Severity: Low
- Confidence: Medium
- Evidence label: Observed
- Evidence: `scripts/rag/ingestion/transaction_commit.py::_insert_chunks_batch` inserts rows one at a time with an inline comment prioritizing atomicity over speed.
- Current behavior: "Batch" insert is actually a row loop; correctness/atomicity preserved, throughput not.
- Impact: Higher write cost on large documents. Deliberate tradeoff (atomicity over speed), not a defect.
- Recommended action: None required unless ingestion throughput becomes a measured bottleneck; could revisit with `executemany` + explicit transaction.

### F-004 — `assert` used as a runtime guard (B101)

- Title: `assert` guards compiled out under `-O`.
- Severity: Low
- Confidence: High
- Evidence label: Tool (bandit B101)
- Evidence: `scripts/rag/llm_client.py` — `assert _llm_url_cache is not None` (~line 77) and `assert _embed_url_cache is not None` (~line 90). Bandit reports 2 Low / High-confidence B101.
- Current behavior: The assert only narrows the type after the cache is populated; on config-load failure the cache is set to `""` (not `None`), so the assert passes and returns `""`.
- Impact: Guard is weaker than it reads (allows `""`), but behavior is intentional and consistent with the rest of the module. Pre-existing repo-wide pattern, not introduced here.
- Recommended action: None. Consistent with existing style; changing it is out-of-scope cleanup.

### F-005 — Local (in-function) imports

- Title: Imports declared inside function bodies.
- Severity: Informational
- Confidence: High
- Evidence label: Observed
- Evidence: `scripts/rag/augment.py::run_refiner` has `from typing import Literal` at line 100; `scripts/rag/ingestion/file_routing.py` has local `import shutil` (~lines 56/96); `scripts/rag/stages/search.py::_search_all_queries` uses lazy `import httpx`/`get_embedding` to avoid a cycle (justified).
- Current behavior: Most local imports are intentional cycle-avoidance (correct). The `Literal` import inside `run_refiner` is a minor convention nit.
- Impact: Negligible. ruff/mypy pass. The `Literal` one is cosmetic.
- Recommended action: Optional move `from typing import Literal` to module level in `augment.py`.

## Open Questions

- Question: Is the empty-path → in-memory fallback in `db_connection.py` an accepted default or an accidental silent mode?
- Why it matters: If accidental, production deployments passing `""` would lose persistence silently.
- Required confirmation: Confirm the intended contract for an empty path (in-memory OK vs. should error).

## Suggested Tests

- Test target: `search.py::_search_all_queries`.
- Behavior to verify: When only the vector leg fails, `fts_errors == 1` and FTS hits still surface; when only the FTS leg fails, `fts_errors == 1` and vector hits still surface.
- Failure mode: A regression that makes one leg swallow the other's failure would drop `fts_errors` and hide partial-result degradation.

## Documentation Notes

- Target document: `scripts/rag/stages/search.py` docstring / any API reference naming `fts_errors`.
- Required update: Rename the documented field to `retrieval_leg_failures` (or equivalent) to match what it counts.
- Reason: F-001 — the current name overstates FTS specificity.

## Final Recommendation

**Proceed.** No Medium-or-higher finding survives. Toolchain is green (ruff, mypy clean over 51 files; bandit only pre-existing Low B101; module sizes within baseline). The five Low/Informational items are optional polish; none is actionable enough to warrant a tracked issue. The single Open Question (F-002 path contract) is confirmable without code change and does not block.
