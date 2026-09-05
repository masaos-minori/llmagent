## Goal
Remove `use_semantic_cache`/`semantic_cache_max_size`/`semantic_cache_threshold` from
`tests/rag/test_rag_quality_regression.py`'s `_make_rag_cfg()` helper signature and
its `SimpleNamespace` construction, made obsolete by procedure documents `01`/`03`
(`REQ-009`).

## Scope
- **In-Scope**: remove the `use_semantic_cache: bool = True` parameter (line 27) from
  `_make_rag_cfg()`'s signature; remove `semantic_cache_max_size=100,` (line 31) and
  `semantic_cache_threshold=0.85,` (line 32) from its `SimpleNamespace(...)`
  construction; remove `use_semantic_cache=use_semantic_cache,` (line 49) from the
  same construction.
- **Out-of-Scope**: every other parameter/field in `_make_rag_cfg()` (`use_rrf`,
  `use_rerank`, `use_mqe`, `use_refiner`, `use_search`, etc.) — confirmed unrelated by
  reading the full function; every test in `class TestRagQualityRegression` —
  confirmed by `grep` that none passes `use_semantic_cache=` as a call-site argument
  (the parameter is never actually overridden by any caller in this file).

## Assumptions
- `_make_rag_cfg()` returns a `SimpleNamespace`, not a `RagConfigImpl`/`RAGConfig`
  instance — confirmed by reading its `return SimpleNamespace(...)` statement — so
  removing this parameter is safe independent of `RagConfigImpl`'s/`RAGConfig`'s own
  field-removal landing order (a `SimpleNamespace` accepts arbitrary keyword
  arguments); the removal here is fixture hygiene tracking the wider Plan, not a hard
  dependency.
- No call site in this file passes `use_semantic_cache=...` as an override (confirmed
  by `grep -n "use_semantic_cache="` matching only the parameter's own definition and
  its forwarding into `SimpleNamespace`, never a caller override) — removing the
  parameter does not require updating any call site's keyword arguments.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Remove the parameter from `_make_rag_cfg()`'s signature (not just its
  forward-into-`SimpleNamespace` line) — since no caller in this file ever overrides
  it, the parameter is purely vestigial once the underlying config concept is
  removed; keeping an unused, disconnected `bool = True` parameter would be
  misleading.

## Alternatives considered
- Leaving the parameter in the signature but no longer forwarding it into
  `SimpleNamespace` — rejected: this would silently make the parameter a no-op
  (accepted but ignored), which is worse than removing it outright, since a future
  caller passing `use_semantic_cache=False` would appear to have an effect but
  actually do nothing.

## Implementation
### Target file
`tests/rag/test_rag_quality_regression.py`

### Procedure
1. Remove the `use_semantic_cache: bool = True,` parameter (line 27) from
   `_make_rag_cfg()`'s signature.
2. Remove `semantic_cache_max_size=100,` (line 31) from the `SimpleNamespace(...)`
   construction.
3. Remove `semantic_cache_threshold=0.85,` (line 32) from the same construction.
4. Remove `use_semantic_cache=use_semantic_cache,` (line 49) from the same
   construction.

### Method
Direct removal via `Edit`: one function-signature parameter removal and three
constructor-argument removals.

### Details
- Confirm no test in `class TestRagQualityRegression` calls `_make_rag_cfg(...,
  use_semantic_cache=...)` before finalizing — re-check via `rg -n
  "_make_rag_cfg\(" tests/rag/test_rag_quality_regression.py` and inspect each call
  site's arguments.
- Confirm after editing: `rg -n "semantic_cache"
  tests/rag/test_rag_quality_regression.py` returns zero matches.

## Compatibility considerations
N/A: test-only file; `_make_rag_cfg()` is private to this test module (leading
underscore).

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; independent of `RagConfigImpl`'s/
  `RAGConfig`'s landing order (see Assumptions), so no cross-document ordering
  constraint applies.

## Validation plan
- `uv run pytest tests/rag/test_rag_quality_regression.py -v` — all tests pass; no
  caller depended on the removed parameter's default value producing a different
  effect than its absence.
- `rg -n "semantic_cache" tests/rag/test_rag_quality_regression.py` — zero matches.

## Completion criteria
- `_make_rag_cfg()`'s signature and `SimpleNamespace` construction no longer reference
  any of the three removed keys (Plan `AC-8`).
- All tests in `class TestRagQualityRegression` pass unchanged.

## Out of scope
- Every other `_make_rag_cfg()` parameter and every test's non-cache assertions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixture cleanup only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-009` (remove cache references from mocks and fixtures)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/rag/test_rag_quality_regression.py
