---
title: "Shared Runtime and Execution - Caching and Reference (Part 1)"
category: shared
tags:
  - shared
  - runtime
  - retry-handler
  - tool-cache
  - tool-spec
  - ai-reference
related:
  - 90_shared_00_document-guide.md
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
  - 90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md
source:
  - 90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md
---

# 共有ランタイムおよび実行インフラストラクチャ

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 14. `LlmRetryHandler` (`shared/llm_retry.py`)

Exponential backoff retry for HTTP POST requests to LLM endpoints. Retries on 429 (rate limit), 503 (service unavailable), and httpx.RequestError (connection error). Non-transient HTTP errors (4xx/5xx other than 429/503) raised immediately. Delay formula: retry_base_delay * (2**attempt) where attempt starts at 0. Last exception raised when all retries exhausted.

---

## 15. `ToolResultCache` / `CacheEntry` (`shared/tool_cache.py`)

Frozen dataclass CacheEntry with output (str), is_error (bool), cached_at (float). Standalone LRU+TTL cache utility for tool results. Not currently used by ToolExecutor; kept for potential future use without stampede protection. Key = {tool_name}:{json_dumps(args)} using shared.json_utils.dumps. store_if_success() stores only is_error=False results.

---

## 16. `ToolSpec` (`shared/tool_spec.py`)

Frozen dataclass for DAG scheduling metadata. call_id (LLM-assigned tool call id from tool_calls[].id), name (tool function name), args (dict[str, object]), resource_scope (resource path/branch string for conflict detection), requires_serial (forces serialization regardless of parallel mode), is_write (used by is_side_effect() to classify write/delete tools). DAG execution layer builds ToolSpec for each approved tool call.

---


