## Goal

Consolidate duplicate numeric-range validators in `config_validators.py` into three shared helpers. Public function names, signatures, and error messages remain unchanged — this is a pure refactor.

## Scope

**In-Scope**:
- `scripts/agent/services/config_validators.py`: replace 23 of 27 `validate_*` functions with one-line delegations to 3 shared helpers.

**Out-of-Scope**:
- `validate_llm_budget_warn_ratio`, `validate_llm_temperature`, `validate_approval_risk_rules`, `validate_tool_safety_tiers` — field-specific logic, not consolidatable.
- Validation rule/threshold changes.
- Which fields are validated — no change.
- `/reload` validator re-execution (separate issue).

## Assumptions

- All 27 functions were read body-by-body during plan creation; shape classification is complete and accurate.
- Error message strings within each shape are identical across all members of that shape.

## Design decisions

- Three helpers distinguished by operator: `_require_non_negative` (`< 0`), `_require_at_least` (`< minimum`), `_require_positive` (`<= 0`).
- Each original docstring is preserved as-is on the delegation line (as a comment or retained on the public wrapper).
- No change to public API surface.

## Alternatives considered

- Keep all 27 functions as-is: rejected because future rule changes risk being applied inconsistently.
- Two helpers only (as originally proposed in the issue): rejected because Shape 3 uses `<= 0` which differs from Shape 2's `< 1`.

## Implementation

### Target file

`scripts/agent/services/config_validators.py`

### Procedure

#### Phase 1: Preparation

```bash
# Verify: confirm 27 validate_* functions exist
grep -c "^def validate_" scripts/agent/services/config_validators.py
# Expected: 27

# Verify: confirm 4 excluded functions have different logic
grep -A3 "def validate_llm_budget_warn_ratio\|def validate_llm_temperature\|def validate_approval_risk_rules\|def validate_tool_safety_tiers" scripts/agent/services/config_validators.py
# Expected: each has != simple single-bound comparison
```

#### Phase 2: Core Logic

**Step A: Add 3 shared helpers after `LLM_TEMPERATURE_MAX` constant**

Current code (lines 23–24):
```python
# Re-exported constant so validators can reference it without circular import
LLM_TEMPERATURE_MAX = 2.0
```

After change:
```python
# Re-exported constant so validators can reference it without circular import
LLM_TEMPERATURE_MAX = 2.0


def _require_non_negative(name: str, value: float) -> None:
    """Require value >= 0."""
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")


def _require_at_least(name: str, value: float, minimum: float) -> None:
    """Require value >= minimum."""
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")


def _require_positive(name: str, value: float) -> None:
    """Require value > 0."""
    if value <= 0:
        raise ValueError(f"{name} must be > 0, got {value}")
```

**Step B: Replace Shape 1 functions (12 functions — require >= 0)**

For each of these 12 functions, replace the entire body with a single delegation:

```python
def validate_llm_context_char_limit(cfg: LLMConfig) -> None:
    """Validate that context_char_limit is non-negative."""
    _require_non_negative("context_char_limit", cfg.context_char_limit)
```

Apply the same pattern to all 12:
- `validate_llm_context_char_limit` → `_require_non_negative("context_char_limit", cfg.context_char_limit)`
- `validate_llm_max_retries` → `_require_non_negative("llm_max_retries", cfg.llm_max_retries)`
- `validate_llm_sse_heartbeat_timeout` → `_require_non_negative("sse_heartbeat_timeout", cfg.sse_heartbeat_timeout)`
- `validate_llm_sse_malformed_retry` → `_require_non_negative("sse_malformed_retry", cfg.sse_malformed_retry)`
- `validate_llm_sse_reconnect_max` → `_require_non_negative("sse_reconnect_max", cfg.sse_reconnect_max)`
- `validate_tool_cycle_detect_window` → `_require_non_negative("tool_cycle_detect_window", cfg.tool_cycle_detect_window)`
- `validate_tool_error_max_consecutive` → `_require_non_negative("tool_error_max_consecutive", cfg.tool_error_max_consecutive)`
- `validate_tool_cache_max_size` → `_require_non_negative("tool_cache_max_size", cfg.tool_cache_max_size)`
- `validate_tool_error_retry_max` → `_require_non_negative("tool_error_retry_max", cfg.tool_error_retry_max)`
- `validate_progress_stagnation_window` → `_require_non_negative("progress_stagnation_window", cfg.progress_stagnation_window)`
- `validate_memory_max_inject_semantic` → `_require_non_negative("memory_max_inject_semantic", cfg.memory_max_inject_semantic)`
- `validate_memory_max_inject_episodic` → `_require_non_negative("memory_max_inject_episodic", cfg.memory_max_inject_episodic)`

**Step C: Replace Shape 2 functions (7 functions — require >= 1)**

```python
def validate_llm_max_tokens(cfg: LLMConfig) -> None:
    """Validate that llm_max_tokens is at least 1."""
    _require_at_least("llm_max_tokens", cfg.llm_max_tokens, 1)
```

Apply the same pattern to all 7:
- `validate_llm_max_tokens` → `_require_at_least("llm_max_tokens", cfg.llm_max_tokens, 1)`
- `validate_rag_refiner_max_tokens` → `_require_at_least("refiner_max_tokens", cfg.refiner_max_tokens, 1)`
- `validate_rag_refiner_max_chars_per_chunk` → `_require_at_least("refiner_max_chars_per_chunk", cfg.refiner_max_chars_per_chunk, 1)`
- `validate_tool_dedup_max_repeats` → `_require_at_least("tool_dedup_max_repeats", cfg.tool_dedup_max_repeats, 1)`
- `validate_memory_fts_limit` → `_require_at_least("memory_fts_limit", cfg.memory_fts_limit, 1)`
- `validate_memory_rrf_k` → `_require_at_least("memory_rrf_k", cfg.memory_rrf_k, 1)`
- `validate_memory_retention_days` → `_require_at_least("memory_retention_days", cfg.memory_retention_days, 1)`

