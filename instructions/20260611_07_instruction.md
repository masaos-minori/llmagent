# Refactoring Plan

## Overall Policy
- Do not preserve backward compatibility. Remove compatibility entry points, re-exports, fallbacks, placeholders, and ambiguous compatibility aliases.
- Do not use `assert` in business logic. Express precondition violations with explicit exceptions.
- Do not use `except Exception`. Split exception handling into specific exception types such as HTTP, JSON, SQLite, LLM, and I/O errors.
- Do not use `dict[str, Any]` outside external boundaries. Convert data into DTOs, enums, or validated types immediately after crossing a boundary.
- Avoid ambiguous string conversion or fallback patterns such as `str(args.get(...))`, `str(entry[0])`, or `c.get('title') or ...`. Validate the type first and process only after successful validation.
- Do not treat `None`, empty strings, unset values, and invalid values as equivalent.
- Define audit logs, approval decisions, and execution results as dedicated DTOs. Do not rely on dictionaries for return values or shared state.
- Validate LLM-derived JSON against a schema immediately after decoding. Fail immediately on schema mismatch.
- Do not output directly with `print()`. Route output through a UI/CLI interface or a presenter.
- For unknown tool names, unknown tiers, and unknown metadata, use fail-fast behavior instead of fail-open behavior.

## Implementation Rules

### Mandatory Rules
- Refactor the public APIs of the RAG, ingestion, search, and stage layers toward request DTO / result DTO-based interfaces.
- Replace surrounding types such as `RawHit`, `MergedHit`, `RankedHit`, `PipelineContext`, and `SearchDocsRequest` from TypedDict-centered structures to stricter dataclasses, immutable DTOs, and enums.
- Represent stage names, tier names, language values, and search result categories with enums instead of raw string comparisons.
- Reduce implementations that return `None` on failure, swallow errors with empty lists, or continue through fallback behavior. Make failure reasons explicit through dedicated exceptions or result DTOs.
- Apply common validation, serialization, and logging rules across both the ingestion pipeline (`crawl -> chunk -> ingest`) and the retrieval pipeline (`MQE -> search -> fusion -> rerank -> augment`).

### Common Elements to Add or Reorganize
- Add the following under `rag/models.py` or another appropriate layer:
  - `EmbeddingResponse`
  - `RagSearchRequest`
  - `RagSearchResult`
  - `PipelineExecutionResult`
  - `AuditLogRecord`
  - `ApprovalDecision`
  - `ChunkDocument`
  - `ChunkRecord`
  - `RegisteredDocument`
  - `SearchDocsResult`
- Add the following under `rag/enums.py`:
  - `LanguageCode`
  - `PipelineStageName`
  - `HitKind`
  - `ToolSafetyTier`
  - `SearchBackend`
- Add the following under `rag/exceptions.py`:
  - `EmbeddingSchemaError`
  - `PipelineValidationError`
  - `SearchQueryError`
  - `ChunkFormatError`
  - `UnknownTierError`
  - `UnknownMetadataError`

## File-by-File Changes

### `rag/pipeline.py`
- Replace `_cfg: dict[str, Any] | None` and `_get_cfg() -> dict[str, Any]` with a strict config DTO.
- Reorganize the structure that re-exports `get_embedding` and `sanitize_document` via `__all__` in accordance with the no-backward-compatibility policy.
- The pipeline currently centralizes shared state into `PipelineContext`, but it remains mutable. Introduce explicit input/output DTOs for each stage.
- Do not collapse all pipeline exceptions into `RagPipelineError`. Separate configuration errors, database errors, and stage execution errors.

### `rag/stage.py`
- Remove `PipelineContext.search_results: list[Any]` and `observers: list[Any]`, and replace them with dedicated DTOs and/or Protocols.
- Narrow `PipelineStage.run(..., **kwargs: Any)` into a typed request context.

