## Goal

Consolidate the 23 duplicated numeric-range `validate_*` functions in
`scripts/agent/services/config_validators.py` into calls to three new shared helpers,
with zero change to public function names, signatures, or raised error message text
(REQ-001, REQ-002, REQ-003, REQ-004).

## Scope

- REQ-001 (purpose: add the 3 shared helpers `_require_non_negative`,
  `_require_at_least`, `_require_positive`).
- REQ-002 (purpose: rewrite the 12 "non-negative" functions as one-line delegations to
  `_require_non_negative`).
- REQ-003 (purpose: rewrite the 7 ">= 1" functions as one-line delegations to
  `_require_at_least`).
- REQ-004 (purpose: rewrite the 4 "> 0" functions as one-line delegations to
  `_require_positive`).
- REQ-005 (purpose: confirm the 4 field-specific validators are left untouched — no
  code change, verification only).
- Out of scope: `validate_llm_budget_warn_ratio`, `validate_llm_temperature`,
  `validate_approval_risk_rules`, `validate_tool_safety_tiers` (REQ-005); the `/reload`
  path re-execution of validators (tracked separately by
  `plans/20260825-142225_plan.md`); any change to `config_dataclasses.py` call sites
  (they call the same public function names with the same signatures, so nothing there
  changes).

## Assumptions

- N/A: none beyond what is verified below. Every function body, message string, and
  the 27/23/4 split was re-read directly from
  `scripts/agent/services/config_validators.py` (236 lines) rather than taken from the
  plan's prose — see Design decisions.

## Design decisions