**Step D: Replace Shape 3 functions (4 functions — require > 0)**

```python
def validate_llm_retry_base_delay(cfg: LLMConfig) -> None:
    """Validate that llm_retry_base_delay is positive."""
    _require_positive("llm_retry_base_delay", cfg.llm_retry_base_delay)
```

Apply the same pattern to all 4:
- `validate_llm_retry_base_delay` → `_require_positive("llm_retry_base_delay", cfg.llm_retry_base_delay)`
- `validate_rag_refiner_timeout` → `_require_positive("refiner_timeout", cfg.refiner_timeout)`
- `validate_memory_recency_days` → `_require_positive("memory_recency_days", cfg.memory_recency_days)`
- `validate_memory_embed_timeout_sec` → `_require_positive("memory_embed_timeout_sec", cfg.memory_embed_timeout_sec)`

**Step E: Leave 4 functions unchanged**

Do NOT modify:
- `validate_llm_budget_warn_ratio` (range `(0.0, 1.0]` check)
- `validate_llm_temperature` (range `[0.0, LLM_TEMPERATURE_MAX]` check)
- `validate_approval_risk_rules` (dict value set validation)
- `validate_tool_safety_tiers` (dict value set validation)

#### Phase 3: Deployment & Verification

**Step 1: Verify message string equality for all 23 replaced functions**

```bash
# For each replaced function, verify the error message would be identical.
# Example for Shape 1:
python -c "
from agent.services.config_validators import validate_llm_context_char_limit
try:
    class FakeCfg:
        context_char_limit = -1
    validate_llm_context_char_limit(FakeCfg())
except ValueError as e:
    assert str(e) == 'context_char_limit must be >= 0, got -1', f'Got: {e}'
    print('OK')
"
```

Repeat for all 23 functions, testing boundary values (-1, 0, etc.) per shape.

**Step 2: Verify public API unchanged**

```bash
python -c "from agent.services import config_validators; print('OK')"
```

**Step 3: Run full test suite**

```bash
uv run pytest tests/agent/ -k "config_validators or config_dataclasses" -v
uv run pytest
```

**Step 4: Type check**

```bash
uv run mypy scripts/
```

**Step 5: Confirm net line reduction**

```bash
wc -l scripts/agent/services/config_validators.py
# Expected: fewer lines than before (23 functions reduced from ~6 lines each to ~3 lines each = ~92 lines saved)
```

### Details

- **REQ-001**: Add 3 helpers (`_require_non_negative`, `_require_at_least`, `_require_positive`) with exact signatures and messages matching each shape.
- **REQ-002**: Replace 12 Shape 1 functions with `_require_non_negative("X", cfg.X)`.
- **REQ-003**: Replace 7 Shape 2 functions with `_require_at_least("X", cfg.X, 1)`.
- **REQ-004**: Replace 4 Shape 3 functions with `_require_positive("X", cfg.X)`.
- **REQ-005**: Do not modify the 4 excluded functions.

### Verification checklist

Before committing:

- [ ] All 23 replaced functions produce identical error messages at boundary values.
- [ ] Public API (`from agent.services import config_validators`) imports successfully.
- [ ] All existing tests pass.
- [ ] No new type errors from `mypy`.
- [ ] Net line count decreased.

## Compatibility considerations

- No API changes — public function names, signatures, and error messages are preserved exactly.
- No config schema changes required.
- `config_dataclasses.py` import path unchanged.

## Security considerations

- None — pure refactor, no behavioral change.

## Rollback considerations

- Revert: restore original file.
- Git ref-safe rollback: `git checkout HEAD -- scripts/agent/services/config_validators.py`.
- No database migration or config file changes.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_validators.py` | Unit | `uv run pytest tests/agent/ -k "config_validators or config_dataclasses" -v` | All message strings match originals |
| Repository | Full suite | `uv run pytest` | No new failures |
| Repository | Type check | `uv run mypy scripts/` | No new errors |

## Completion criteria

- [ ] 3 shared helpers added with correct signatures and messages.
- [ ] 12 Shape 1 functions replaced with `_require_non_negative` delegations.
- [ ] 7 Shape 2 functions replaced with `_require_at_least` delegations.
- [ ] 4 Shape 3 functions replaced with `_require_positive` delegations.
- [ ] 4 excluded functions left unchanged.
- [ ] All 23 replaced functions produce identical error messages at boundary values.
- [ ] Public API imports successfully.
- [ ] All tests pass.
- [ ] No new type errors.
- [ ] Net line count decreased.

## Out of scope

- Changes to `validate_*` function contents (other than consolidation).
- Applying validation re-execution to `ApprovalConfig`, `MemoryConfig`, `MCPConfig` etc.
- Adding new validation rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Preparation | Pending | — | — | Awaiting implementation |
| 2 | Core Logic Implementation | Pending | — | — | Awaiting implementation |
| 3 | Deployment & Verification | Pending | — | — | Awaiting implementation |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: issues/20260825_config_validators_duplicate_range_checks_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-142749_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-08-25 22:43:56
- **Related target files**: scripts/agent/services/config_validators.py
