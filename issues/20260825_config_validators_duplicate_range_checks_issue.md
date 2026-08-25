# Collapse repetitive numeric range validators into shared helpers

## Priority
Low

## Summary
`scripts/agent/services/config_validators.py` contains many near-identical single-field validators (confirmed at least 20 `validate_*` functions covering `LLMConfig`, `RAGConfig`, `ToolConfig`, `MemoryConfig` fields), most following a small number of repeated shapes ("must be non-negative", "must be >= 1", threshold range checks). This duplication increases maintenance cost and drift risk when the validation pattern needs to change.

## Background
N/A: covered by Summary.

## Problem
Verified: `grep -n "^def validate_" scripts/agent/services/config_validators.py` lists at least 20 top-level validator functions (`validate_llm_context_char_limit`, `validate_llm_budget_warn_ratio`, `validate_llm_max_retries`, `validate_llm_retry_base_delay`, `validate_llm_temperature`, `validate_llm_max_tokens`, `validate_llm_sse_heartbeat_timeout`, `validate_llm_sse_malformed_retry`, `validate_llm_sse_reconnect_max`, `validate_rag_refiner_max_tokens`, `validate_rag_refiner_timeout`, `validate_rag_refiner_max_chars_per_chunk`, `validate_tool_dedup_max_repeats`, `validate_tool_cycle_detect_window`, `validate_tool_error_max_consecutive`, `validate_tool_cache_max_size`, `validate_tool_error_retry_max`, `validate_progress_stagnation_window`, `validate_memory_fts_limit`, `validate_memory_rrf_k`, and others beyond this list). Several share the same one- or two-line body shape (single-field non-negative or minimum-value check) confirmed by their naming pattern; a full body-by-body diff was not performed in this pass and should be done before implementation to confirm the exact duplication shape (see AI Implementation Instruction).

## Reason for Change
Reducing near-identical validators to shared helpers lowers maintenance cost and the risk that a future rule change is applied to some validators but missed in others.

## Implementation Intent
Introduce shared helpers, e.g.:
- `_require_non_negative(name: str, value: float) -> None`
- `_require_at_least(name: str, value: float, minimum: float) -> None`
Rewrite the individual `validate_*` functions to delegate to these helpers, preserving existing message format and every public function name (all are imported by `config_dataclasses.py`).

## Target Files or Areas
- `scripts/agent/services/config_validators.py`

## Required Changes
- Before rewriting, diff the bodies of all `validate_*` functions to confirm which share an identical shape versus which have field-specific logic that must not be collapsed.
- Introduce the shared helper(s).
- Rewrite qualifying validators to delegate to the helper(s), preserving public names, signatures, and error message text exactly.

## Constraints
- Public validator function names and signatures must not change — they are imported directly by `config_dataclasses.py`'s `__post_init__` methods.
- Error messages must remain equivalent (exact wording may be reformatted only if the helper's message format is verified against every existing message first).

## Acceptance Criteria
- [ ] Public validator names/signatures are unchanged (no import breakage in `config_dataclasses.py`).
- [ ] Error messages remain equivalent.
- [ ] Net line count in `config_validators.py` is reduced.

## Testing Expectations
- Existing config validation tests pass unchanged.
- If no dedicated test exists for a given validator's error message text, add one before refactoring it, to guard against accidental message drift.

## Documentation Impact
N/A: internal implementation detail, not part of any documented public behavior.

## Out of Scope
- Changing validation rules or thresholds.
- Changing which fields are validated.

## Dependencies
- Coordinate with `issues/20260825_cfgreload_missing_validator_reexecution_issue.md` if that issue's implementation (making validators reusable from the reload path) lands first or concurrently — that issue calls these same `validate_*` functions and should not be blocked by, or conflict with, this refactor's internal restructuring.

## Unresolved Questions
- N/A: none beyond confirming the exact duplication shape at implementation time (see Required Changes).

## AI Implementation Instruction
Do the full body-by-body diff of all `validate_*` functions before writing the shared helpers — do not assume every function listed here is a trivial duplicate without checking. Preserve public names/signatures/messages exactly; this is a pure refactor with zero intended behavior change.