- Verified against current source (not the plan's description) that all 27
  `validate_*` functions and their classification hold exactly as the plan states:
  - **12 "non-negative" (`< 0`) functions** — confirmed identical shape at lines 27-32,
    43-46, 71-76, 79-84, 87-90, 123-128, 131-136, 139-144, 147-152, 155-160, 183-188,
    191-196: `validate_llm_context_char_limit`, `validate_llm_max_retries`,
    `validate_llm_sse_heartbeat_timeout`, `validate_llm_sse_malformed_retry`,
    `validate_llm_sse_reconnect_max`, `validate_tool_cycle_detect_window`,
    `validate_tool_error_max_consecutive`, `validate_tool_cache_max_size`,
    `validate_tool_error_retry_max`, `validate_progress_stagnation_window`,
    `validate_memory_max_inject_semantic`, `validate_memory_max_inject_episodic`.
  - **7 "at least 1" (`< 1`) functions** — confirmed at lines 65-68, 93-98, 107-112,
    115-120, 163-166, 169-172, 207-212: `validate_llm_max_tokens`,
    `validate_rag_refiner_max_tokens`, `validate_rag_refiner_max_chars_per_chunk`,
    `validate_tool_dedup_max_repeats`, `validate_memory_fts_limit`,
    `validate_memory_rrf_k`, `validate_memory_retention_days`.
  - **4 "positive" (`<= 0`) functions** — confirmed at lines 49-54, 101-104, 175-180,
    199-204: `validate_llm_retry_base_delay`, `validate_rag_refiner_timeout`,
    `validate_memory_recency_days`, `validate_memory_embed_timeout_sec`.
  - **4 excluded functions** — confirmed field-specific at lines 35-40 (two-sided range
    check `0.0 < x <= 1.0`), 57-62 (two-sided range check against a module constant),
    215-222 and 225-235 (dict-value-set validation): `validate_llm_budget_warn_ratio`,
    `validate_llm_temperature`, `validate_approval_risk_rules`,
    `validate_tool_safety_tiers`.
  - Every one of the 23 in-scope functions' `f"..."` message uses exactly the bare
    field name (not `cfg.<field>`) followed by `must be >= 0, got {cfg.<field>}` /
    `must be >= 1, got {cfg.<field>}` / `must be > 0, got {cfg.<field>}` — so calling
    the new helper with `name="<field_name>"` reproduces the exact current string.
- **Cross-plan note — do not silently fold in `validate_tool_cache_max_size` without
  comment**: `plans/20260825-142646_plan.md` (currently `Blocked` on an unmet
  prerequisite — removal of `ToolExecutor`'s TTL cache, tracked by a not-yet-created
  plan) targets this exact function, `validate_tool_cache_max_size`, for deletion once
  that prerequisite lands. This plan's own Design section does not special-case it — it
  is included as one more instance of the "non-negative" shape alongside the other 11.
  Per that treatment, this document folds it into the `_require_non_negative`
  consolidation along with the other 11, but flags explicitly: **whichever of these two
  plans lands second must re-verify that the other did not already remove or move this
  function** before editing it — if `142646` lands first (deleting
  `validate_tool_cache_max_size` and its `config_dataclasses.py` wiring), this
  document's step for that one function is a no-op / skip, not a conflict, since the
  other 11 lines are independent.
- The three helpers are added once, near the top of the file (after the
  `LLM_TEMPERATURE_MAX` constant, before the first `validate_*` function), matching the
  plan's Requirements code block verbatim.
- Each rewritten function keeps its original docstring (per the plan's Design section)
  and its original one-line-per-field signature; only the body becomes a single
  delegation call.

## Alternatives considered

- Collapsing all three shapes into a single parameterized helper (e.g.
  `_require(name, value, minimum, inclusive)`) was considered but rejected by the plan
  itself (see plan's Problem section) — `_require_positive`'s `<=` comparison is not
  expressible as a minimum-with-inclusive-flag without adding a second boolean
  parameter, which the plan's author judged less readable than three named, single-
  purpose helpers with names that read naturally at each call site
  (`_require_non_negative(...)`, `_require_at_least(..., 1)`, `_require_positive(...)`).
  This document preserves that decision rather than re-opening it, since it is not
  contradicted by anything found in current source.
- Deleting the original docstrings (since the one-line body no longer needs a "why"
  explanation as much) was considered and rejected — the plan explicitly requires
  keeping them as behavior documentation for each field, and removing them would be an
  unrelated formatting change outside this plan's scope.

## Implementation
### Target file
`scripts/agent/services/config_validators.py`

### Procedure
1. Insert the three helper functions from the plan's `REQ-001` code block after the
   `LLM_TEMPERATURE_MAX = 2.0` line (line 24) and before
   `def validate_llm_context_char_limit` (line 27).
2. Rewrite each of the 12 "non-negative" functions' bodies to
   `_require_non_negative("<field>", cfg.<field>)`, keeping the existing docstring and
   signature.
3. Rewrite each of the 7 "at least 1" functions' bodies to
   `_require_at_least("<field>", cfg.<field>, 1)`.
4. Rewrite each of the 4 "positive" functions' bodies to
   `_require_positive("<field>", cfg.<field>)`.
5. Leave the 4 excluded functions (lines 35-40, 57-62, 215-222, 225-235) byte-for-byte
   unchanged.
6. Confirm no other file needs a change: `config_dataclasses.py`'s 23 import statements
   and 23 call sites (`_v_llm_ccl(self)`, etc., lines 141-149, 167-169, 232-237,
   270-276) reference these functions by their unchanged public names and unchanged
   `(cfg) -> None` signature, so nothing there needs editing.

### Method
Direct in-place body replacement per function — for each target function, replace the
`if cfg.<field> <op> <threshold>: raise ValueError(...)` block with a single call to the
matching helper. Do not touch the `def ...(cfg: <Type>) -> None:` line or the docstring
line above it.

### Details

**1. New helpers (insert after line 24):**
```python
def _require_non_negative(name: str, value: float) -> None:
    """Raise ValueError if value is negative."""
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")


def _require_at_least(name: str, value: float, minimum: float) -> None:
    """Raise ValueError if value is below minimum."""
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")


def _require_positive(name: str, value: float) -> None:
    """Raise ValueError if value is not strictly positive."""
    if value <= 0:
        raise ValueError(f"{name} must be > 0, got {value}")
```
(Docstrings are not specified in the plan's `REQ-001` code block; adding a one-line
docstring to each is consistent with `rules/coding.md`'s general style and does not
change behavior — flagged here so the implementer can drop them if a reviewer prefers
the plan's exact snippet verbatim instead.)

**2. Shape-1 rewrite (12 functions), e.g.:**
```python
def validate_llm_context_char_limit(cfg: LLMConfig) -> None:
    """Validate that context_char_limit is non-negative."""
    _require_non_negative("context_char_limit", cfg.context_char_limit)
```
Apply the same pattern (field name substituted) to: `llm_max_retries`,
`sse_heartbeat_timeout`, `sse_malformed_retry`, `sse_reconnect_max`,
`tool_cycle_detect_window`, `tool_error_max_consecutive`, `tool_cache_max_size` (see
cross-plan note above), `tool_error_retry_max`, `progress_stagnation_window`,
`memory_max_inject_semantic`, `memory_max_inject_episodic`.

**3. Shape-2 rewrite (7 functions), e.g.:**
```python
def validate_llm_max_tokens(cfg: LLMConfig) -> None:
    """Validate that llm_max_tokens is at least 1."""
    _require_at_least("llm_max_tokens", cfg.llm_max_tokens, 1)
```
Apply the same pattern to: `refiner_max_tokens`, `refiner_max_chars_per_chunk`,
`tool_dedup_max_repeats`, `memory_fts_limit`, `memory_rrf_k`, `memory_retention_days`.

**4. Shape-3 rewrite (4 functions), e.g.:**
```python
def validate_llm_retry_base_delay(cfg: LLMConfig) -> None:
    """Validate that llm_retry_base_delay is positive."""
    _require_positive("llm_retry_base_delay", cfg.llm_retry_base_delay)
```
Apply the same pattern to: `refiner_timeout`, `memory_recency_days`,
`memory_embed_timeout_sec`.

**5.** `validate_llm_budget_warn_ratio`, `validate_llm_temperature`,
`validate_approval_risk_rules`, `validate_tool_safety_tiers` — no change.

## Compatibility considerations

- Public API is unchanged: all 27 function names, all signatures (`(cfg: <Type>) ->
  None`), and all raised `ValueError` message strings stay identical — verified this
  document's `implementations/20260826-105557_01_..._test_config_dataclasses.py.md`
  characterization tests must remain green unmodified against the post-refactor code.
- `config_dataclasses.py`'s import-alias block (lines 27-105) and its 7
  `__post_init__` call blocks (lines 141-149 `LLMConfig`, 167-169 `RAGConfig`, 232-237
  `ToolConfig`, 270-276 `MemoryConfig`, 387 `ApprovalConfig`) require zero edits.
- `AC-02` (`python -c "from agent.services import config_validators"` succeeds) is
  satisfied trivially since no import or `TYPE_CHECKING` structure changes.

## Security considerations

N/A: pure internal refactor of numeric-comparison validation logic; no user input
handling, no new external dependency, no change to what values are accepted or
rejected.

## Rollback considerations

Single-file, purely mechanical change (body-only rewrites plus 3 new private helper
functions) — revert `scripts/agent/services/config_validators.py` via git if any
post-refactor validation step (message-string diff, `uv run pytest`, `uv run mypy`)
fails. No data migration, no config format change, no `deploy.sh` impact (file is
neither added, removed, nor moved).

## Validation plan

- `uv run pytest tests/agent/test_config_dataclasses.py -v` — all tests (including the
  ones added by
  `implementations/20260826-105557_01_tests_agent_test_config_dataclasses.py.md`) pass
  with identical message strings, both before this refactor lands (baseline) and after
  (regression check) — this is the mechanism satisfying AC-03.
- `python -c "from agent.services import config_validators"` succeeds (AC-02).
- `git diff scripts/agent/services/config_validators.py` — manually diff each rewritten
  function's message-producing branch against its pre-refactor form to catch any
  transcription error before running tests (per the plan's Risk mitigation).
- `wc -l scripts/agent/services/config_validators.py` before/after — confirm net line
  count decreased (AC-04).
- `uv run pytest` (full suite) — no new failures.
- `uv run mypy scripts/` — no new errors introduced by the new helpers' type
  annotations (`float` parameters accept the `int`-typed config fields passed to them
  without a cast, matching existing usage of `int < float`-shaped comparisons already
  present in the pre-refactor bodies).
- `PYTHONPATH=scripts uv run lint-imports` — no architecture-boundary change expected
  (no new imports added).

## Completion criteria

- The 3 helpers exist with the exact behavior specified in REQ-001.
- All 23 in-scope functions delegate to the matching helper in one line each, with
  their original docstring and signature intact.
- The 4 out-of-scope functions are byte-for-byte unchanged.
- `tests/agent/test_config_dataclasses.py` passes in full, including the new
  full-message-string assertions from
  `implementations/20260826-105557_01_tests_agent_test_config_dataclasses.py.md`.
- `uv run pytest`, `uv run mypy scripts/`, and `PYTHONPATH=scripts uv run lint-imports`
  all pass with no new failures/errors relative to `master`.
- Net line count of `scripts/agent/services/config_validators.py` decreased.

## Out of scope

- `implementations/20260826-105557_01_tests_agent_test_config_dataclasses.py.md` (must
  land first — this document's Validation plan depends on those characterization tests
  already existing).
- `plans/20260825-142646_plan.md`'s eventual deletion of `validate_tool_cache_max_size`
  — not this document's concern; see the cross-plan note in Design decisions.
- `plans/20260825-142225_plan.md`'s `/reload`-path validator re-execution — unrelated
  and independently progressing per the plan's own Out-of-Scope section.
- `deploy/deploy.sh` — no update needed (no file added/removed/moved).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the 3 shared helpers (REQ-001) | Pending | — | — | |
| 2 | Rewrite 12 non-negative functions (REQ-002) | Pending | — | — | Includes `validate_tool_cache_max_size` — see cross-plan note |
| 3 | Rewrite 7 at-least-1 functions (REQ-003) | Pending | — | — | |
| 4 | Rewrite 4 positive functions (REQ-004) | Pending | — | — | |
| 5 | Confirm 4 excluded functions unchanged (REQ-005) | Pending | — | — | |
| 6 | Run validation sequence (`rules/toolchain.md`) and message-string diff | Pending | — | — | |
| 7 | Confirm no `deploy.sh` update needed | Pending | — | — | |

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
- **Source issue**: `issues/20260825_config_validators_duplicate_range_checks_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142749_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-105557
- **Related target files**: `scripts/agent/services/config_validators.py`
