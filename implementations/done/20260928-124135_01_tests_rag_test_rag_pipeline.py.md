## Goal

Add one unit test to `TestFormatChunksDesign2` asserting that `_format_chunks()` never emits a chunk's `normalized_content` value when it differs from `content`, closing the ADR-009 / INV-008 automated-test gap (`REQ-001`, `REQ-002`, `REQ-003`).

## Scope

One new test method appended to the existing `TestFormatChunksDesign2` class in `tests/rag/test_rag_pipeline.py`. No production code change.

## Assumptions

- `SimpleNamespace` (imported at `tests/rag/test_rag_pipeline.py:8`) can stand in for a hit that exposes both `content` and a distinct `normalized_content`.
- `_format_chunks()` reads only `title`, `url`, and `content` (`scripts/rag/stages/augment.py:19-21`); a stray `normalized_content` attribute on the input object does not affect formatting, so its absence in output is a clean assertion signal.
- `RankedHit` has no `normalized_content` field (`scripts/shared/types.py:147-158`), which is exactly why the existing three methods cannot exercise this path.
- The three existing `TestFormatChunksDesign2` methods are left unchanged.

## Design decisions

- Append to the existing `TestFormatChunksDesign2` class rather than introduce a new one: same DESIGN-2 invariant family, keeps related assertions colocated.
- Use `SimpleNamespace` instead of subclassing `RankedHit`: the goal is to prove behavior holds for any object exposing `content` plus an unrelated `normalized_content`, and subclassing would force a dataclass change outside test scope.
- Assert both the positive (`content` present) and negative (`normalized_content` absent) outcomes in a single method.

## Alternatives considered

- Subclassing or extending `RankedHit` to carry `normalized_content`: rejected — expands the dataclass beyond the test's purpose.
- Driving the invariant through `AugmentStage.run()` end-to-end: rejected — the invariant lives entirely in `_format_chunks()`; routing through the async stage adds context-setup cost without additional coverage.

## Implementation
### Target file

`tests/rag/test_rag_pipeline.py`

### Procedure

Append one method to `TestFormatChunksDesign2`, immediately after `test_normalized_differs_from_content_not_in_output` (currently ending at line 161):

1. Build a `SimpleNamespace` with `content="検索結果"`, `normalized_content="けんさく けっか"`, `url="http://example.com"`, `title=""`.
2. Call `_augment_format_chunks([chunk])`.
3. Assert the `content` value is present in the returned string.
4. Assert the `normalized_content` value is absent from the returned string.

### Method

Call `_format_chunks()` directly with the mock object (same style as the existing class `_hit` callers); no async stage or `PipelineContext` required.

### Details

- Contract under test: `_format_chunks()` joins `[Source: ...]\n{sanitize_document(c.content)}` blocks using `c.content` only (`scripts/rag/stages/augment.py:15-24`).
- Gap being closed: the existing `test_normalized_differs_from_content_not_in_output` passes two *literal strings* that merely look different; it never supplies an object carrying a real `normalized_content` attribute, so it does not prove the FTS5-only field is excluded when present.
- Type basis: `RankedHit` (and `RawHit`/`MergedHit`) define no `normalized_content` (`scripts/shared/types.py:122-158`), so the mock must supply it explicitly.
- Reference: `scripts/rag/stages/augment.py`, `scripts/shared/types.py`, `tests/rag/test_rag_pipeline.py:130-161`.

## Compatibility considerations

Purely additive test. No source, API, or behavioral change; existing tests are unaffected.

## Security considerations

N/A for the change itself; the asserted behavior enforces ADR-009 — the FTS5-only `normalized_content` field must never reach LLM-facing output.

## Rollback considerations

Delete the single appended method to fully revert.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/rag/test_rag_pipeline.py` | Unit test execution | `uv run pytest tests/rag/test_rag_pipeline.py::TestFormatChunksDesign2 -v` | All tests in the class pass, including the new method |
| `tests/rag/test_rag_pipeline.py` | Full suite regression | `uv run pytest` | No regressions |

## Completion criteria

- The new method exists inside `TestFormatChunksDesign2` and asserts both `content` presence and `normalized_content` absence.
- It passes in isolation and the full suite shows no regression.

## Out of scope

Any change to `_format_chunks()` behavior; sibling issues CI-009, CI-010, CI-012, CI-016; cross-cutting ownership-model decisions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260928-232024 | 20260928-232024 | Appended test_real_normalized_content_attribute_excluded to TestFormatChunksDesign2 (purely additive; no source change) |
| 2 | Add or update tests per Validation plan | Completed | 20260928-232024 | 20260928-232024 | Targeted 4/4 pass; full suite shows 3 failures present identically on base commit (unrelated to this additive change); no new regressions |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260928-232024 | 20260928-232024 | ruff format+check clean; lint-imports shared->agent violation is pre-existing (production_config_validator); coverage source=scripts only, no source touched |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260928-232024 | 20260928-232024 | N/A: no docs/00_index.md task-scope mapping for tests/rag/test_rag_pipeline.py |

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
- **Requirement ID**: `REQ-001` (ADR-009 prohibition test exists and passes), `REQ-002` (`_format_chunks()` uses `c.content`), `REQ-003` (exclusion verified via mock with a distinct `normalized_content`)
- **Source issue**: `issues/20260927-211346_ci014_add-unit-test-for-adr-009-normalized_content-llm-output-prohibition.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260928-093959_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260928-124135
- **Related target files**: `tests/rag/test_rag_pipeline.py`