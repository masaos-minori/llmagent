# Implementation: Fix MCP response truncation double-truncation bug and add metadata consistency tests

## Goal

Fix the double-truncation bug in `_process_stdio_line` where `_truncate_with_meta()` is called twice (once in `_handle_stdio_request`, once in `_process_stdio_line`) causing `total_bytes` and `actual_visible_bytes` to include the truncation suffix length, and add explicit tests for all truncation boundary scenarios via the stdio path.

## Scope

- **In-Scope**:
  - Fix double-truncation bug: refactor `_StdioRequestResult` to carry truncation metadata from `_handle_stdio_request`
  - Remove redundant `_truncate_with_meta(result)` call in `_process_stdio_line`
  - Add tests for all truncation boundary scenarios via stdio path
  - Update `docs/04_mcp_02_protocol_and_transport.md` if any wording needs clarification after fix
- **Out-of-Scope**:
  - Changing the 512 KB global max response size
  - Adding streaming responses
  - Modifying any other MCP server files

## Assumptions

- The current implementation of `_truncate_with_meta()` is correct: `actual_visible_bytes` is calculated from `len(shown.encode("utf-8"))` after `errors="ignore"` decode.
- The suffix text already uses `actual_visible_bytes` (not the configured limit), consistent with the docs.
- The double-truncation bug means `total_bytes` in `_write_stdio_response` includes the suffix length, which is inaccurate when the original output was truncated.
- For non-introspection, non-error requests, the second truncation call will always truncate (the suffix pushes the text over the limit), so `truncated=True` is correct but metadata is wrong.

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Whether any existing test covers under-limit ASCII separately from UTF-8 | Already checked: `test_under_limit_no_truncation` exists (covers this case with ASCII) |
| UNK-02 | Whether `_process_stdio_line` correctly propagates `tr.text` to the response | Confirmed: `_process_stdio_line` discards the second `tr.text`; `result` remains the original from `_handle_stdio_request` — metadata is wrong but payload is correct |

## Implementation

### Target file: `scripts/mcp/server.py`

#### Procedure

1. Add truncation metadata fields to `_StdioRequestResult` dataclass
2. Update `_handle_stdio_request` to populate these fields
3. Remove redundant `_truncate_with_meta(result)` call in `_process_stdio_line`

#### Method

Direct file edit — modify dataclass and two methods.

#### Details

**1. Update `_StdioRequestResult` dataclass (line 63):**

```python
@dataclasses.dataclass
class _StdioRequestResult:
    """Result from parsing a stdio request line."""

    is_error: bool
    result: str
    req_id: int
    is_introspection: bool
    name: str
    truncated: bool = False
    total_bytes: int = 0
    actual_visible_bytes: int = 0
```

**2. Update `_handle_stdio_request` method (line 324):**

In the non-introspection branch (after line 349), update to carry truncation metadata:

```python
dispatch_result = await self.dispatch(name, dict(req.get("args", {})))
tr = _truncate_with_meta(dispatch_result.output)
result = tr.text
is_error = dispatch_result.is_error

if is_error:
    self._record_tool_error(name)

return _StdioRequestResult(
    is_error=is_error,
    result=result,
    req_id=req_id,
    is_introspection=False,
    name=name,
    truncated=tr.truncated,
    total_bytes=tr.total_bytes,
    actual_visible_bytes=tr.actual_visible_bytes,
)
```

For the introspection branch (line 339-347), add metadata:

```python
if name == "__list_tools__":
    result = _json_dumps({"tools": self.list_tools()})
    return _StdioRequestResult(
        is_error=False,
        result=result,
        req_id=req_id,
        is_introspection=True,
        name=name,
        truncated=False,
        total_bytes=len(result),
        actual_visible_bytes=len(result),
    )
```

**3. Update `_process_stdio_line` method (line 260):**

Remove the redundant truncation call and read metadata from `req_result`:

```python
truncated = req_result.truncated
total_bytes = req_result.total_bytes
actual_visible_bytes = req_result.actual_visible_bytes

# Remove: if not is_error and not is_introspection:
#             tr = _truncate_with_meta(result)
#             is_error = False
#             truncated = tr.truncated
#             total_bytes = tr.total_bytes
#             actual_visible_bytes = tr.actual_visible_bytes
```

### Target file: `tests/test_mcp_server_base.py`

#### Procedure

Add integration tests for truncation metadata via stdio path to `TestRunStdio` class.

#### Method

Direct file edit — append new test methods after existing `test_normal_dispatch_via_run_stdio` method (around line 157).

#### Details

