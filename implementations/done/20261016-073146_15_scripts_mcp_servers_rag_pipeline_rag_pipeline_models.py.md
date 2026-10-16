## Goal

Expose the RAG Pipeline server's configuration inputs for self-validation and add the validation
results, so rag-pipeline-mcp validates its own configuration and publishes the common Security
Posture instead of being checked only by a `deps` probe (`REQ-010`, `AC-005`).

## Scope

- One modified module `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`: add a non-secret
  config view used for fingerprinting.
- One new module `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py` (Plan row `55`, added
  by amendment while executing this row): the RAG self-validation function that produces
  `SecurityCheckResult` values. See Details for why the validator is not in the models module.
- Publishing on `/health` and the Ready gate are row `46`
  (`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py:163-167`).

## Assumptions

- Current config model verified: `RagPipelineConfig` at
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py:39` with `llm_url` (`:42`), `embed_url`
  (`:43`), `rag_db_path` (`:44`), `sqlite_vec_so` (`:45`), `sqlite_timeout` (`:46`),
  `sqlite_busy_timeout_ms` (`:47`), `mqe_n_queries` (`:48`), `use_mqe`/`use_rrf`/`use_rerank`/
  `use_refiner` (`:51-55`), `rrf_k` (`:53`), `top_k_search` (`:56`), `top_k_rerank` (`:57`),
  `rag_top_k` (`:58`), `rag_min_score` (`:59`), `max_chunks_per_doc` (`:60`), `refiner_max_tokens`
  (`:61`), `refiner_max_chars_per_chunk` (`:62`), `refiner_timeout` (`:63`), and the two Secret
  fields `rag_auth_token` (`:64`) and `auth_token` (`:65`). `RagPipelineServiceError` is at `:29`.
- Today's only startup-time check is `_check_health_deps()` in
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py:150-160`, which reports
  `deps["embed_url"] = "not configured"` and swallows every config error with a bare `except Exception`
  at `:157-158`.
- Plan `UNK-03`: the precise RAG check granularity is derived here from `REQ-010` because `memo2.md`
  is unrecoverable. **Needs confirmation**.

## Design decisions

- Add `RagPipelineConfig.non_secret_view(self) -> dict[str, object]` (new method) that returns the
  config view the posture fingerprint is computed from, excluding `auth_token` (`:65`) and
  `rag_auth_token` (`:64`). This is the "expose config inputs" half of `REQ-010`: row `03` computes
  the posture fingerprint over a normalized non-secret view, and without a view owned by the server
  the Agent would have to read `rag_pipeline_mcp_server.toml` itself, which `REQ-017` removes.
- The view carries scalar settings as values and carries `llm_url`, `embed_url`, `rag_db_path`,
  `sqlite_vec_so`, both auth tokens, and the prompt templates as presence booleans only.
  **Resolved (user decision)**: `compute_config_fingerprint()` (row `03`, already frozen) runs every
  string through `assert_non_secret()`, which rejects an absolute path, a credential-shaped value,
  and a config section header. The deployed config carries `rag_db_path =
  "/opt/llm/db/rag.sqlite"` and `sqlite_vec_so = "/opt/llm/sqlite-vec/vec0.so"`, so a view holding
  those values by value would make `common.own_config_only` `FAILED` and stop this server from
  starting once row `46` wires the posture. Row `51` (`web_search_models.py`) already uses the same
  scalars-plus-presence shape.
- Add `validate_rag_pipeline_security(cfg: RagPipelineConfig) -> list[SecurityCheckResult]` (new
  module-level function) in `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py`.
