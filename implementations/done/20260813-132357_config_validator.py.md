# Implementation Procedure: Remove Obsolete Dimension Validation from RagConfigValidator

## Goal

Remove the obsolete `embedding_dim` vs `vec_dim` comparison logic from `RagConfigValidator.validate()` in `scripts/shared/config_validator.py`. Dimensions are now hardcoded to 1024 in `store_protocols.py`, making this validation redundant.

## Scope

- **In scope**: Remove lines 35–39 in `scripts/shared/config_validator.py`.
- **Out of scope**: Schema changes, test updates, config file changes.

## Assumptions

- No production config files set both `embedding_dim` and `vec_dim` simultaneously (verified in UNK-01).
- The hardcoded constant `QWEN3_EMBEDDING_DIMS = 1024` in `store_protocols.py` is the single source of truth.
- Existing callers of `RagConfigValidator.validate()` can accept removal of dimension-related errors without breaking.

## Design decisions

- Complete removal rather than converting to a warning: since dimensions are hardcoded, any mismatch between `embedding_dim` and `vec_dim` in config is meaningless — there is no actual dimension value to compare against.

## Alternatives considered

- Convert to a warning-level message: rejected because the keys themselves are obsolete; a warning about their mismatch implies they are still meaningful configuration options.
- Keep as-is with updated error message: rejected because the validation serves no purpose when dimensions are hardcoded.

## Implementation

### Target file

`scripts/shared/config_validator.py`

### Procedure

1. Locate the embedding dimension consistency block (lines 35–39).
2. Remove the comment line, variable assignments, conditional check, and error append.
3. Verify no other references to these variables exist in the file.

### Method

Inline deletion of 5 consecutive lines. No code logic changes elsewhere.

### Details

Current code (lines 35–39):

```python
        # Embedding dimension consistency
        embed_dim = rag.get("embedding_dim")
        vec_dim = rag.get("vec_dim")
        if embed_dim and vec_dim and embed_dim != vec_dim:
            errors.append(f"embedding_dim={embed_dim} != vec_dim={vec_dim}")
```

After removal, lines 34→40 become contiguous:

```python
        rag = (
            cfg["rag"] if "rag" in cfg else cfg
        )  # Normalize: nested {"rag": {...}} (agent.toml) and flat {...} (MCP module_cfg) both supported

        # use_rrf=False warning
        if not rag.get("use_rrf", True):
            warnings.append(
                "use_rrf=false degrades retrieval quality; use only for diagnostics"
            )
```

Key points:
- Blank line after `rag` assignment is preserved.
- No indentation or whitespace changes needed beyond removing the 5 lines.
- Verify `rag.get("embedding_dim")` and `rag.get("vec_dim")` are not referenced elsewhere in the file.

## Compatibility considerations

- `RagConfigValidator.validate()` will no longer produce errors for mismatched `embedding_dim`/`vec_dim` values. This is acceptable since these keys are obsolete.
- Callers that previously checked for dimension-mismatch errors will see fewer errors — this is expected behavior.

## Security considerations

N/A — removing validation does not introduce security surface area. It reduces the attack surface by eliminating a misleading validation path.

## Rollback considerations

- To roll back, restore the 5 removed lines.
- No data loss risk: only validator output changes.

## Validation plan

| Step | Command | Expected Outcome |
|---|---|---|
| 1 | `grep -n "embedding_dim\|vec_dim" scripts/shared/config_validator.py` | No results (all references removed) |
| 2 | `grep -n "Embedding dimension consistency" scripts/shared/config_validator.py` | No results |
| 3 | Run affected tests: `pytest tests/shared/test_config_validator.py -v` | Tests pass without dimension-mismatch assertions |

## Out of scope

- Schema constraint additions (handled separately).
- Test fixture cleanup (handled separately).
- Config file reference removal (handled separately).
- Documentation updates.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260807_06_issue.md
- Source requirement: requires/20260813_094450_require.md
- Source plan: plans/20260813-103307_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-132357
- Related target files: scripts/shared/config_validator.py
