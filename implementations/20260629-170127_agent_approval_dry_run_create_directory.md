# Implementation: Add `create_directory` to approval_dry_run_tools

## Goal

Add `create_directory` to `approval_dry_run_tools` in `config/security.toml` and `_DEFAULT_DRY_RUN_TOOLS` in `config_builders.py` so that approval-flow dry-run preview is consistent with the tool's actual `dry_run` implementation and documentation.

## Scope

- **In-Scope**:
  - `config/security.toml`: add `create_directory` to `approval_dry_run_tools`
  - `scripts/agent/config_builders.py`: add `create_directory` to `_DEFAULT_DRY_RUN_TOOLS`
  - `tests/test_tool_approval_preflight.py`: add test asserting `create_directory` dry-run is exercised by the approval flow
- **Out-of-Scope**:
  - Changes to `write_service.py`, `write_models.py`, `write_tools.py` (implementation already correct)
  - Changes to `04_mcp_04_server_catalog.md` (already lists `create_directory` with dry_run)
  - Changes to `04_mcp_05_security_and_safety_model.md` (Dry-Run Support table already lists `create_directory`)
  - Adding dry_run to unrelated tools

## Assumptions

- `create_directory(dry_run=True)` is fully implemented and tested in `write_service.py` (confirmed: TestCreateDirectoryDryRun class exists with 4 tests)
- `04_mcp_04_server_catalog.md` and `04_mcp_05_security_and_safety_model.md` are already consistent (confirmed)
- `approval_dry_run_tools` in `security.toml` is the canonical config consumed at runtime; `_DEFAULT_DRY_RUN_TOOLS` in `config_builders.py` is the fallback when the key is absent from the TOML

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Whether `test_tool_approval_preflight.py` already covers `create_directory` dry-run in the approval flow | No existing test for `create_directory` — need to add one |
| UNK-02 | Whether any other file-write tool (e.g. `move_file`) is missing from `approval_dry_run_tools` compared to its implementation | `move_file` is already listed; only `create_directory` is the gap |

## Implementation

### Target file: `config/security.toml`

#### Procedure

Add `create_directory` to the `approval_dry_run_tools` list.

#### Method

Direct file edit — add after `"edit_file"`.

#### Details

**Replace lines 84-90:**
```toml
# Tools that support dry_run=True; approval flow executes dry_run before prompting
approval_dry_run_tools = [
  "write_file",
  "edit_file",
  "create_directory",
  "delete_file",
  "delete_directory",
  "move_file",
]
```

### Target file: `scripts/agent/config_builders.py`

#### Procedure

Add `create_directory` to `_DEFAULT_DRY_RUN_TOOLS` list.

#### Method

Direct file edit — add after `"edit_file"`.

#### Details

**Replace lines 107-113:**
```python
_DEFAULT_DRY_RUN_TOOLS: list[str] = [
    "write_file",
    "edit_file",
    "create_directory",
    "delete_file",
    "delete_directory",
    "move_file",
]
```

### Target file: `tests/test_tool_approval_preflight.py`

#### Procedure

Add test asserting that when `create_directory` is invoked via the approval flow, the preflight dry-run is triggered.

#### Method

Direct file edit — add new test method in class `TestCheckApprovalDryRun`.

#### Details

**Add after line 384 (after `test_dry_run_result_appended_to_preview`):**
```python
    @pytest.mark.asyncio
    async def test_create_directory_dry_run_result_appended_to_preview(self) -> None:
        """create_directory dry_run execution output should be included in preview before prompt."""
        cfg = _make_cfg()
        ctx = _make_ctx(cfg=cfg)
        ctx.services.tools = MagicMock()
        ctx.services.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="Dry-run: /tmp/newdir (0 bytes) [new directory]",
                is_error=False,
                request_id="",
                server_key="",
            )
        )

        printed: list[str] = []
        with (
            patch("builtins.print", side_effect=lambda *a: printed.append(str(a))),
            patch("asyncio.to_thread", new=AsyncMock(return_value="y")),
        ):
            result = await check_approval(
                ctx, "create_directory", {"path": "/tmp/newdir"}
            )

        assert result is True
        combined = " ".join(printed)
        assert "Dry-run" in combined
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `config/security.toml` | Config load round-trip: verify `create_directory` appears in loaded `ApprovalConfig.approval_dry_run_tools` | `uv run pytest tests/test_config_builders.py -v` | `create_directory` in loaded list |
| `scripts/agent/config_builders.py` | Unit test `_DEFAULT_DRY_RUN_TOOLS` contains `create_directory` | `uv run pytest tests/test_config_builders.py -v` | Assertion passes |
| `tests/test_tool_approval_preflight.py` | Approval preflight for `create_directory` triggers dry_run call | `uv run pytest tests/test_tool_approval_preflight.py::TestCheckApprovalDryRun -v` | New test passes; existing tests still pass |
| `scripts/mcp/file/write_service.py` | Side-effect free dry_run (no directory created) | `uv run pytest tests/test_file_write_mcp_service.py::TestCreateDirectoryDryRun -v` | All 4 tests pass; no filesystem side effects |
| Full regression | No regressions in approval or file-write logic | `uv run pytest tests/ -v --tb=short` | All tests pass |

## Risks & Mitigations

- **Risk**: Adding `create_directory` to `_DEFAULT_DRY_RUN_TOOLS` changes default behavior for deployments that rely on the fallback (no `security.toml` override) → **Mitigation**: The dry-run insertion is a preview-only step; it does not block execution. The user still sees the approval prompt after the dry-run output. No destructive behavior is introduced.
- **Risk**: `test_tool_approval_preflight.py` may mock the tool executor in a way that makes adding `create_directory` assertions fragile → **Mitigation**: Mirror the existing pattern for `write_file` (same mocking approach, same assertion style).
