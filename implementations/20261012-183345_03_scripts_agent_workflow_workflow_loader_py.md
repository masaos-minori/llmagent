## Goal

Derive the module-level `WORKFLOWS_DIR` from the shared config-dir resolver instead of a four-levels-up `__file__` computation that breaks under Nuitka `--onefile`. Implements `REQ-002` / AC-03.

## Scope

Modifies the module-level `WORKFLOWS_DIR` constant in `scripts/agent/workflow/workflow_loader.py`.

## Assumptions

- `WORKFLOWS_DIR` is currently `Path(__file__).resolve().parent.parent.parent.parent / "config" / "workflows"` (verified at lines 48-50): four parent levels up from `scripts/agent/workflow/workflow_loader.py` to the repository root, then `config/workflows`.
- `WORKFLOWS_DIR` is a module-level readonly constant read by the workflow engine and `agent.workflow.validate`.

## Design decisions

- Compute `WORKFLOWS_DIR` as `resolve_config_dir() / "workflows"` at module load, so it inherits the same precedence (env > compiled-adjacent > repo-root) as every other config site.
- Keep it a module-level constant (not a function) because existing importers reference `workflow_loader.WORKFLOWS_DIR` directly.

## Alternatives considered

- Repeating the four-parent traversal inline in a compiled-aware way: rejected — duplicates the resolver logic and would drift; the resolver already encodes the correct root.

## Implementation

### Target file

`scripts/agent/workflow/workflow_loader.py`

### Procedure

Replace the `__file__`-based `WORKFLOWS_DIR` assignment with a resolver-derived one.

### Method

1. Add `from shared.runtime_paths import resolve_config_dir` to the imports.
2. Replace the current `WORKFLOWS_DIR = Path(__file__).resolve().... / "config" / "workflows"` line with `WORKFLOWS_DIR = resolve_config_dir() / "workflows"`.
3. Remove the `Path` import if it becomes unreferenced elsewhere in the file.

### Details

- `resolve_config_dir()` returns the repo-root `config/` when uncompiled, so `uv run python -m agent.workflow.validate` sees the same directory as before.

## Compatibility considerations

- No caller changes; the constant name and type (`Path`) are unchanged.

## Security considerations

- N/A: directory selection only; no command execution or privilege change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_loader.py` — `WORKFLOWS_DIR` resolves correctly.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports` clean.
- `rg "__file__" scripts/agent/workflow/workflow_loader.py` — no remaining `config/` resolution outside the resolver.

## Completion criteria

- `WORKFLOWS_DIR` is derived from `resolve_config_dir()`; the loader test suite passes; no `__file__`-based `config/` resolution remains in the file.

## Out of scope

- The resolver (`runtime_paths.py`) and the other display/error-path rows are separate documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Derive `WORKFLOWS_DIR` from the resolver | Pending | — | — | |
| 2 | Update `tests/agent/workflow/test_workflow_loader.py` | Pending | — | — | |
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-104451_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183345
- **Related target files**: scripts/agent/workflow/workflow_loader.py
