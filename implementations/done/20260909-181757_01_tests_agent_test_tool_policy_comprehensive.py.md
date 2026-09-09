## Goal
Remove the 12 obsolete legacy flat config keys from `tests/agent/test_tool_policy_comprehensive.py`'s `_cfg()` helper so it no longer triggers `ProductionConfigValidator`'s `Unknown config keys` error (REQ-002).

## Scope
In scope: the `_cfg()` helper's `defaults` dict literal in this file only. Out of scope: this file's separate, pre-existing `tool_definitions_strict`/`routing_drift_strict`/`allowed_tools` gap (Plan Unknowns UNK-03) — this file will still show failures after this change, but none citing `Unknown config keys`.

## Assumptions
- None of the 12 removed keys is referenced elsewhere in this file (e.g. via an `overrides=` call site or an assertion checking one of their values) — confirm via `rg` before editing.
- Removing these keys does not change any test's intent; each test targets `agent/tool_policy.py` risk-classification/pre-flight behavior, not RAG or tool-cache settings.

## Design decisions
- Minimal, additive-safe deletion of the 12 dict entries only — not a redesign of `_cfg()`.

## Alternatives considered
- Extending `ProductionConfigValidator`'s allowed-keys set to accept these flat keys — rejected (see Plan Implementation intent): these keys have no current consumer anywhere in `scripts/`, so accepting them would mask dead configuration rather than fix a genuine input-shape mismatch.

## Implementation
### Target file
`tests/agent/test_tool_policy_comprehensive.py`

### Procedure
1. Locate the `_cfg()` function's `defaults` dict literal.
2. Remove exactly these 12 key/value pairs: `tool_cache_ttl`, `top_k_search`, `top_k_rerank`, `rag_top_k`, `use_mqe`, `use_search`, `use_rrf`, `use_rerank`, `rag_min_score`, `max_chunks_per_doc`, `use_two_stage_fetch`, `two_stage_max_docs`.
3. Leave every other key/value pair in `defaults` unchanged.
4. Run `uv run pytest tests/agent/test_tool_policy_comprehensive.py -q` and confirm no remaining failure's traceback cites `Unknown config keys`.

### Method
Direct in-place edit of the dict literal — no helper refactor, no new fixture.

### Details
- Current values of the 12 keys (`300`, `20`, `15`, `5`, `True`, `True`, `True`, `True`, `0.0`, `2`, `False`, `2` respectively) were confirmed via direct read; none is referenced elsewhere in this file.
- After removal, this file's tests will still show failures from a separate, pre-existing cause: this file's `_cfg()` never sets `tool_definitions_strict`, `routing_drift_strict`, or a non-empty `allowed_tools`, each of which independently triggers its own `ProductionConfigValidator` error. This is out of scope for this document (Plan Unknowns UNK-03) — do not add these 3 keys here.

## Compatibility considerations
Test-only change; no production code or public contract affected.

## Security considerations
N/A: test fixture only; no security-relevant behavior changes.

## Rollback considerations
Revert the commit; no data migration or external state involved.

## Validation plan
`uv run pytest tests/agent/test_tool_policy_comprehensive.py -q` — expect zero failures whose traceback cites `Unknown config keys`. Some failures are expected to remain from the separate, out-of-scope UNK-03 cause until that is fixed independently.

## Completion criteria
The 12 obsolete keys no longer appear in `_cfg()`'s `defaults` dict, and re-running the file's test suite shows no failure attributable to `Unknown config keys`.

## Out of scope
- This file's separate `tool_definitions_strict`/`routing_drift_strict`/`allowed_tools` gap (Plan Unknowns UNK-03) — recommended as a candidate for a new, separate issue.
- Any change to `scripts/shared/production_config_validator.py` or `scripts/agent/config_builders.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the 12 obsolete keys from `_cfg()`'s `defaults` dict | Pending | — | — | |
| 2 | Run `uv run pytest tests/agent/test_tool_policy_comprehensive.py -q` and confirm no `Unknown config keys` failure | Pending | — | — | |
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
- **Related target files**: tests/agent/test_tool_policy_comprehensive.py