**Add after line 157 (after `test_normal_dispatch_via_run_stdio`):**
```python
    @pytest.mark.asyncio
    async def test_under_limit_no_truncation_via_stdio(self) -> None:
        """Under-limit response should have truncated=False and matching byte counts."""
        srv = _SimpleServer()
        request = orjson.dumps({"id": 3, "name": "tool_a", "args": {}}) + b"\n"

        pre_fed_reader = asyncio.StreamReader()
        pre_fed_reader.feed_data(request)
        pre_fed_reader.feed_eof()

        written: list[str] = []

        from unittest.mock import AsyncMock, MagicMock, patch  # noqa: PLC0415

        mock_loop = MagicMock()
        mock_loop.connect_read_pipe = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_loop.run_in_executor = MagicMock(
            side_effect=lambda executor, fn, *args: fn(*args)
        )

        with (
            patch("asyncio.get_running_loop", return_value=mock_loop),
            patch("asyncio.StreamReader", return_value=pre_fed_reader),
            patch("asyncio.StreamReaderProtocol"),
            patch("sys.stdout") as mock_stdout,
        ):
            mock_stdout.write = lambda s: written.append(s)
            mock_stdout.flush = lambda: None
            await srv.run_stdio()

        assert len(written) == 1
        resp = orjson.loads(written[0])
        assert not resp["truncated"]
        assert resp["total_bytes"] == resp["actual_visible_bytes"]

    @pytest.mark.asyncio
    async def test_over_limit_ascii_truncation_via_stdio(self) -> None:
        """Over-limit ASCII response should have truncated=True with correct metadata."""
        from scripts.mcp.server import MCP_MAX_RESPONSE_BYTES  # noqa: PLC0415

        class _LongServer(_SimpleServer):
            async def dispatch(self, name: str, args: dict) -> DispatchResult:
                if name == "tool_a":
                    long_text = "a" * (MCP_MAX_RESPONSE_BYTES + 1000)
                    return DispatchResult(
                        output=long_text,
                        is_error=False,
                    )
                return await super().dispatch(name, args)

        srv = _LongServer()
        request = orjson.dumps({"id": 4, "name": "tool_a", "args": {}}) + b"\n"

        pre_fed_reader = asyncio.StreamReader()
        pre_fed_reader.feed_data(request)
        pre_fed_reader.feed_eof()

        written: list[str] = []

        from unittest.mock import AsyncMock, MagicMock, patch  # noqa: PLC0415

        mock_loop = MagicMock()
        mock_loop.connect_read_pipe = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_loop.run_in_executor = MagicMock(
            side_effect=lambda executor, fn, *args: fn(*args)
        )

        with (
            patch("asyncio.get_running_loop", return_value=mock_loop),
            patch("asyncio.StreamReader", return_value=pre_fed_reader),
            patch("asyncio.StreamReaderProtocol"),
            patch("sys.stdout") as mock_stdout,
        ):
            mock_stdout.write = lambda s: written.append(s)
            mock_stdout.flush = lambda: None
            await srv.run_stdio()

        assert len(written) == 1
        resp = orjson.loads(written[0])
        assert resp["truncated"]
        # actual_visible_bytes should equal max_bytes for ASCII text
        assert resp["actual_visible_bytes"] == MCP_MAX_RESPONSE_BYTES
        # total_bytes should be the original size, not including suffix
        assert resp["total_bytes"] > MCP_MAX_RESPONSE_BYTES

    @pytest.mark.asyncio
    async def test_over_limit_utf8_truncation_via_stdio(self) -> None:
        """Over-limit UTF-8 response should have actual_visible_bytes < total_bytes."""
        from scripts.mcp.server import MCP_MAX_RESPONSE_BYTES  # noqa: PLC0415

        class _Utf8LongServer(_SimpleServer):
            async def dispatch(self, name: str, args: dict) -> DispatchResult:
                if name == "tool_a":
                    # Multi-byte UTF-8: "あ" is 3 bytes; push over limit with UTF-8 chars
                    utf8_text = "あ" * ((MCP_MAX_RESPONSE_BYTES // 3) + 100)
                    return DispatchResult(
                        output=utf8_text,
                        is_error=False,
                    )
                return await super().dispatch(name, args)

        srv = _Utf8LongServer()
        request = orjson.dumps({"id": 5, "name": "tool_a", "args": {}}) + b"\n"

        pre_fed_reader = asyncio.StreamReader()
        pre_fed_reader.feed_data(request)
        pre_fed_reader.feed_eof()

        written: list[str] = []

        from unittest.mock import AsyncMock, MagicMock, patch  # noqa: PLC0415

        mock_loop = MagicMock()
        mock_loop.connect_read_pipe = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_loop.run_in_executor = MagicMock(
            side_effect=lambda executor, fn, *args: fn(*args)
        )

        with (
            patch("asyncio.get_running_loop", return_value=mock_loop),
            patch("asyncio.StreamReader", return_value=pre_fed_reader),
            patch("asyncio.StreamReaderProtocol"),
            patch("sys.stdout") as mock_stdout,
        ):
            mock_stdout.write = lambda s: written.append(s)
            mock_stdout.flush = lambda: None
            await srv.run_stdio()

        assert len(written) == 1
        resp = orjson.loads(written[0])
        assert resp["truncated"]
        # For UTF-8, actual_visible_bytes may be less than max_bytes due to partial char at boundary
        assert resp["actual_visible_bytes"] <= MCP_MAX_RESPONSE_BYTES
        # total_bytes should be the original UTF-8 byte count
        assert resp["total_bytes"] > MCP_MAX_RESPONSE_BYTES

    @pytest.mark.asyncio
    async def test_truncated_text_valid_utf8_via_stdio(self) -> None:
        """Truncated text via stdio should contain valid UTF-8 (no corrupted characters)."""
        from scripts.mcp.server import MCP_MAX_RESPONSE_BYTES  # noqa: PLC0415

        class _MixedUtf8Server(_SimpleServer):
            async def dispatch(self, name: str, args: dict) -> DispatchResult:
                if name == "tool_a":
                    # Mix ASCII and multi-byte UTF-8 at the truncation boundary
                    long_text = "A" * 100 + "あいうえお" * ((MCP_MAX_RESPONSE_BYTES // 15) + 100)
                    return DispatchResult(
                        output=long_text,
                        is_error=False,
                    )
                return await super().dispatch(name, args)

        srv = _MixedUtf8Server()
        request = orjson.dumps({"id": 6, "name": "tool_a", "args": {}}) + b"\n"

        pre_fed_reader = asyncio.StreamReader()
        pre_fed_reader.feed_data(request)
        pre_fed_reader.feed_eof()

        written: list[str] = []

        from unittest.mock import AsyncMock, MagicMock, patch  # noqa: PLC0415

        mock_loop = MagicMock()
        mock_loop.connect_read_pipe = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_loop.run_in_executor = MagicMock(
            side_effect=lambda executor, fn, *args: fn(*args)
        )

        with (
            patch("asyncio.get_running_loop", return_value=mock_loop),
            patch("asyncio.StreamReader", return_value=pre_fed_reader),
            patch("asyncio.StreamReaderProtocol"),
            patch("sys.stdout") as mock_stdout,
        ):
            mock_stdout.write = lambda s: written.append(s)
            mock_stdout.flush = lambda: None
            await srv.run_stdio()

        assert len(written) == 1
        resp = orjson.loads(written[0])
        # The result text should be valid UTF-8 (no corrupted characters from truncation)
        resp["result"].encode("utf-8")  # raises if corrupted
```

