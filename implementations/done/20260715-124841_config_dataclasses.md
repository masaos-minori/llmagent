# Implementation Procedure: Normalize configuration schema — remove legacy Memory keys and GitOps security fields

## Status: INVALID — production code does not match plan

The following discrepancies were found between the plan and production code:

1. **RAGConfig**: Plan assumed `top_k_search`, `top_k_rerank`, `rrf_k` fields exist, but production code has none of them.
2. **MemoryConfig**: Plan assumed `use_memory_layer`, `memory_jsonl_dir`, `memory_embed_enabled` fields exist, but production code has none of them.
3. **ToolConfig**: Plan did not account for many existing fields like `tool_definitions_strict`, `routing_drift_strict`, etc.

Production code was already modified independently. This procedure is invalid and archived here.

## Original goal (for reference)

Remove deprecated Memory configuration keys (`use_memory_layer`, `memory_jsonl_dir`, `memory_embed_enabled`) and clarify/remove GitOps security fields (`gitops_force_push_blocked`, `gitops_protected_branches`). Add removed-key validation, include original exception messages in `ConfigLoadError`, and add reload preflight validation.
