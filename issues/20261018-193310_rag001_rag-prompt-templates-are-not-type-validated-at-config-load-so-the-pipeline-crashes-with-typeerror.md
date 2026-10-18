# RAG prompt templates are not type-validated at config load so the pipeline crashes with TypeError

## Priority
Medium

## Summary
The RAG prompt-template config values (`mqe_prompt_template`, `rerank_prompt_template`) are not type-validated at config load. When a configured template is not a `str`, `_mqe_prompt` / `_build_rerank_prompt` raise `TypeError`, which is not caught by the MQE or rerank error handlers, so the entire `RagPipeline.run()` aborts with an unhandled `TypeError` instead of failing fast at startup or falling back gracefully.

## Background
The RAG pipeline builds its multi-query-expansion and cross-encoder prompts via `_mqe_prompt()` and `_build_rerank_prompt()` in `scripts/rag/llm_prompts.py`. Both raise `TypeError` when the corresponding `cfg` template attribute is not a `str`. They are invoked from `RagLLM.expand_queries()` (MQE) and `RagLLM.cross_encoder_rerank()` (rerank).

The resolved config comes from `resolve_rag_config()` in `scripts/rag/config_resolution.py`, which fills defaults for missing fields and delegates to `RagConfigValidator.validate()` in `scripts/shared/config_validator.py`. That validator only checks `use_rrf` (warning) and removed semantic-cache keys (error); it never validates the type or shape of the prompt-template strings.

## Problem
Trace of the exception path when a non-string template reaches the pipeline:

1. `MqeStage.run` calls `_run_mqe` -> `RagLLM.expand_queries`, which evaluates `_mqe_prompt(...)` inside its `try`.
2. `expand_queries` catches only `(httpx.HTTPStatusError, httpx.RequestError, orjson.JSONDecodeError, MqeParseError)`. `TypeError` is not among them, so it propagates.
3. `MqeStage.run` catches only `RagExpansionError`, so it propagates further.
4. The shared `_run_stage` wrapper catches only `(RuntimeError, sqlite3.OperationalError, httpx.HTTPStatusError, httpx.RequestError, TimeoutError)`. `TypeError` is again uncaught, so it leaves `RagPipelineStageLifecycle.run()` / `RagPipeline.run()` unhandled.

The same gap exists for rerank:

1. `cross_encoder_rerank` evaluates `_build_rerank_prompt(...)` inside its `try`.
2. It catches `(httpx.HTTPStatusError, httpx.RequestError, ValueError)`. `TypeError` is not a `ValueError`, so it propagates.
3. `RerankStage.run` catches only `RagRerankError`, so it propagates.

Result: a misconfigured non-string prompt template aborts the whole pipeline run with an unhandled `TypeError`, rather than failing fast at startup (where it belongs under the typed-config policy in `rules/coding.md`) or degrading gracefully.

## Reason for Change
The typed-config policy in `rules/coding.md` (Type-coercion policy) requires config loaders to validate field types and reject wrong types at load time. Prompt templates are currently the one class of RAG config that slips through validation entirely, so a bad value surfaces as a deep runtime crash instead of an early, actionable config error.

## Implementation Intent
Add prompt-template type validation to the startup validator so a non-string template fails fast with a clear, key-naming error. Prefer fixing at the config-validation boundary over adding broad `except TypeError` handlers, because fail-fast at startup is the intended control and matches the typed-config policy. A targeted defense-in-depth guard in the stage handlers is optional; do not mask the root cause there.

## Target Files or Areas
- `scripts/shared/config_validator.py` — `RagConfigValidator.validate`
- `scripts/rag/config_resolution.py` — `resolve_rag_config`
- `scripts/rag/llm_prompts.py` — `_mqe_prompt`, `_build_rerank_prompt`
- `scripts/rag/llm_client.py` — `RagLLM.expand_queries`, `RagLLM.cross_encoder_rerank`
- `scripts/rag/stages/mqe.py` — `MqeStage.run`
- `scripts/rag/stages/rerank.py` — `RerankStage.run`

## Required Changes
- Validate that `mqe_prompt_template` and `rerank_prompt_template` are strings in `RagConfigValidator.validate`; append an error (and set `ok=False`) when either is missing or not a `str`.
- Make the error message name the offending key so the operator can fix the config.
- Confirm no code path allows a non-string template to reach `MqeStage` / `RerankStage` as an uncaught `TypeError`.

## Constraints
- Do not change the default template values or their `{query}` format contract.
- Keep the existing warning/error split in `RagConfigValidator` (this is an error, not a warning).
- Validation must not silently accept wrong types (per `rules/coding.md` type-coercion policy).

## Acceptance Criteria
- A config with a non-string `mqe_prompt_template` or `rerank_prompt_template` makes `resolve_rag_config` raise with an error naming the key, before any pipeline run.
- A config with valid string templates resolves normally.
- No runtime path allows a non-string template to reach the pipeline stages as an uncaught `TypeError`.

## Testing Expectations
- Unit test that `RagConfigValidator.validate` rejects a non-string template with `ok=False` and a message naming the key.
- Unit/integration test that `resolve_rag_config` raises on a non-string template and succeeds on a string template.
- Regression test that a non-string template does not produce an uncaught `TypeError` from `RagPipeline.run`.
- Run `ruff check`, `mypy`, `bandit`, and the affected test targets before closing.

## Documentation Impact
No `docs/*.md` change required unless the RAG config reference documents template validation. If it does, note only that template types are validated at startup (intent/boundary), not implementation detail.

## Out of Scope
- Do not refactor the MQE / rerank prompt-building logic beyond type handling.
- Do not add generic global exception handlers around the pipeline.
- Do not change validation of other RAG config fields.

## Dependencies
N/A: none (no open sibling issue covers RAG config validation).

## Unresolved Questions
- Should the fix live solely in `RagConfigValidator`, or should the stage handlers also degrade gracefully if a bad value bypasses validation? Recommend the config-boundary fix as primary.
- Are there production call sites that pass templates programmatically (bypassing TOML) and would now fail at construction where they previously ran with a coerced default?

## AI Implementation Instruction
Fix at the config-validation boundary first; confirm `resolve_rag_config` raises before any pipeline run. Do not add broad `except Exception` / `except TypeError` handlers that mask config errors. Preserve default template values and the `{query}` format contract. Verify with the full affected test suite plus `ruff` / `mypy` / `bandit`.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261018-193310
- **Related target files**: scripts/shared/config_validator.py, scripts/rag/config_resolution.py, scripts/rag/llm_prompts.py, scripts/rag/llm_client.py, scripts/rag/stages/mqe.py, scripts/rag/stages/rerank.py
