## Goal

Update `tests/agent/workflow/test_workflow_loader.py` so `WORKFLOWS_DIR` resolves through the shared resolver (env > compiled-adjacent > repo-root) instead of a `__file__` computation. Implements `REQ-002` / AC-03.

## Scope

Modifies `tests/agent/workflow/test_workflow_loader.py`: add/adjust a case asserting `WORKFLOWS_DIR` resolves via the resolver.

## Assumptions

- `WORKFLOWS_DIR` is now `resolve_config_dir() / "workflows"` (see the `workflow_loader.py` row).
- The current suite references `WORKFLOWS_DIR`.

## Design decisions

- Add a case asserting that with `LLMAGENT_CONFIG_DIR` set to an existing temp dir, `workflow_loader.WORKFLOWS_DIR` equals `<that dir>/workflows`.
- Keep existing cases that do not depend on the old `__file__` traversal.

## Alternatives considered

- Rewriting the suite: rejected — only the resolution mechanism changed; the constant name and type are unchanged.

## Implementation

### Target file

`tests/agent/workflow/test_workflow_loader.py`

### Procedure

Add a case asserting the resolver-derived `WORKFLOWS_DIR`.

### Method

1. Add a test that sets `LLMAGENT_CONFIG_DIR` to a `tmp_path` dir and asserts `workflow_loader.WORKFLOWS_DIR == tmp_path / "workflows"`.
2. Confirm existing cases that do not depend on the old traversal still pass.

### Details

- Because `WORKFLOWS_DIR` is a module-level constant computed at import time, reload the module under the patched env (or assert against the repo-root value when no env is set) rather than expecting the constant to update live.

## Compatibility considerations

- Existing cases are preserved.

## Security considerations

- N/A: directory selection only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_loader.py` — the resolver-derived `WORKFLOWS_DIR` case passes.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy` clean.

## Completion criteria

- `test_workflow_loader.py` asserts the resolver-derived `WORKFLOWS_DIR`; the suite passes.

## Out of scope

- The resolver (`scripts/shared/runtime_paths.py`) and the other config-site rows are separate rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the resolver-derived `WORKFLOWS_DIR` case | Completed | 20261013-141500 | 20261013-142100 | `WORKFLOWS_DIR == resolve_config_dir() / "workflows"` を構造的に検証する1件追加。reload 版は共有モジュールのクラス差し替えで他へ横漏出するため採用せず、安全な別手法に切り替え。 |
| 2 | Confirm existing cases still pass | Completed | 20261013-141800 | 20261013-142000 | existing 全ケース維持（ランダム順序含む全23件合格）。 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261013-142000 | 20261013-142100 | ruff format/check+mypy 合格。フルsuite 8355 passed/20 skipped/失敗0（回帰なし）。 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A |

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
- **Related target files**: tests/agent/workflow/test_workflow_loader.py
