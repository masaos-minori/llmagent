# RAG URL key ambiguity

## Priority
Low

## Summary
Resolve the naming overlap between the two RAG service-URL config keys so a developer
cannot confuse the query-path URL with the ingestion-path URL. The keys currently differ
only by an inserted `_pipeline_service` segment, which makes them easy to mix up.

## Background
The resolved RAG config (`scripts/rag/config_resolution.py`) exposes two service-URL
fields, both present in `_ALL_FIELDS` and `_DEFAULTS_FOR_ALL`:

- `rag_service_url` — read by the query path in `scripts/rag/pipeline.py`
  (`if rag_url := self._cfg.rag_service_url`) to decide whether to delegate `augment()`
  to an external RAG service. The MCP server pins it to `""` to prevent an HTTP loop
  (`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`).
- `rag_pipeline_service_url` — read by the ingestion path in
  `scripts/rag/ingestion/ingester.py` (`self._rag_pipeline_service_url = cfg.get(...)`).

Both fields are declared in `RagConfigImpl` (`scripts/rag/models_config.py`) and the
`RagConfig` protocol (`scripts/shared/types.py`). They belong to different subsystems
(query vs ingestion) but share the base name `rag_*_service_url`.

## Problem
The two keys differ only by the `_pipeline_service` segment:

- `rag_service_url`
- `rag_pipeline_service_url`

A developer configuring one subsystem can reasonably assume the other key means the same
thing, or set the wrong one and wonder why delegation never triggers. The names suggest
a hierarchy (one is a "pipeline service" variant of the other) when they are actually
independent keys for independent paths. This is a documentation/footgun risk, not a
runtime failure: both keys resolve and work as wired today.

## Reason for Change
As more RAG URLs are added, near-identical key names increase the chance of misconfiguration and slow code review. Settling the naming now, before more parallel keys appear,
keeps the query and ingestion surfaces distinguishable.

## Implementation Intent
Make the two keys unambiguously distinct by renaming at least one so their purposes are
obvious from the name alone (for example, prefixing the query-path key with `query` or
the ingestion-path key with `ingest`). Apply the rename across every declaration site
(`config_resolution.py`, `models_config.py`, `shared/types.py`) and all callers, and
update the config schema/loader and tests that reference the renamed key. Preserve the
existing default values and validation. Describe the goal (unambiguous per-path naming)
rather than mandating a specific new string.

## Target Files or Areas
- `scripts/rag/config_resolution.py`
- `scripts/rag/models_config.py`
- `scripts/shared/types.py`
- `scripts/rag/pipeline.py` (reader of `rag_service_url`)
- `scripts/rag/ingestion/ingester.py` (reader of `rag_pipeline_service_url`)
- Config schema/YAML and any test fixtures referencing either key

## Required Changes
- Rename one of the two keys so the query-path and ingestion-path URLs are distinguishable
  by name.
- Propagate the rename through every declaration, the protocol, the config loader, and
  all readers.
- Update tests and fixtures that construct configs with the renamed key.
- Keep the renamed key's default and validation identical to the original.

## Constraints
- The rename must not change which path reads which key; behavior is preserved.
- Do not drop either field from the config surface.
- Coordinate any external consumers of the YAML/config key (deploy configs, other
  services) before renaming, since a config key change can break deployments.

## Acceptance Criteria
- Only one of the two keys uses the old spelling; the other uses a purpose-obvious name.
- All readers and declarations reference the renamed key consistently.
- `tests/rag/test_config_resolution.py` and related config tests pass.

## Testing Expectations
- Regression run of `tests/rag/test_config_resolution.py` and any test constructing
  `rag_service_url` / `rag_pipeline_service_url`.
- Confirm the config loader still accepts the renamed key and rejects the old spelling
  (or maps it, if backward-compat is retained).

## Documentation Impact
Document the two keys' distinct purposes in the RAG config reference so future keys are
named consistently and the query-vs-ingestion split is explicit.

## Out of Scope
- Changing the semantics or defaults of either key.
- Renaming unrelated RAG config fields.
- Adding a third service-URL key as part of this issue.

## Dependencies
- Depends on confirming whether the config key is consumed outside this repository
  (deploy configs, other services) before renaming.

## Unresolved Questions
- Whether the query-path key or the ingestion-path key should keep the shorter
  `rag_service_url` spelling (unresolved: no naming convention recorded).
- Whether the config key is referenced in deployed YAML/config outside this repo
  (unresolved: needs a deployment-inventory check).

## AI Implementation Instruction
Rename one of the two near-identical RAG service-URL keys so each path's key is
purpose-obvious, then propagate the rename through `config_resolution.py`,
`models_config.py`, `shared/types.py`, both readers, the config loader, and tests.
Preserve defaults, validation, and behavior. Check for out-of-repo config consumers
before renaming. Keep the diff scoped to the two keys.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-071953
- **Related target files**: scripts/rag/config_resolution.py, scripts/rag/models_config.py, scripts/shared/types.py, scripts/rag/pipeline.py, scripts/rag/ingestion/ingester.py