### `rag/types.py`
- Remove the backward-compatibility re-export of `LLMMessage`.
- Remove the compatibility alias `RagHit = RawHit | MergedHit | RankedHit` and separate DTOs by specific purpose.
- Reconsider the use of `TypedDict(total=False)`. Express required fields explicitly using dataclasses, pydantic models, or equivalent typed structures.

### `rag/repository.py`
- Remove backward-compatible re-exports such as `SemanticCache as SemanticCache` and `cosine_sim as cosine_sim`.
- Replace the Sudachi tokenizer cache that uses `Any`, and replace dictionary merging such as `merged.append({**item, "rrf_score": 0.0})` with DTO-based handling.
- Handle ambiguous FTS query outputs such as empty strings or `""` through a search request validator.
- Separate the mapper that converts SQL results into `RawHit`, and clarify the boundary between SQLite rows and DTOs.

### `rag/cache.py`
- Replace `self._entries: list[dict[str, Any]]` with a `CacheEntry` DTO.
- Remove dictionary-style access such as `entry["embedding"]` and `entry["context_str"]`.
- Organize max size, threshold, and dimension mismatch handling through config DTOs and dedicated exceptions.

### `rag/llm.py`
- Replace `_mqe_prompt()`, `_extract_chat_content()`, and `summarize_tool_result()`, which currently accept `dict[str, Any]`, with strict DTO-based inputs.
- Remove unconditional string conversion such as `return str(cfg.get(...).format(...))`.
- Replace `orjson.loads(resp.content).get("embedding")` with schema validation immediately after decoding.
- Separate response parsers for embedding, MQE, rerank, summarize, and refiner into dedicated validators.
- Refine `RagExpansionError` and `RagRerankError` into more specific categories such as HTTP, JSON, schema, and timeout errors.

### `rag/ingestion/pipeline_utils.py`
- Replace `read_json_file() -> dict[str, Any] | None` with DTO returns such as `ChunkDocument`.
- Stop returning `None` on failure. Propagate `JSONDecodeError`, `OSError`, and schema validation errors to the caller.
- Convert `collect_source_files()` and `is_already_processed()` into result DTOs as well, so skip reasons become visible.

### `rag/ingestion/crawler_utils.py`
- Replace `parse_target_urls(target_raw: list[Any])` with a strict request DTO-based interface.
- Remove unconditional string conversion such as `url, lang = str(entry[0]), str(entry[1])`.
- Replace `text or fallback` in `extract_text()` with a result DTO that includes the extraction source.
- Change `detect_lang() -> str | None` to return an enum, and represent `None` explicitly as an undetermined state.

### `rag/ingestion/crawler.py`
- Separate the CLI entry point from the crawler implementation, and convert config loading, argument parsing, and execution results into DTOs.
- Remove `typing.Any` and make crawl input and crawl output strict and typed.
- Split HTTP, parsing, file writing, and SQLite update errors into stage-specific categories.

### `rag/ingestion/chunk_utils.py`
- Make it possible to preserve the tail-merge rule of `merge_text_items()` as result metadata.

### `rag/ingestion/chunk_english.py`
- Make implicit dependencies such as `_max_chunk`, which are injected from `ChunkSplitter`, explicit through the constructor.
- Preserve the behavior of discarding short text after stopword removal as result DTO fields or metrics.

### `rag/ingestion/chunk_japanese.py`
- Replace `_sd_tkn: Any` and `_split_c: Any` with a type-safe wrapper.
- Rework the design that continues with an empty string after `except RuntimeError`, and instead make tokenization failures detectable through a result DTO.
- Combine the dual representation of normalized/original text into a `JapaneseChunkPair` DTO.

### `rag/ingestion/chunk_splitter.py`
- Remove `typing.Any` and dictionary-based JSON assumptions, and accept only crawler output DTOs.
- Route chunk output JSON through a dedicated serializer.
- Reconsider the mixin-based design in favor of a strategy/service structure, and reduce the responsibility of `ChunkSplitter`.

