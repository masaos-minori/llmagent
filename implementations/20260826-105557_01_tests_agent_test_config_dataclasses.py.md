## Goal

Establish, before any refactoring touches `scripts/agent/services/config_validators.py`,
a full-message-string characterization test for each of the 23 `validate_*` functions
the plan targets for consolidation (REQ-002, REQ-003, REQ-004), so that a post-refactor
diff can prove the error message text is byte-for-byte unchanged (AC-03).

## Scope

- REQ-002/REQ-003/REQ-004 (purpose: guarantee pre-existing test coverage of the exact
  error message string for every function about to be rewritten as a one-line
  delegation, per `plans/20260825-142749_plan.md` Tests section).
- In scope: `tests/agent/test_config_dataclasses.py` only — add or strengthen tests so
  every one of the 23 target functions has a test asserting the *complete* error
  message string, not just a substring.
- Out of scope: the 4 non-consolidated validators (`validate_llm_budget_warn_ratio`,
  `validate_llm_temperature`, `validate_approval_risk_rules`, `validate_tool_safety_tiers`)
  — their existing tests are untouched.

## Assumptions

- N/A: none. Investigation below is based on reading the actual current test file and
  the actual current validator bodies, not on the plan's description of either.

## Design decisions

- Investigation of the current file (`tests/agent/test_config_dataclasses.py`, 269
  lines) shows three states among the 23 target functions, contradicting the plan's own
  Phase 1 framing ("functions with no existing message-verifying test") — the real
  split is finer-grained:
  - **3 functions already have a full-message assertion** (`match=` covers the whole
    string, e.g. `match="memory_fts_limit must be >= 1"`): `memory_fts_limit`,
    `memory_rrf_k`, `memory_recency_days`. No action needed for these.
  - **12 functions have a test, but it only asserts the field name appears in the
    message** (`match="<field_name>"` alone, e.g. `test_llm_max_retries_negative_raises`
    uses `match="llm_max_retries"`), not the full `"<name> must be >= N, got <value>"`
    text: `llm_max_retries`, `llm_retry_base_delay`, `llm_max_tokens`,
    `sse_malformed_retry`, `sse_reconnect_max`, `refiner_max_tokens`, `refiner_timeout`,
    `refiner_max_chars_per_chunk`, `tool_dedup_max_repeats`, `tool_cycle_detect_window`,
    `tool_error_max_consecutive`, `tool_cache_max_size`. A partial-name match would not
    catch a change in the numeric threshold, the comparison wording, or trailing
    punctuation — insufficient for AC-03's "completely matches" requirement.
  - **8 functions have no test at all** referencing them in this file:
    `llm_context_char_limit`, `sse_heartbeat_timeout`, `tool_error_retry_max`,
    `progress_stagnation_window`, `memory_max_inject_semantic`,
    `memory_max_inject_episodic`, `memory_embed_timeout_sec`, `memory_retention_days`.
  - 3 + 12 + 8 = 23, matching the plan's function count exactly.
- Given AC-03 explicitly requires exact message-string equivalence pre/post-refactor,
  this document strengthens all 20 functions in the second and third buckets (not only
  the 8 with zero coverage) — the plan's Phase 1 wording ("洗い出す"/"identify") is
  read as in service of AC-03, not as a narrower literal "zero tests only" scope. This
  is a derived clarification of the plan's own acceptance criterion, not a correction
  to a factual claim, so it is applied here without editing the plan text.
- Reuse the existing per-`Config`-class test class grouping (`TestLLMConfigValidation`,
  `TestRAGConfigValidation`, `TestToolConfigValidation`, `TestMemoryConfigValidation`)
  already present in the file, rather than introducing a new test module — keeps the
  characterization tests co-located with the config classes they construct.
- For the 12 partial-match cases, add the full-string assertion as a **new** test
  method alongside the existing one (do not delete/modify the existing test) — the
  existing test already exercises the "raises" behavior; the new one exercises exact
  message text. This keeps the diff additive and low-risk.

## Alternatives considered

