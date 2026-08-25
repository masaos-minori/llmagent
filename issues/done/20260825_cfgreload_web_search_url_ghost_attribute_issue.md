# `web_search_url` is set on RAGConfig during reload but is not a defined field

## Priority
Medium

## Summary
`_apply_llm_prompt_params()` in `config_reload.py` executes `setattr(cfg.rag, "web_search_url", v)`, but `RAGConfig` (`scripts/agent/config_dataclasses.py`) defines no `web_search_url` field. Python dataclasses allow dynamic attribute assignment, so this silently creates a ghost attribute that nothing else reads.

## Background
N/A: covered by Summary — likely a leftover from an older config spec.

## Problem
Verified:
- `scripts/agent/services/config_reload.py:354` contains `_apply_str(new_cfg, "web_search_url", lambda v: setattr(cfg.rag, "web_search_url", v))`.
- `RAGConfig`'s field list (`scripts/agent/config_dataclasses.py`, confirmed fields: `embed_url`, `use_semantic_cache`, `semantic_cache_threshold`, `semantic_cache_max_size`, `use_refiner`, `refiner_max_tokens`, `refiner_timeout`, `refiner_max_chars_per_chunk`, and others) does not include `web_search_url`.
- No consumer of `cfg.rag.web_search_url` was found in this pass; a repository-wide search should be run at implementation time to confirm before removing the line (see AI Implementation Instruction).

## Reason for Change
A config field that is written but never read (or read only via a dynamically-created attribute with no declared type) is a maintenance hazard: it looks configurable to an operator inspecting reload payloads, but has no effect and no compile-time visibility.

## Implementation Intent
Investigate whether any code reads `cfg.rag.web_search_url` (or `web_search_url` from any related config surface). If unused, remove the reload line. If it turns out to be used somewhere not surfaced by this issue's search, promote it to a first-class, declared field on the appropriate config dataclass instead of leaving it as a dynamic attribute.

## Target Files or Areas
- `scripts/agent/services/config_reload.py`
- `scripts/agent/config_dataclasses.py` (`RAGConfig`)
- `scripts/shared/types.py` (`RagConfig` protocol, if one exists) — consumer check
- `scripts/agent/config_builders.py` — loader check

## Required Changes
- Run `grep -rn "web_search_url" scripts/` at implementation time to get a current, authoritative list of all references.
- If no consumer exists: remove the `_apply_str(new_cfg, "web_search_url", ...)` line from `_apply_llm_prompt_params()`.
- If a consumer exists: add `web_search_url` as a declared field on the owning config dataclass and wire it through the loader (`config_builders.py`) so it is validated and typed consistently with other fields.

## Constraints
- N/A: none beyond confirming the field is genuinely unused before removing it.

## Acceptance Criteria
- [ ] No ghost (undeclared) attribute is created on `RAGConfig` via `/reload`.
- [ ] Either the reload line is removed, or `web_search_url` is formally declared and consumed consistently.

## Testing Expectations
- `grep -rn "web_search_url" scripts/` shows a consistent, intentional result (either zero hits after removal, or a fully wired field).
- Regression: existing `_apply_llm_prompt_params()` tests for the surrounding fields continue to pass.

## Documentation Impact
If any doc lists `web_search_url` as a configurable field, correct it to match whichever resolution (removal or formalization) is chosen.

## Out of Scope
- Adding new web-search functionality.
- Changing any other field in `_apply_llm_prompt_params()`.

## Dependencies
- N/A: none.

## Unresolved Questions
- Whether `web_search_url` was ever a real, consumed field on a different config surface (e.g. the web_search MCP server's own config, `web_search_mcp_server.toml`, rather than `RAGConfig`) and this line is a stale cross-wiring from an earlier design. Confirm via the repository-wide grep before deciding removal vs. formalization.

## AI Implementation Instruction
Do the `grep -rn "web_search_url" scripts/` investigation first and report findings before choosing removal vs. formalization — do not default to deletion without confirming there is truly no reader, since a config field silently going from "ineffective" to "type-error on missing attribute" (if something reads it via `getattr` with no default) would be a regression.