### Target file: `docs/04_mcp_02_protocol_and_transport.md`

#### Procedure

Update Response Truncation section to clarify the metadata is computed on the original output, not the truncated text.

#### Method

Direct file edit — add clarification note after line 285.

#### Details

**Add after line 285:**
```markdown
**Important:** The `total_bytes` and `actual_visible_bytes` fields in the stdio response metadata represent the original dispatch output size, not the truncated text size. This ensures the client can distinguish between a short response (no truncation needed) and a long response that was truncated.
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp/server.py` `_truncate_with_meta` | Unit tests for 4 specified scenarios | `uv run pytest tests/test_mcp_server_base.py::TestTruncateWithMeta -v` | All cases pass |
| `scripts/mcp/server.py` `_process_stdio_line` | Integration test via `run_stdio` with oversized payload | `uv run pytest tests/test_mcp_server_base.py::TestRunStdio -v` | `truncated=True`, correct `total_bytes`, `actual_visible_bytes` |
| `docs/04_mcp_02_protocol_and_transport.md` | Manual review: suffix description matches code | N/A (documentation review) | Suffix description matches `actual_visible_bytes` not limit |
| Full test suite | Regression check | `uv run pytest tests/ -q` | No regressions |

## Risks & Mitigations

- **Risk**: Refactoring `_StdioRequestResult` to carry truncation metadata may miss the error path (is_error=True) → **Mitigation**: Error responses should have `truncated=False`, `total_bytes=0`, `actual_visible_bytes=0`; keep existing defaults and only populate from `TruncationResult` on non-error dispatch
- **Risk**: Double-truncation fix may alter the `result` text if `_process_stdio_line` was accidentally relying on the second `_truncate_with_meta` call → **Mitigation**: The second call's `tr.text` is already discarded in current code; removing the call changes only metadata, not `result`
- **Risk**: Existing tests for `TestRunStdio` may not assert `truncated`/`actual_visible_bytes` fields → **Mitigation**: Add explicit assertions in new tests; existing tests remain valid as they test non-truncation path