- Strengthen the 12 existing partial-match tests in place (change their `match=` to the
  full string) instead of adding new tests. Rejected: touches lines already covered by
  a passing test for a reason unrelated to this plan's goal, increasing diff size for no
  functional benefit — additive is safer and easier to review.
- Create a new `tests/agent/test_config_validators.py` targeting the module directly
  (bypassing `Config` dataclass construction). Rejected: no such file exists today, and
  the existing suite's convention is to test validators indirectly through the
  dataclass constructors they are wired into (`__post_init__`) — introducing a second,
  parallel test style for the same functions would fragment coverage rather than close
  the gap.

## Implementation
### Target file
`tests/agent/test_config_dataclasses.py`

### Procedure
1. For each of the 8 zero-coverage functions, add one new test method to the
   appropriate existing `Test*ConfigValidation` class, constructing the config with the
   boundary-violating value and asserting the exact current message string from
   `scripts/agent/services/config_validators.py`.
2. For each of the 12 partial-match functions, add one new test method (next to the
   existing partial-match test) asserting the exact current message string.
3. Leave the 3 already-fully-covered functions and the 4 out-of-scope functions
   untouched.

### Method
Use `pytest.raises(ValueError, match=re.escape(expected_message))` (requires `import re`
at the top of the file, currently absent) rather than `==` comparison against
`exc_info.value.args[0]`, to stay consistent with the file's existing
`pytest.raises(..., match=...)` idiom — `re.escape` is needed because several messages
contain regex metacharacters (`.`, `[`, `]`, parentheses do not appear in the 23 target
messages, but `.` does, e.g. "got 0.0").

### Details

Exact current messages to assert (read from
`scripts/agent/services/config_validators.py`, lines as cited):

- `llm_context_char_limit` (line 27-32, class `TestLLMConfigValidation`):
  boundary `LLMConfig(context_char_limit=-1)` →
  `"context_char_limit must be >= 0, got -1"`
- `llm_max_retries` (line 43-46): `LLMConfig(llm_max_retries=-1)` →
  `"llm_max_retries must be >= 0, got -1"`
- `llm_retry_base_delay` (line 49-54): `LLMConfig(llm_retry_base_delay=0.0)` →
  `"llm_retry_base_delay must be > 0, got 0.0"`
- `llm_max_tokens` (line 65-68): `LLMConfig(llm_max_tokens=0)` →
  `"llm_max_tokens must be >= 1, got 0"`
- `sse_heartbeat_timeout` (line 71-76): `LLMConfig(sse_heartbeat_timeout=-1)` →
  `"sse_heartbeat_timeout must be >= 0, got -1"`
- `sse_malformed_retry` (line 79-84): `LLMConfig(sse_malformed_retry=-1)` →
  `"sse_malformed_retry must be >= 0, got -1"`
- `sse_reconnect_max` (line 87-90): `LLMConfig(sse_reconnect_max=-1)` →
  `"sse_reconnect_max must be >= 0, got -1"`
- `refiner_max_tokens` (line 93-98, class `TestRAGConfigValidation`):
  `RAGConfig(refiner_max_tokens=0)` → `"refiner_max_tokens must be >= 1, got 0"`
- `refiner_timeout` (line 101-104): `RAGConfig(refiner_timeout=0.0)` →
  `"refiner_timeout must be > 0, got 0.0"`
- `refiner_max_chars_per_chunk` (line 107-112): `RAGConfig(refiner_max_chars_per_chunk=0)`
  → `"refiner_max_chars_per_chunk must be >= 1, got 0"`
- `tool_dedup_max_repeats` (line 115-120, class `TestToolConfigValidation`):
  `ToolConfig(tool_dedup_max_repeats=0)` →
  `"tool_dedup_max_repeats must be >= 1, got 0"`
- `tool_cycle_detect_window` (line 123-128): `ToolConfig(tool_cycle_detect_window=-1)` →
  `"tool_cycle_detect_window must be >= 0, got -1"`
