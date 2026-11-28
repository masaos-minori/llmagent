## Goal

Create `tests/mcp_servers/mdq/test_mdq_model_usage.py`, which pins the 9 response models as consumer-less and then guards that every definition in `scripts/mcp_servers/mdq/mdq_models.py` has a consumer in `scripts/` (`REQ-004`; `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

- New test module: one pin stage (plan Phase 1) and one guard stage (plan Phase 3), in the same file.
- The module is `contract`, so it carries the `REQ-004` citation, and it is `repo_scan` because it reads the whole repository.

## Assumptions

- The module does not exist today; `tests/mcp_servers/mdq/` holds 38 test modules at current HEAD (35 at the evidence revision) and none checks model usage, and the directory has no `__init__.py`, so the module is imported as `tests.mcp_servers.mdq.test_mdq_model_usage` following the existing helper precedent.
- `vulture --min-confidence 80` reports nothing for `mdq_models.py`, because these are public definitions, so the static dead-code gate cannot catch them; this module is the enforcement the plan names.
- The consumer rule excludes `mdq_models.py` itself, so a definition referenced only from inside the module does not satisfy `AC-4`; this is what keeps a `pass`-only placeholder such as `IndexMetadata` from passing the guard.
- `tools/test_taxonomy_baseline.txt` has no MDQ entry, and none is added: the baseline is for modules that cannot be classified, and this module can be.
- `repo_scan` is registered in `pyproject.toml` (line 147), and CI's coverage run deselects it, so the guard must be run explicitly with `-m repo_scan`.

## Design decisions

- Scan text for whole-word references rather than importing `mdq_models.py`: importing a model module for a static check would make the guard depend on the definitions it is checking, and a deleted name would raise at import time instead of reporting which definition lost its consumer.
- Keep the guard as one test with a single assertion over the collected names, so a failure names the definitions rather than producing several partial failures.
- Use `pytestmark = pytest.mark.contract` at module level and `@pytest.mark.repo_scan` on the test, matching the repository convention where the taxonomy marker is module-level and `repo_scan` is per-test (`tests/shared/test_route_resolver.py:246`).

## Alternatives considered

- Rely on `vulture` as the gate: rejected, it reports nothing for these definitions, which is why the plan requires a guard test.
- Put the guard in `tests/tools/` as a checker test: rejected, the assertion is about the MDQ model module's consumers, and the plan names `tests/mcp_servers/mdq/` as its location.
- Keep the pin as a permanent assertion: rejected, the plan flips it to the guard in Phase 3, so the pin records the change and the guard prevents its return.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_model_usage.py` (new)

### Procedure
1. Create the module with the module docstring carrying the `REQ-004` citation, `import pytest`, `pytestmark = pytest.mark.contract`, and `@pytest.mark.repo_scan` on the test.
2. Stage 1 (plan Phase 1): assert the 9 names are defined in `mdq_models.py` and that none of them has a reference in `scripts/` outside the module, with the 9 names written as an inline literal set.
3. Stage 2 (plan Phase 3, after row 03 deletes the definitions): flip the assertion so every class defined in `mdq_models.py` has at least one whole-word reference in a `scripts/` file other than `mdq_models.py`.

### Method

- Resolve the repository root as `Path(__file__).resolve().parents[3]` and read `scripts/mcp_servers/mdq/mdq_models.py` with `ast.parse` to collect the class definitions, then read every `.py` file under `scripts/` for whole-word references.
- Apply the flip only after row 03 lands, so the pin and the guard are two recorded states rather than an untracked deletion.
- No database, no service instance, and no fixture is needed: the guard is a static scan, so it is deterministic and does not touch `/opt/llm`.

### Details

- Names pinned in stage 1: `ParsedSectionRequest`, `SearchDocsResponse`, `GetChunkResponse`, `OutlineResponse`, `IndexPathsResponse`, `RefreshIndexResponse`, `IndexMetadata`, `StatsResponse`, `GrepDocsResponse`.
- Stage 2 must not treat `docs/` as a consumer, because `AC-4` names a consumer in `scripts/`; a docs mention would let a documented-but-unused shape pass.
- `tests/mcp_servers/mdq/` has no `__init__.py`, so no package file is added.

## Compatibility considerations

- Nothing imports the deleted names, so the guard's stage-2 assertion holds for the retained definitions (`ParsedSection`, `ChunkRecord`, `SearchResultItem`, `OutlineHeading`, `GrepDocMatch`, `SearchDocsMetadata`, `IndexPathsMetadata`, `GrepDocsMetadata`, the request models, and the exception classes).
- The module is judged only after row 05 adds `tests/mcp_servers/mdq` to `CLASSIFIED_AREAS`; before that it is not reported, so the citation and the marker are safe to land in any order.
- CI deselects `repo_scan`, so the guard is not part of the coverage run; it runs as an explicit gate.

## Security considerations

- `N/A: static repository scan in a test.` No authorization, path, or scope behavior is involved; the scan reads source files only.

## Rollback considerations

- Delete the module and revert the commit. No persisted state is involved.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_model_usage.py -m repo_scan` — the guard (`AC-4`)
- `uv run python tools/check_test_taxonomy.py` — the module is `contract` with the `REQ-004` citation (`AC-3`)
- `uv run ruff check tests/mcp_servers/mdq/test_mdq_model_usage.py && uv run mypy tests/mcp_servers/mdq/test_mdq_model_usage.py`
- Full sequence per `rules/toolchain.md`, including the diff-scoped coverage gate at the 90 percent threshold.

## Completion criteria

- Stage 1 records that the 9 models have no consumer, so the removal is a recorded change (`AC-4`).
- Stage 2 fails when a definition in `mdq_models.py` has no consumer in `scripts/` outside the module (`AC-4`).
- The module carries exactly one taxonomy marker and the citation, and appears in no baseline entry (`AC-3`).

## Out of Scope

- The deletion itself (`scripts/mcp_servers/mdq/mdq_models.py`, row 03).
- Any change to `vulture` configuration or to the dead-code gate.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 1 pin, flipped in Phase 3 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | The "Add or update tests" step does not apply: this row is the test module itself |

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
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_model_usage.py`
