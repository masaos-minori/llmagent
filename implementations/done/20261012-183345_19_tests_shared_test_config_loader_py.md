## Goal

Update `tests/shared/test_config_loader.py` so `ConfigLoader` obtains its default directory from the resolver (default-via-resolver) while keeping the explicit-override case passing. Implements `REQ-001` / AC-01.

## Scope

Modifies `tests/shared/test_config_loader.py`: add/adjust a default-via-resolver case and keep the explicit-override case.

## Assumptions

- `ConfigLoader.__init__` delegates its default directory to `resolve_config_dir()` (see the `config_loader.py` row); the explicit `config_dir=...` argument still wins.
- The current suite already has an explicit-override case.

## Design decisions

- Add a case asserting that with `LLMAGENT_CONFIG_DIR` pointing at an existing temp dir, `ConfigLoader()` reads from it.
- Add a case asserting that with `LLMAGENT_CONFIG_DIR` pointing at a missing dir, construction raises `FileNotFoundError` naming the path.
- Keep the existing explicit-override case unchanged.

## Alternatives considered

- Rewriting the whole suite: rejected — only the default-directory behavior changes; preserve existing cases.

## Implementation

### Target file

`tests/shared/test_config_loader.py`

### Procedure

Add the default-via-resolver and missing-directory cases; keep the explicit-override case.

### Method

1. Add a test that sets `LLMAGENT_CONFIG_DIR` to a `tmp_path` dir and asserts `ConfigLoader().config_dir` (or equivalent accessor) resolves to it.
2. Add a test that sets `LLMAGENT_CONFIG_DIR` to a missing path and asserts `FileNotFoundError` is raised.
3. Confirm the existing explicit-override test still passes unchanged.

### Details

- Use `monkeypatch` to set/clear `LLMAGENT_CONFIG_DIR` between cases.

## Compatibility considerations

- Existing cases are preserved; only additive cases are added.

## Security considerations

- N/A: the missing-directory case asserts the fail-fast error (AC-01).

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_config_loader.py` — default-via-resolver, missing-directory, and explicit-override cases pass.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy` clean.

## Completion criteria

- `test_config_loader.py` includes the default-via-resolver and missing-directory cases and the explicit-override case; the suite passes.

## Out of scope

- The resolver (`scripts/shared/runtime_paths.py`) and the `ConfigLoader` change are separate rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add default-via-resolver and missing-directory cases | Completed | 20261013-140000 | 20261013-140700 | 新2件追加(既定 via resolver + missing dir の fail-fast)。existing explicit-override 維持。 |
| 2 | Confirm the explicit-override case still passes | Completed | 20261013-140200 | 20261013-140500 | existing 全ケース維持。 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261013-140500 | 20261013-140700 | ruff format/check + mypy 合格。フルsuite 8354 passed/20 skipped/失敗0（回帰なし）。 |
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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-104451_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183345
- **Related target files**: tests/shared/test_config_loader.py
