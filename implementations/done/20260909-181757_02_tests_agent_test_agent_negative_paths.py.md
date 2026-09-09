## Goal
Remove the 12 obsolete legacy flat config keys from `tests/agent/test_agent_negative_paths.py`'s `_cfg()` helper so it no longer triggers `ProductionConfigValidator`'s `Unknown config keys` error (REQ-002).

## Scope
In scope: the `_cfg()` helper's `defaults` dict literal in this file only.

## Assumptions
- None of the 12 removed keys is referenced elsewhere in this file (e.g. via an `overrides=` call site or an assertion checking one of their values) — confirm via `rg` before editing.
- This file's `_cfg()` already sets `tool_definitions_strict=True`, `routing_drift_strict=True`, and a non-empty `allowed_tools` — no gap analogous to `test_tool_policy_comprehensive.py`'s UNK-03 exists here (confirmed via direct read).

## Design decisions
- Minimal, additive-safe deletion of the 12 dict entries only.

## Alternatives considered
- Extending `ProductionConfigValidator`'s allowed-keys set to accept these flat keys — rejected (see Plan Implementation intent): these keys have no current consumer anywhere in `scripts/`.

## Implementation
### Target file
`tests/agent/test_agent_negative_paths.py`

### Procedure
1. Locate the `_cfg()` function's `defaults` dict literal.
2. Remove exactly these 12 key/value pairs: `tool_cache_ttl`, `top_k_search`, `top_k_rerank`, `rag_top_k`, `use_mqe`, `use_search`, `use_rrf`, `use_rerank`, `rag_min_score`, `max_chunks_per_doc`, `use_two_stage_fetch`, `two_stage_max_docs`.
3. Leave every other key/value pair unchanged (`allowed_tools`, `tool_definitions_strict`, `routing_drift_strict`, `security_profile`, etc. already correctly set).
4. Run `uv run pytest tests/agent/test_agent_negative_paths.py -q` and confirm zero failures.

### Method
Direct in-place edit of the dict literal.

### Details
- Current values of the 12 keys were confirmed via direct read; none is referenced elsewhere in this file.
- Unlike `tests/agent/test_tool_policy_comprehensive.py`, this file's `_cfg()` already sets the strict-mode keys (`tool_definitions_strict`, `routing_drift_strict`, non-empty `allowed_tools`) correctly, so removing the 12 obsolete keys alone is expected to fully clear this file's 6 currently-failing tests.

## Compatibility considerations
Test-only change; no production code or public contract affected.

## Security considerations
N/A: test fixture only; no security-relevant behavior changes.

## Rollback considerations
Revert the commit; no data migration or external state involved.

## Validation plan
`uv run pytest tests/agent/test_agent_negative_paths.py -q` — expect zero failures.

## Completion criteria
The 12 obsolete keys no longer appear in `_cfg()`'s `defaults` dict, and re-running the file's test suite shows zero failures.

## Out of scope
- Any change to `scripts/shared/production_config_validator.py` or `scripts/agent/config_builders.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the 12 obsolete keys from `_cfg()`'s `defaults` dict | Pending | — | — | |
| 2 | Run `uv run pytest tests/agent/test_agent_negative_paths.py -q` and confirm zero failures | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation update in scope |

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
- **Requirement ID**: `REQ-002` (remove obsolete flat keys); `REQ-003` (verify via full-suite re-run)
- **Source issue**: issues/20260908-162735_cfgval001_unknown-key-validation-breaks-legacy-test-configs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-221312_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-181757
- **Related target files**: tests/agent/test_agent_negative_paths.py
