# Procedure: create the fixture builder that keeps the permissive test defaults

## Goal

Add `build_fixture_runtime_tool` (new) that reproduces the old permissive defaults by delegating to the real builder (Plan REQ-002).

## Scope

- Create only `tests/shared/runtime_tool_factory.py`.
- In scope: one function and its docstring.
- Out of scope: call-site changes (rows 03-08), the production builder (row 01).

## Assumptions

- `tests/shared/` has no `__init__.py` and `tests/` is a regular package; confirm the module imports as `tests.shared.runtime_tool_factory` from a test under `tests/agent/services` and from one under `tests/integration` before moving call sites (UNK-03); if it fails, record it and stop (Plan amendment needed).
- The wrapper delegates to whatever `build_runtime_tool` signature exists, so it works before and after row 01.
- Overlap (compatible): `plans/done/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md` (archived, procedures pending) also targets `tests/shared/test_runtime_tool_registry.py`; it adds exclusion-reason tests, while this procedure only changes which builder the existing calls use. The mcpcompat003 work (`implementations/20261028-065435_*`, already executed) edited `tests/shared/test_resource_scope.py`; re-read it before editing.

## Design decisions

- Take `*args` and `**overrides` so existing call forms (`name`, `server_key` positionally or by keyword, plus overrides) keep working.
- Reproduce the old rules exactly: `is_write` omitted or `None` becomes `False` and makes `requires_serial` default to `True`; otherwise `requires_serial` defaults to `False`; scope kind defaults to `""` and scope keys to `()`.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`tests/shared/runtime_tool_factory.py` (new)

### Procedure

- Create the module with `from __future__ import annotations`, a one-line module docstring header and imports of `Any` and `RuntimeTool`, `build_runtime_tool` from `shared.runtime_tool`.
- Define `build_fixture_runtime_tool(*args: Any, **overrides: Any) -> RuntimeTool` (new): pop `is_write`, `requires_serial`, `resource_scope_kind`, `resource_scope_keys` from `overrides`, apply the old defaults, and call `build_runtime_tool(*args, is_write=..., requires_serial=..., resource_scope_kind=..., resource_scope_keys=..., **overrides)`.
- Docstring: test-only; production modules MUST NOT import it (a guard test enforces this).

### Method

New file of about 30 lines; no other file changes.

### Details

- The module lives under `tests/`, which `scripts/` never imports; `.importlinter` covers `scripts/` packages only.
- Add the equivalence tests in `tests/shared/test_runtime_tool.py` (row 03).

## Compatibility considerations

- Test-only; no production change.

## Security considerations

- No security impact.

## Rollback considerations

- Delete the new file (a single file) if the batch is reverted.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/shared/test_runtime_tool.py -q` | Pass |
| 2 | `uv run ruff format tests/shared/runtime_tool_factory.py`; `uv run ruff check tests/shared/runtime_tool_factory.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r tests/shared/runtime_tool_factory.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- The fixture builder returns the same `RuntimeTool` the old permissive builder returned for omitted `is_write`, explicit `is_write=True` and omitted scope.

## Out of Scope

- Production changes, call-site moves.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (fixture builder)
- **Source issue**: issues/20261027-155851_rtool008_fail-closed-runtimetool-builder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120306
- **Related target files**: tests/shared/runtime_tool_factory.py
