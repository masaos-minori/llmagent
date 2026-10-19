## Goal

Add prompt-template type validation to `RagConfigValidator.validate` in
`scripts/shared/config_validator.py` so a non-string `mqe_prompt_template` or
`rerank_prompt_template` fails fast with a clear, key-naming error at RAG config-load time,
instead of surfacing as an uncaught `TypeError` deep in the MQE/rerank pipeline. This closes the
documented gap where prompt templates bypass validation entirely.

## Scope

- **In-Scope**:
  - Add a private check for `mqe_prompt_template` and `rerank_prompt_template` to
    `RagConfigValidator.validate`; when either key is missing or its value is not a `str`, append a
    key-naming error and set `ok=False`.
  - Preserve the existing warning/error split (this is an error, not a warning).
  - Add unit + integration tests covering the validator and `resolve_rag_config`.
- **Out-of-Scope**:
  - Stage-handler defense-in-depth guards (`except TypeError`) in the MQE/rerank path.
  - Refactoring MQE/rerank prompt-building logic.
  - Changing default template values or the `{query}` format contract.
  - Validating other RAG config fields.
  - Any `docs/*.md` change.

## Assumptions

- `isinstance(value, str)` is the correct type check; a `bool` is not a valid template (a `bool` is
  not a `str`, so it is rejected).