- `tool_error_max_consecutive` (line 131-136):
  `ToolConfig(tool_error_max_consecutive=-1)` →
  `"tool_error_max_consecutive must be >= 0, got -1"`
- `tool_cache_max_size` (line 139-144): `ToolConfig(tool_cache_max_size=-1)` →
  `"tool_cache_max_size must be >= 0, got -1"` — **note**: this validator is separately
  scheduled for deletion by `plans/20260825-142646_plan.md` once its own prerequisite
  (removal of `ToolExecutor`'s TTL cache) lands; that plan is currently `Blocked` and out
  of scope here. Add the test now regardless, since as of today this validator is still
  active and part of the current plan's 23-function consolidation.
- `tool_error_retry_max` (line 147-152): `ToolConfig(tool_error_retry_max=-1)` →
  `"tool_error_retry_max must be >= 0, got -1"`
- `progress_stagnation_window` (line 155-160): `ToolConfig(progress_stagnation_window=-1)`
  → `"progress_stagnation_window must be >= 0, got -1"`
- `memory_max_inject_semantic` (line 183-188, class `TestMemoryConfigValidation`):
  `MemoryConfig(memory_max_inject_semantic=-1)` →
  `"memory_max_inject_semantic must be >= 0, got -1"`
- `memory_max_inject_episodic` (line 191-196): `MemoryConfig(memory_max_inject_episodic=-1)`
  → `"memory_max_inject_episodic must be >= 0, got -1"`
- `memory_embed_timeout_sec` (line 199-204): `MemoryConfig(memory_embed_timeout_sec=0.0)`
  → `"memory_embed_timeout_sec must be > 0, got 0.0"`
- `memory_retention_days` (line 207-212): `MemoryConfig(memory_retention_days=0)` →
  `"memory_retention_days must be >= 1, got 0"`

Add `import re` near the top of `tests/agent/test_config_dataclasses.py` (after the
existing `from __future__ import annotations`, before `import pytest`) to support
`re.escape()` in the new assertions.

## Compatibility considerations

- Purely additive — no existing test method is modified or removed, so no existing
  passing test can start failing because of this document's changes.
- These tests intentionally run against the *pre-refactor* validator bodies; they must
  stay green both before and after the config_validators.py refactor (implementation
  document `20260826-105557_02_scripts_agent_services_config_validators.py.md`) — that
  is the mechanism proving message-string equivalence (AC-03).

## Security considerations

N/A: test-only change, no security-relevant logic touched.

## Rollback considerations

Revert this test file's diff; no production code or config format is affected, so
rollback is a simple git revert of this file.

## Validation plan

- `uv run pytest tests/agent/test_config_dataclasses.py -v` — all tests (existing +
  newly added) pass against the current (pre-refactor) `config_validators.py`.
- `uv run ruff check tests/agent/test_config_dataclasses.py` — no new lint errors
  (in particular no unused `re` import once assertions are added).

## Completion criteria

- All 23 target functions have at least one test in
  `tests/agent/test_config_dataclasses.py` asserting the complete current error message
  string.
- `uv run pytest tests/agent/test_config_dataclasses.py -v` passes.
- No existing test method was altered or removed.

## Out of scope

- Any change to `scripts/agent/services/config_validators.py` itself — that is
  `implementations/20260826-105557_02_scripts_agent_services_config_validators.py.md`,
  which depends on this document landing first (tests must exist before the refactor,
  per the plan's Tests section and Risk mitigation).
- The 4 non-consolidated validators and their existing tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add full-message tests for the 8 zero-coverage functions | Pending | — | — | |
| 2 | Add full-message tests for the 12 partial-match functions | Pending | — | — | |
| 3 | Run `uv run pytest tests/agent/test_config_dataclasses.py -v` | Pending | — | — | |
| 4 | N/A: no documentation update required for this test-only change | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-004 (pre-refactor message-string characterization tests, per the plan's Tests section)
- **Source issue**: `issues/20260825_config_validators_duplicate_range_checks_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142749_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-105557
- **Related target files**: `tests/agent/test_config_dataclasses.py`
