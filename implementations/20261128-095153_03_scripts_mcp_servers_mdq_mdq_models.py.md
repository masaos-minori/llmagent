## Goal

Remove the 9 response models in `scripts/mcp_servers/mdq/mdq_models.py` that no production code produces, including the empty `IndexMetadata` placeholder, so the module declares only shapes that have a consumer (`REQ-004`, every model has a production consumer; `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

- 9 class definitions are deleted; no remaining definition is touched.
- The enforcement is the guard test in row 09, which is written before the deletion (plan Phase 1 pin) and flipped to the guard assertion in plan Phase 3.

## Assumptions

- Removal is the plan default because no producer exists. Implementing the shapes would make the service return models, which is a behavior change owned by the mdqmcp001 and mdqmcp008 plans.
- Verified at current HEAD: zero references to `ParsedSectionRequest`, `SearchDocsResponse`, `GetChunkResponse`, `OutlineResponse`, `IndexPathsResponse`, `RefreshIndexResponse`, `IndexMetadata`, `StatsResponse`, and `GrepDocsResponse` outside `mdq_models.py` in `scripts/`, `tests/`, and `docs/`.
- `IndexMetadata` is `pass`-only and is named only by `StatsResponse.index_metadata` (line 322); at current HEAD `stats()` builds no metadata dict from `index_state` (its docstring, line 334, says the raw dict is not part of the response), so the model has no producer left and is removed.
- `vulture --min-confidence 80` reports nothing for this module, because these are public definitions, which is why the static dead-code gate cannot catch them and the guard test is the enforcement.
- `tools/check_docstrings_baseline.txt` line 185 records this module as `missing separator`; the entry stays valid because no module docstring changes. Module size 12071 B, below the 24576 B gate.

## Design decisions

- Delete rather than implement: a declared shape with no producer reads as a contract, which is the problem `REQ-004` states.
- `IndexMetadata` is deleted with `StatsResponse` rather than kept as a placeholder, because its only consumer is the dead model being removed.
- The guard's consumer rule excludes `mdq_models.py` itself, so a definition referenced only from inside the module does not satisfy `AC-4`; this is what keeps `IndexMetadata`-like placeholders from passing the guard.

## Alternatives considered

- Keep the models and add producers in the service: rejected here, it is a behavior change owned by another plan.
- Rely on `vulture`: rejected, it reports nothing for these definitions (plan Design, Step 5 baseline).

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_models.py`

### Procedure
1. Delete `ParsedSectionRequest` (59), `SearchDocsResponse` (264), `GetChunkResponse` (270), `OutlineResponse` (288), `IndexPathsResponse` (295), `RefreshIndexResponse` (301), `IndexMetadata` (311), `StatsResponse` (317), and `GrepDocsResponse` (335).
2. Leave every other definition in place.

### Method

- Apply after row 09's guard test exists, so the deletion is the flip of a recorded assertion rather than an untracked removal (plan Phase 1 then Phase 3).
- `radon cc -s` reports rank A for every function and class in this module, so no complexity threshold is affected by the deletions.
- `bandit -c pyproject.toml` reports no Medium or High finding for this module, and the deletions add none.

### Details

- Retained shapes: the internal DTOs with consumers (`ParsedSection`, `ChunkRecord`, `SearchResultItem`, `OutlineHeading`, `GrepDocMatch`) and the metadata shapes the audit layer reads (`SearchDocsMetadata`, `IndexPathsMetadata`, `GrepDocsMetadata`).
- Retained request models and exception classes are unchanged, so the schema parity established by the mdqmcp008 plan is not disturbed.

## Compatibility considerations

- 10 `scripts/` modules and 20 test modules import this module; none imports a deleted name, so no consumer changes.
- `tests/mcp_servers/mdq/test_mdq_model_usage.py` (row 09) is the test that documents the change: its pin records the 9 names before the deletion, and its guard assertion after it.

## Security considerations

- `N/A: definition removal only.` No authorization, path, or scope field is involved.

## Rollback considerations

- Revert the commit. No persisted state, migration, or config key depends on the deleted definitions.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_model_usage.py -m repo_scan` — the guard (`AC-4`)
- `uv run ruff check scripts/mcp_servers/mdq/mdq_models.py && uv run mypy scripts/mcp_servers/mdq/mdq_models.py`
- Full sequence per `rules/toolchain.md`, including the diff-scoped coverage gate at the 90 percent threshold.

## Completion criteria

- The 9 names are absent from the module (`AC-4`).
- Every remaining definition has at least one consumer in `scripts/` outside this module, as the guard test asserts (`AC-4`).
- No import of a deleted name fails anywhere in `scripts/`, `tests/`, or `docs/`.

## Out of Scope

- The guard test itself (`tests/mcp_servers/mdq/test_mdq_model_usage.py`, row 09).
- Any response-model behavior change, which belongs to the mdqmcp001 and mdqmcp008 plans.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 3 |
| 2 | Add or update tests per Validation plan | Pending | — | — | The pin and the guard live in row 09 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A for this row: the documentation change is row 06 |

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
- **Requirement ID**: REQ-004 (every model has a production consumer), AC-4
- **Source issue**: `issues/20261119-142132_mdqmcp010_mdq-release-readiness.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-095153
- **Related target files**: `scripts/mcp_servers/mdq/mdq_models.py`