- Both production entry points that build `RagConfigImpl` go through `RagConfigValidator.validate`
  (`resolve_rag_config` in `scripts/rag/config_resolution.py` and `RagPipelineConfig.load` in
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`), and both raise `ValueError` on
  `ok=False`, so validating there covers all runtime paths.
- The single production construction site of `RagConfigImpl` is `resolve_rag_config`, which
  validates before construction (UNK-01 resolved).
- The input to `validate()` is a flat dict with top-level RAG keys (`_extract_rag_section` returns
  the input unchanged); the new check reads `rag.get("mqe_prompt_template")` /
  `rag.get("rerank_prompt_template")`.

## Design decisions

- Follow the existing `_check_*` static-method convention: a helper returns an error message string
  or `None`, and `validate()` appends it to `errors` when non-`None`. This keeps the new check
  consistent with `_check_use_rrf` and `_check_removed_semantic_cache_keys`.
- Fail fast at the config-validation boundary rather than adding broad `except TypeError` handlers
  to the stage lifecycle — fail-fast at startup is the intended control and matches the typed-config
  policy in `rules/coding.md`.
- The `validate()` signature and `ConfigValidationResult` shape are unchanged; only the `errors`
  list grows. Path A (small task).

## Alternatives considered

- Adding `except TypeError` handlers to `expand_queries` / `cross_encoder_rerank` / the shared
  `_run_stage` wrapper — rejected: out of scope, and it would mask the misconfiguration instead of
  failing fast with an actionable config error.
- Coercing the template type in `RagConfigImpl.__init__` — rejected: `RagConfigImpl` is a plain
  dataclass with no `__init__` coercion (`scripts/rag/models_config.py`), so validation must live in
  the validator, not the DTO.

## Implementation

### Target file

`scripts/shared/config_validator.py`

### Procedure

1. Confirm via grep that no other module constructs `RagConfigImpl` outside the two validated entry
   points (production or test). Record the result. (UNK-01)
2. In `RagConfigValidator.validate`, add a call to a new private check for the two prompt-template
   keys after the removed-semantic-cache-keys check, appending any returned error to `errors`:
   ```python
           template_type_error = self._check_prompt_template_types(rag)
           if template_type_error is not None:
               errors.append(template_type_error)
   ```
3. Implement `_check_prompt_template_types` as a static method following the existing `_check_*`
   convention (returns an error message string or `None`). Per the Plan Gap note above, this
   procedure uses approach (a) — flag present-but-wrong-type only, leaving missing keys alone so
   the existing `{}`-based tests stay green:
   ```python
       @staticmethod
       def _check_prompt_template_types(rag: Mapping[str, Any]) -> str | None:
           """Return an error message when a prompt template is present but not a str."""
           for key in ("mqe_prompt_template", "rerank_prompt_template"):
               if key not in rag:
                   continue
               value = rag[key]
               if not isinstance(value, str):
                   return (
                       f"Configuration key {key!r} must be a string, got "
                       f"{type(value).__name__}"
                   )
           return None
   ```
   If the implementer instead chooses approach (b) (flag missing too), replace the `continue` with
   a missing-key return and update `test_ok_no_errors` / `test_no_rag_key` to supply valid
   templates.
4. Add unit tests in `tests/shared/test_config_validator.py` asserting a non-string template yields
   `ok=False` and a message naming the key (T1).
5. Add an integration test in `tests/rag/test_config_resolution.py` asserting `resolve_rag_config`
   raises on a non-string template and succeeds on string templates (T2).
6. Run `ruff check`, `mypy`, `bandit`, and the affected test targets; confirm clean. (AC-3)

### Method

- **Append to `errors` (REQ-001).** The new check lives in the error branch (not a warning) to match
  the typed-config policy. Because `ConfigValidationResult.ok` is `len(self.errors) == 0`, appending
  any error sets `ok=False`, which both production entry points translate into a `ValueError` before
  any pipeline run.
- **Key-naming message.** The message names the offending key (`mqe_prompt_template` or
  `rerank_prompt_template`) so the failure is actionable. Missing key and wrong-type are reported
  distinctly (missing → "required and must be a string"; wrong type → "must be a string, got <type>").
- **Preserve behavior for valid configs (AC-2).** String templates pass the check unchanged; the
  `{query}`/`{n_queries}` format contract and default template values are untouched.
- **Cover both keys.** The loop iterates both template keys so either one can trigger the error.

### Details

- `REQ-001`: `RagConfigValidator.validate` rejects a non-string `mqe_prompt_template` or
  `rerank_prompt_template` by appending a key-naming error and setting `ok=False`.
- `REQ-002`: `resolve_rag_config` raises `ValueError` naming the key when a template is non-string,
  before any pipeline run, and resolves normally when templates are valid strings.
- **UNK-01:** the single production construction site of `RagConfigImpl` is `resolve_rag_config`,
  which validates before construction; both it and `RagPipelineConfig.load` validate via
  `RagConfigValidator`. Not blocking.

> **Plan Gap (scope decision for the Plan, not applied here):** the Implementation steps word the
> check as "when either key is **missing** or its value is not a `str`". Flagging *missing* keys
> conflicts with two existing unit tests — `test_ok_no_errors` and `test_no_rag_key` — which call
> `validate({})` and assert `ok is True`. Two resolutions, pick one at implementation time:
> - **(a) Non-string only.** Check only present-but-wrong-type values (`isinstance(value, str)`);
>   leave missing keys alone. This matches REQ-001's exact wording ("rejects a non-string"), keeps
>   the existing `{}`-based tests green, and is sufficient because `resolve_rag_config` fills both
>   defaults before validating, so missing never occurs in production.
> - **(b) Missing + non-string.** Flag both; then `test_ok_no_errors` and `test_no_rag_key` must be
>   updated to supply valid `mqe_prompt_template`/`rerank_prompt_template` strings so they still
>   model a valid config.
> This procedure implements REQ-001 as written (non-string rejection) and recommends (a); if the
> implementer chooses (b), update those two tests accordingly.

## Compatibility considerations

Behavior-preserving for valid configs; only genuinely invalid (non-string) templates now fail fast.
No change to the `validate()` signature or `ConfigValidationResult` shape. No `docs/*.md` change.

## Security considerations

N/A: config validation only; no security-relevant behavior change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/shared/config_validator.py` | Unit: non-string template rejected, key named, `ok=False`; valid strings pass | `uv run pytest tests/shared/test_config_validator.py` | New and existing tests pass; zero errors on real config |
| `tests/rag/test_config_resolution.py` | Integration: `resolve_rag_config` raises on bad template, succeeds on good | `uv run pytest tests/rag/test_config_resolution.py` | Raises `ValueError` naming the key; resolves normally otherwise |
| Whole affected area | Static checks | `uv run ruff check`, `uv run mypy`, `uv run bandit` | Clean |

## Completion criteria

- `RagConfigValidator.validate` rejects a non-string `mqe_prompt_template` or `rerank_prompt_template`
  with a key-naming error and `ok=False` (AC-1).
- `resolve_rag_config` raises on a non-string template and succeeds on string templates (AC-2).
- No runtime path allows a non-string template to reach the pipeline stages as an uncaught `TypeError`
  (AC-3).

## Out of scope

Stage-handler defense-in-depth guards in the MQE/rerank path, refactoring MQE/rerank
prompt-building logic, changing default template values or the `{query}` format contract, validating
other RAG config fields, and any `docs/*.md` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Add prompt-template type validation to `RagConfigValidator.validate` | Completed | — | — | REQ-001; AC-1, AC-3 |
| 2 | Phase 2: Add unit + integration tests | Completed | — | — | REQ-001/002; T1/T2 |
| 3 | Phase 3: Run ruff / mypy / bandit / affected tests | Completed | — | — | all REQs |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: issues/20261018-193310_rag001_rag-prompt-templates-are-not-type-validated-at-config-load-so-the-pipeline-crashes-with-typeerror.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261018-220244_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-073608
- **Related target files**: scripts/shared/config_validator.py