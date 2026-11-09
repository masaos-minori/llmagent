## Goal

Set `rag_db_path` explicitly in the `_make_cfg` fixture of `tests/agent/commands/test_agent_rag.py`, so the real `RagPipeline` those tests construct keeps resolving once `rag_db_path` is required with `use_search=True` (`REQ-006`: fallout fix, no behavior test weakened).

## Scope
**Release unit**: ragrev008-core

- In scope: the defaults dict in `_make_cfg` of `tests/agent/commands/test_agent_rag.py`.
- Out of scope: any test assertion, the production resolver, and other test files.
- Fallout row added to the Plan by amendment in Step 3a (class fallout); Plan step 3, first bullet.

## Assumptions

- Re-verified at generation time: `_make_cfg` builds a `SimpleNamespace` with `use_search: True`, `rag_query_service_url`, `llm_url`, `embed_url` and no `rag_db_path`; five tests build `RagPipeline(http, cfg)` with it, so the real resolver runs on that object.
- Until `..._01_scripts_rag_config_resolution.py.md` is applied, an extra `rag_db_path` attribute is harmless (it is a known config field), so this change can be applied before or after it; both ship in Release unit `ragrev008-core`.
- The tests that call `augment()` already patch `rag.pipeline.SQLiteHelper` where the in-process path opens a database, so a path value does not cause real database access; a value of `":memory:"` matches the other in-tree fixtures that set it explicitly.

## Design decisions

- Add `"rag_db_path": ":memory:"` to the `defaults` dict next to the other URL keys; no new fixture and no per-test override.
- Do not touch any assertion or the `**kwargs` override mechanism.

## Alternatives considered

- Passing `module_cfg={"rag_db_path": ...}` in each of the five `RagPipeline(...)` calls: rejected; one fixture edit is smaller and does not change how the tests construct the pipeline.

## Implementation
### Target file
`tests/agent/commands/test_agent_rag.py`

### Procedure
1. In `_make_cfg`, add `"rag_db_path": ":memory:"` to `defaults`.

### Method
- Keep key order and style of the surrounding entries.

### Details
- After the edit run `uv run pytest tests/agent/commands/test_agent_rag.py -q`; it must pass both before and after the resolver change.
- A second fixture in this file needing the same fix would be the same fallout; report it rather than editing other files.

## Compatibility considerations

N/A: test-only; no test is weakened and the tests keep their intent.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/commands/test_agent_rag.py -q` (green on HEAD and after the resolver change).
- `uv run ruff check tests/agent/commands/test_agent_rag.py` and `uv run ruff format --check tests/agent/commands/test_agent_rag.py`.
- `uv run pytest tests -q` compared with the pre-change baseline recorded by `..._01_scripts_rag_config_resolution.py.md`.

## Completion criteria

- `_make_cfg` sets `rag_db_path` explicitly and the five `RagPipeline` tests pass against the changed resolver.
- No assertion was modified; ruff is clean.

## Out of Scope

- The resolver, its tests, docs, and any other fixture.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the explicit `rag_db_path` to the `_make_cfg` defaults | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) and the file's tests | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (fallout fixes for the implicit `:memory:` default)
- **Source issue**: issues/20261108-131121_ragrev008_rag-config-defaults-mutation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165441_ragrev008_rag-config-defaults-mutation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-135232
- **Related target files**: `tests/agent/commands/test_agent_rag.py`
