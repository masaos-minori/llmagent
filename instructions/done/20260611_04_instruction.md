Refactor the memory layer of this Python codebase.

Target files:
- jsonl_store.py
- mapper.py
- retriever.py
- services.py
- store.py
- types.py
- embedding_client.py
- extract.py
- ingestion.py
- injection.py

Important:
- Do not preserve backward compatibility.
- Remove fallback behavior, silent recovery, and compatibility-style continuation logic.
- types.py is currently unavailable, so first restore or reattach it before finalizing the type design.

Core requirements:
- Do not use assert in business logic. Raise explicit exceptions instead.
- Do not use except Exception. Catch only specific exceptions.
- Do not use dict[str, Any] outside external boundaries. Convert boundary data to typed DTOs immediately.
- Do not use unconditional string conversion such as str(...), str(args.get(...)), or str(msg.get(...)). Validate types strictly and raise on mismatch.
- Do not treat None, empty string, and unset as equivalent.
- Do not return raw dict, tuple, or object from the public API of the memory layer.
- Do not use .get(..., default) to silently fill missing fields for SQLite rows or decoded JSON.
- Validate all decoded JSON with schema validation and fail immediately on mismatch.
- Do not continue on malformed JSONL, invalid DB state, invalid embedding response, or invalid timestamps.
- Do not collapse DB or diagnostic errors into sentinel values such as 0, -1, None, or empty lists.
- Do not print directly from memory-layer logic. Route output through a UI/CLI output interface.

Add these shared modules:
- agent/memory/models.py
- agent/memory/enums.py
- agent/memory/exceptions.py
- agent/memory/ports.py

Introduce explicit DTOs and enums for:
- memory records, rows, search requests/results, neighbors, embedding requests/responses, JSONL records, consistency reports, injection snippets, and extraction candidates
- memory type, source type, embedding error kind, retrieval mode, and extraction decision

Introduce explicit exceptions for:
- schema errors
- storage errors
- JSONL format errors
- consistency errors
- embedding transport/protocol errors
- extraction errors
- unknown memory type errors

Required file-level changes:

1. store.py
- Remove broad exception handling.
- Replace numeric fallbacks such as 0 and -1 with explicit exceptions or typed consistency results.
- Split write, query, and diagnostic responsibilities.

2. embedding_client.py
- Replace broad exception handling with specific HTTP, transport, JSON, and schema errors.
- Convert response bodies to validated EmbeddingResponse DTOs.
- Do not silently absorb disabled, timeout, circuit-open, or invalid-response states.

3. jsonl_store.py
- Remove strict=False continuation and quarantine-based recovery.
- Fail immediately on malformed JSONL.
- Replace raw dict input with validated JsonlRecord DTOs.
- Replace generic serialization with an explicit serializer.

4. mapper.py
- Stop accepting dict[str, Any].
- Accept only validated row DTOs.
- Remove .get(..., default) completion and unconditional float/bool conversion.

5. extract.py
- Replace shared.types.LLMMessage access with memory-specific message DTOs.
- Remove .get() access and unconditional str(...) conversion.
- Replace None-based extraction decisions with explicit decision DTOs or enums.

6. ingestion.py
- Remove broad exception handling.
- Split extraction, deduplication, persistence, and linking into separate stages.
- Pass all manual write operations through request DTOs.

7. retriever.py
- Do not absorb invalid timestamps as score 0.0.
- Treat invalid timestamp format as a schema error.
- Split query building, scoring, SQL access, and merge strategy.

8. injection.py
- Reject empty queries through validation instead of silently returning [].
- Do not silently continue with embedding=None after embedding failure.
- Replace implicit snippet fallback logic with explicit snippet DTOs.

9. services.py
- Replace shared.types.LLMMessage dependency with memory-specific history DTOs.
- Make the facade API strictly DTO-based.

10. types.py
- Restore the file first.
- Audit current DTOs, enums, and exceptions.
- If current types are dict- or TypedDict-based, replace them with explicit immutable DTOs.

Execution order:
1. Restore types.py
2. Add shared DTO/enums/exceptions/ports modules
3. Refactor mapper.py and jsonl_store.py
4. Refactor store.py
5. Refactor embedding_client.py
6. Refactor extract.py, ingestion.py, and injection.py
7. Refactor retriever.py
8. Refactor services.py
9. Update dependent callers
10. Update tests and static checks

Tests to add:
- malformed JSONL
- invalid memory row
- invalid embedding response schema
- invalid timestamp in retrieval
- embedding timeout
- memory_links insert failure

Definition of done:
- types.py is restored and the type design is finalized.
- No broad exception handling remains in the 10 target files.
- No internal dict[str, Any] remains beyond external boundaries.
- No unconditional string conversion remains.
- No quarantine continuation or DB diagnostic fallback remains.
- Embedding responses, memory rows, and history messages are schema-validated after decode.
- Public contracts for retrieval, extraction, injection, and ingestion use explicit DTOs and specific exceptions.
- mypy --strict passes.
- ruff check passes.
- pytest passes.