### `rag/ingestion/ingester.py`
- Eliminate reliance on `typing.Any` and dict-based results from `read_json_file()`, and accept only chunk DTOs.
- Convert embedding generation results, database registration results, and move-to-registered results into dedicated DTOs.
- Move force re-ingestion logic and URL validation into validators.
- Make thread-pool-based parallel processing failures explicit in an execution result DTO.

### `rag/stages/mqe.py`
- Replace `cfg: dict` and `cfg.get("use_mqe", True)` with DTOs and enums.
- Do not hide `return [query]` as a fallback when disabled. Represent the disabled state explicitly in the execution result DTO.
- Convert query expansion results from `list[str]` to an `ExpandedQuerySet` DTO.

### `rag/stages/fusion.py`
- Replace `cfg: dict` and `cfg.get("rrf_k", 60)` with a strict config DTO.
- Do not assign directly to `ctx.merged`. Return a fusion result DTO instead.

### `rag/stages/rerank.py`
- Replace `cfg: dict` and `cfg.get("use_rerank", True)` with a strict config DTO.
- Represent the fallback to RRF order when disabled as an explicit stage result.
- Do not perform deduplication implicitly inside the stage before and after reranking. Separate that responsibility.

### `rag/stages/augment.py`
- Replace the untyped list in `_format_chunks(reranked: list)` with `RankedHit` DTOs.
- Prohibit ambiguous fallback logic such as `c.get('title') or c['url']`, and model title presence explicitly in the type system.
- Define a DTO that carries not only the final augment string, but also source information, boundary markers, and sanitize results.

### `rag/utils.py`
- Make the `0.0` behavior of `cosine_sim()` on zero vectors explicit as a defined specification, and distinguish invalid vectors from legitimate zero scores.
- Make the detection results of prompt-injection patterns in `sanitize_document()` auditable.

### `mcp/mdq/search.py`
- Remove the placeholder implementation and replace it with a real implementation that returns a search result DTO.
- Stop returning `str`; return `SearchDocsResult` instead.
- Separate the FTS5 execution layer from the message-formatting layer.

## Work Steps
1. Identify and remove compatibility-only elements such as re-exports, compatibility aliases, and placeholders.
2. Define common RAG DTOs, enums, and exceptions first, centered around `types.py`, `stage.py`, and `pipeline.py`.
3. Apply strict validation to boundary processing in `llm.py`, `pipeline_utils.py`, and `crawler_utils.py`.
4. Refactor the ingestion layer (`crawler`, `chunk_splitter`, `ingester`) to DTO-based flow and reduce dependencies on `dict` and `Any`.
5. Refactor the retrieval layer (`mqe`, `fusion`, `rerank`, `augment`, `repository`, `cache`) toward DTOs, enums, and fail-fast behavior.
6. Replace the placeholder in `mcp/mdq/search.py` with a real implementation and unify the output around search result DTOs.
7. Standardize logging, audit, approval, and execution-result DTOs.
8. Update static typing checks, unit tests, and regression tests.

## Definition of Done
- Compatibility-only code such as re-exports, compatibility aliases, placeholders, and continuation-oriented fallbacks has been removed.
- `dict[str, Any]` and `Any` have been removed from internal code outside external boundaries.
- Ambiguous completion patterns based on `str(args.get(...))`, `str(entry[0])`, and `.get(..., default)` have been removed.
- LLM JSON, crawl JSON, chunk JSON, and DB rows are schema-validated immediately after decode or retrieval.
- `except Exception` does not exist.
- Return values across ingestion, retrieval, and search are unified around request DTOs and result DTOs.
- Dedicated DTOs for audit logs, approval decisions, and execution results are defined and used in at least the main flows.
- Unknown tools, unknown tiers, and unknown metadata are handled with fail-fast behavior.
- Output is centralized through a presenter or UI/CLI interface.
- `mypy --strict`, `ruff check`, and `pytest` all pass.
