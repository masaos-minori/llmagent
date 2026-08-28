---
title: "Deprecated Items"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---

# Deprecated Items

## Deprecated Compatibility Formats

The following compatibility formats were removed during the MCP Schema 2.0 enforcement and RAG ingestion pipeline hardening workstreams. Each entry records the exact behavior that was eliminated — these are historical removals, not available aliases or migration paths.

- **`input_schema` (snake_case alias)** — Removed; replaced by canonical `inputSchema` only. The fallback `entry.get("inputSchema", entry.get("input_schema"))` was eliminated from `scripts/agent/services/mcp_tool_discovery.py`. No server-side changes required — all production MCP servers emit canonical `inputSchema`.
- **Legacy singular `resource_scope` field** — Removed; no longer accepted in any form. Entries carrying this field are rejected via `StartupCheckOutcome` during discovery. The optional-field type-check tuple `("resource_scope", str)` was removed from `_validate_and_normalize_entry()`.
- **Missing `schema_version` tolerance** — Removed; `/v1/tools` responses without `schema_version` are rejected. Discovery-time rejection via `_warning_fetch_result(...)` excludes the server when `schema_version` is absent or does not match `"1.0"`.
- **`fetched_at` fallback / null-fill (`_update_null_fill()`)** — Removed; `fetched_at` is now mandatory `str` across every layer of the RAG ingestion pipeline. The null-fill branch in `ETagManager.update()` and the method body `_update_null_fill()` were deleted outright. Timestamp validation changed from fail-open to fail-closed.
- **`chunk_index` coercion** — Removed; `_normalize_chunk_index()` was deleted. No implicit conversion of chunk indices occurs.

## Related Documents

Cross-cutting documentation rules and policies:

- [Documentation Policy](00_governance_01_documentation-policy.md)
- [Documentation Metadata](00_governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](00_governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](00_governance_04_documentation-checks.md)

## Keywords

deprecated
compatibility
removal
registry
governance
