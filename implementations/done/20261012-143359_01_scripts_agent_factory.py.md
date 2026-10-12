## Goal
- Restore concrete types on the memory-service builder helpers so `mypy` rejects `None` or a wrong object at their boundaries, with no runtime change (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`).

## Scope
- Only `scripts/agent/factory.py`: the `TYPE_CHECKING` block near line 46 and the signatures of five builder helpers (around lines 561 to 640). No function body, no call site, no deferred import inside the memory-services builder changes.

## Assumptions
- A scratch-copy experiment already showed the target signatures below give `mypy` clean (425 files) and `ruff` clean, and that passing `None` to the retriever builder is rejected with `arg-type`.
- The retriever builder has one caller, which always passes a real client, and no test calls it; the other defaults in these helpers are not `None`.
- No code in `scripts/` evaluates these annotations at runtime, and the module already uses postponed annotation evaluation.

## Design decisions
- Name the concrete types only under `TYPE_CHECKING`, so no import runs at module load and the deferred imports in the memory-services builder keep their purpose.
- Type the two builders' returns and their class parameters too: with the bare class parameters kept, the mypy return-any warning setting reports two `no-any-return` errors.

## Alternatives considered
N/A: the Plan Design section already fixed the approach; a returns-only variant was measured and rejected.

## Implementation
### Target file
`scripts/agent/factory.py`

### Procedure
1. Record the baseline: `uv run mypy --no-namespace-packages scripts/` is clean and `uv run pytest tests/agent/test_agent_factory.py tests/agent/test_memory_local_only.py -q` passes (46 tests at planning time).
2. In the `TYPE_CHECKING` block (line 46) add four type-only names next to `MemoryServices`, keeping the isort order: `EmbeddingClient` (embedding client module), `JsonlMemoryStore` (jsonl store module), `HybridRetriever` (retriever module), `MemoryStore` (store module); `MemoryServices` stays.
3. Embedding-client builder: `client_cls` becomes `type[EmbeddingClient]` and the return type becomes `EmbeddingClient`; `config_cls` stays a bare `type`.
4. Retriever builder: the keyword-only `embed_client` becomes `EmbeddingClient` with no default (the parameter stays keyword-only and required).
5. JSONL store builder: `jsonl_cls` becomes `type[JsonlMemoryStore]` and the return type becomes `JsonlMemoryStore`.
6. Injection service builder: `embed_client` becomes `EmbeddingClient` and `retriever` becomes `HybridRetriever`.
7. Ingestion service builder: `store` becomes `MemoryStore`, `jsonl` becomes `JsonlMemoryStore`, `retriever` becomes `HybridRetriever`, `embed_client` becomes `EmbeddingClient`.
8. Leave every function body, the policy and dedup class parameters, the generic service class parameters, and all call sites as they are.

### Method
- Edit the signatures in place; run `ruff format` afterwards because the longer annotations may reflow a signature across lines.
- After the edit, run the mutation check from the Validation plan, then revert it with an inverse edit (do not use a checkout, the file holds the real change).

### Details
- Target signatures, in prose: embedding-client builder takes the context, the HTTP client, a class of the embedding client and a bare config class and returns an embedding client; retriever builder takes the context and a generic retriever class plus a required keyword-only embedding client; JSONL builder takes the context and a class of the JSONL store and returns a JSONL store.
- The deferred imports inside the memory-services builder repeat names that now also appear under `TYPE_CHECKING`; this was accepted by `ruff` and `mypy` in the experiment, so keep both.
- Do not touch the `branch` parameters (they default to an empty string).

## Compatibility considerations
- Private helpers with one production caller; no public interface changes. The retriever builder's `embed_client` becomes required, which its only caller already satisfies. A running production agent picks the change up only after redeploy; deployment is outside this procedure.

## Security considerations
N/A: type annotations only; no input handling or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run mypy --no-namespace-packages scripts/` (clean), `uv run ruff format --check scripts/`, `uv run ruff check scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/agent -c pyproject.toml`.
- `uv run pytest tests/agent/test_agent_factory.py tests/agent/test_memory_local_only.py tests/agent/test_import_smoke.py -v` unchanged and passing.
- Mutation check: temporarily pass `embed_client=None` in the retriever builder call, run `uv run mypy --no-namespace-packages scripts/agent/factory.py`, expect an `arg-type` error, then revert by an inverse edit and confirm clean.

## Completion criteria
- No memory-builder argument is annotated `object`; the two builders return concrete types; the retriever builder has no `None` default; `git diff` shows only the `TYPE_CHECKING` block and signatures; `mypy`, `ruff`, `bandit`, `lint-imports` and the tests pass; the mutation check failed as expected and was reverted.

## Out of scope
- Call sites, function bodies, non-memory builders, new runtime tests, and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the TYPE_CHECKING imports and signature changes to the five builders | Completed | 20261012-143557 | 20261012-143632 | stale_detector clean changed: scripts/agent/factory.py (4 TYPE_CHECKING imports; 5 builder signatures; diff is signatures only) |
| 2 | Run the validation sequence (`rules/toolchain.md`) and the mutation check | Completed | 20261012-144245 | 20261012-144245 | mypy (425 files), ruff, lint-imports (5 kept, 0 broken), bandit (no high/medium), 50 targeted tests, full suite 8257 passed, pre-commit pass; mutation check: embed_client=None -> arg-type error, reverted by inverse edit |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` (concrete builder types; retriever default removed; returns and class parameters typed; no behavior change)
- **Source issue**: issues/20261012-124821_start002_memory-service-builders-in-factory.py-erase-concrete-types-with-object-annotations-and-none-defaults.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-142724_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-143359
- **Related target files**: scripts/agent/factory.py