- Check ids (finalized here, Needs confirmation):
  - `server.embed_url_configured` — empty `embed_url` is `FAILED` with reason `config_missing`. This
    is the security view of the check the server already performs at
    `rag_pipeline_server.py:154-155`.
  - `server.llm_url_configured` — empty `llm_url` is `FAILED` with reason `config_missing` when
    `use_rerank` or `use_refiner` is enabled, and `NOT_APPLICABLE` with reason `not_applicable`
    otherwise, because the LLM is only contacted on those paths.
  - `server.rag_db_path_configured` — empty `rag_db_path` is `FAILED` with reason `config_missing`.
  - `server.sqlite_vec_available` — `sqlite_vec_so` empty, or a path whose file does not exist, is
    `FAILED` with reason `dependency_unreachable`; vector search cannot run without the extension.
  - `server.top_k_bounds` — any of `top_k_search`, `top_k_rerank`, `rag_top_k` being `<= 0`, or
    `rag_top_k > top_k_rerank`, is `FAILED` with reason `config_invalid`: the pipeline would return
    nothing or discard reranked results it just produced.
  - `server.min_score_valid` — `rag_min_score < 0` is `FAILED` with reason `config_invalid`; a
    negative distance threshold silently filters every hit.
  - `server.refiner_limits` — `use_refiner` enabled with `refiner_max_tokens <= 0` or
    `refiner_max_chars_per_chunk <= 0` is `FAILED` with reason `config_invalid`; otherwise
    `NOT_APPLICABLE` with reason `not_applicable`.
- No check inspects or reports a token value. Token presence is enforced by the server's auth
  middleware and by the Agent's `mcp_auth` check (`scripts/agent/startup_validation.py:70-81`), and
  `REQ-002` forbids carrying Secret values in the posture.
- The function is pure: it stats `sqlite_vec_so` and `rag_db_path` but never opens a database or
  connects to `llm_url` / `embed_url`, so validation cannot issue an outbound request.

## Alternatives considered

- Keep only the existing `_check_health_deps()` probe — rejected: it checks one field, swallows all
  other config errors (`rag_pipeline_server.py:157-158`), and produces no posture, so `REQ-012` and
  `REQ-013` would have nothing to validate.
- Compute the fingerprint from the raw config dict — rejected: the raw dict contains
  `auth_token` and `rag_auth_token`, so a fingerprint over it would be derived from Secrets and could
  be brute-forced; `non_secret_view()` is the boundary that keeps them out.
- Put the validator in `rag_pipeline_service.py` — rejected: `REQ-010` names the models module, and
  the validator is a function of the config shape, not of pipeline execution. The sibling module
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py` (row `55`) is the accepted placement
  once the models module crossed the size trigger.

## Implementation
### Target file

- `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` (modify) — `non_secret_view()`
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py` (new, Plan row `55`) — the validator

### Procedure

1. Import `SecurityCheckResult`, `SecurityCheckStatus`, and the reason-code constants from
   `shared.security.result_dto` (row `02`) in the module that defines each new symbol.
2. Add `non_secret_view()` (new) to `RagPipelineConfig` after the field definitions.
3. Add `validate_rag_pipeline_security()` (new) and its per-check helpers to
   `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py`, which imports
   `RagPipelineConfig` from the models module.
4. Leave `RagRunRequest`, `RagRunResponse`, `HitDict`, `DocumentItem`, `PipelineCapture`,
   `build_rag_cfg_adapter()`, and `RagPipelineServiceError` unchanged.

### Method

- Fixed check order: `server.embed_url_configured`, `server.llm_url_configured`,
  `server.rag_db_path_configured`, `server.sqlite_vec_available`, `server.top_k_bounds`,
  `server.min_score_valid`, `server.refiner_limits`.
- `non_secret_view()` carries `own_config_file`, the scalar settings, and presence booleans for the
  URLs, paths, prompt templates, and both tokens. It is the single source of the fingerprint input
  (row `03`); the validator reads the config fields directly, so a check can report a state the view
  deliberately does not carry by value.
- Messages name the setting and its state (`embed_url is not configured`,
  `rag_top_k exceeds top_k_rerank`). URL values are reported as "configured" or "not configured";
  `rag_db_path` and `sqlite_vec_so` are sensitive paths and are reported by state, not by value.

### Details

- The models module is 244 lines before the change, and the validator would have carried it to 441
  lines, past the 400-line split trigger in `skills/DESIGN.md`. **Resolved (user decision)**: the
  validator moved to the new sibling module `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py`
  (170 lines) and `non_secret_view()` stayed in the models module (284 lines). The Plan's frozen
  table was amended by appending row `55` after row `54`, so the ordinal of every existing row that
  the procedure documents cite is unchanged.
- `RagPipelineConfig` is a plain dataclass (not frozen), so `non_secret_view()` must build a new dict
  rather than expose internal mutable state.
- The existing `except Exception:  # noqa: BLE001` in the server's health probe is not modified here;
  row `46` replaces that probe's role for security data.

## Compatibility considerations

- Additive change: no field, default, or type changes, so `tests/mcp_servers/rag_pipeline/*` keep
  passing.
- Behavior change appears only once row `46` publishes the posture: rag-pipeline-mcp with a missing
  `embed_url`, missing `sqlite_vec_so`, or inverted `top_k` bounds reports `ready=false` (HTTP 503
  through the existing handler contract). Today a missing `embed_url` already degrades `/health`
  (`rag_pipeline_server.py:154-155`), so that case is a strengthening, not a new failure.
- No `docs/*.md` change is in scope for this row.

## Security considerations

- `REQ-010` / Plan `INV-05`: rag-pipeline-mcp validates its own configuration before Ready; the
  Agent never reads `rag_pipeline_mcp_server.toml`.
- `REQ-002` / Plan `INV-09`: `auth_token` and `rag_auth_token` are Secrets and are excluded from
  `non_secret_view()`, the fingerprint, and every message; paths and URLs are reported by state only.
- Keeping the fingerprint derived from a server-owned non-secret view is what makes row `17`'s
  fingerprint comparison possible without a cross-config read.

## Rollback considerations

- Revert this commit together with row `46`, which imports both new symbols. No config or data
  migration is involved.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Missing embed url | `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_security_validation.py` (new test file) | `server.embed_url_configured` `FAILED`, reason `config_missing` |
| LLM url required only when used | same new test file | empty `llm_url` is `FAILED` with `use_rerank=true` and `NOT_APPLICABLE` with `use_rerank=false` and `use_refiner=false` |
| Missing sqlite-vec | same new test file | `server.sqlite_vec_available` `FAILED`, reason `dependency_unreachable` |
| Inverted top-k bounds | same new test file | `server.top_k_bounds` `FAILED`, reason `config_invalid` |
| Non-secret view excludes secrets | same new test file | `non_secret_view()` contains no `auth_token` or `rag_auth_token` key, and `compute_config_fingerprint()` accepts the whole view |
| Fingerprint follows config | same new test file | a changed scalar setting changes the digest, a changed token value does not |
| Deterministic check set | same new test file | the same seven check ids appear for every configuration |
| Existing RAG suite | `uv run pytest tests/mcp_servers/rag_pipeline/` | passes |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-005` for RAG: rag-pipeline-mcp validates its own configuration and returns the common
  posture.
- A server-owned non-secret config view exists and is the only source of the posture fingerprint
  input.
- No token value, path, or URL value appears in any posture field or message.

## Out of scope

- Editing `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (row `46`) or
  `rag_pipeline_service.py`.
- Changing pipeline execution, retrieval quality settings, or `RagPipelineServiceError` behavior.
- Agent-side validation and classification (rows `17`-`18`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `non_secret_view()` | Completed | 20261016-221018 | 20261016-221018 | required by row `03` fingerprint input state-only view: URLs, paths, prompt templates, and both tokens appear as presence booleans because compute_config_fingerprint rejects absolute paths (user decision) |
| 2 | Implement `validate_rag_pipeline_security()` | Completed | 20261016-221018 | 20261016-221018 | check ids are Needs-confirmation (Plan `UNK-03`) lives in the sibling module rag_pipeline_security.py, check ids match the frozen posture contract |
| 3 | Decide single-file vs sibling module (Details) | Completed | 20261016-221018 | 20261016-221018 | sibling module needs a Plan amendment user chose the sibling split, Plan amended by appending row 55 after row 54 so existing row ordinals are unchanged |
| 4 | Add `tests/mcp_servers/rag_pipeline/test_rag_security_validation.py` | Completed | 20261016-221018 | 20261016-221018 | 35 tests in tests/mcp_servers/rag_pipeline/test_rag_security_validation.py |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-221018 | 20261016-221018 | ruff clean, mypy 423 files, lint-imports 6 kept 0 broken, bandit no findings, mock targets clean, docstrings clean for both changed modules, rag suite 119 passed |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-010` (RAG Pipeline self-validation)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`,
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py` (Plan row `55`)