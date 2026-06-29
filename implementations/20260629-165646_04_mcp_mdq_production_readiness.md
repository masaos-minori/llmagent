# Implementation: mdq-mcp production-readiness and stub marker inconsistency resolution

## Goal

Resolve mdq-mcp production-readiness and stub marker inconsistency by aligning code, documentation, and tests around a single verified status.

## Scope

- **In-Scope**:
  - Verify and document that all 7 non-admin mdq-mcp tools have `"status": "production"` in `scripts/mcp/mdq/tools.py`
  - Verify and document that the `/health` endpoint contains no `stub` field
  - Fix MCP-03 in `docs/04_mcp_90_inconsistencies_and_known_issues.md`: remove the incorrect "mixed statuses (production and stub)" wording
  - Mark MCP-05 in `docs/04_mcp_90_inconsistencies_and_known_issues.md` as resolved (move to Resolved section or update text)
  - Add explicit tool status declaration to mdq-mcp section in `docs/04_mcp_04_server_catalog.md`
  - Add unit tests for health metadata consistency (no `stub` field) and tool metadata consistency (all non-admin tools have `"status": "production"`)
- **Out-of-Scope**:
  - Redesigning MDQ indexing
  - Migrating MDQ data to RAG
  - Implementing hybrid search (`mode=hybrid`)
  - Changing any runtime behavior of mdq-mcp server

## Assumptions

- Code in `scripts/mcp/mdq/tools.py` is ground truth: 7 non-admin tools all have `"status": "production"`, 2 admin tools have `"status": "admin"`, no `stub` key anywhere
- The `/health` endpoint in `scripts/mcp/mdq/server.py` returns no `stub` field — confirmed by reading the code
- `04_mcp_90` MCP-03 "mixed statuses (production and stub)" is stale wording from a prior state of the code
- `04_mcp_90` MCP-05 "Historical context" section correctly describes prior state; the issue body should be resolved/closed

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Whether a "Resolved Issues" section already exists in `04_mcp_90_inconsistencies_and_known_issues.md` | No dedicated "Resolved" section visible — add one and move MCP-05 there |
| UNK-02 | Whether `fts_consistency_check` and `fts_rebuild` should be tested as `"status": "admin"` (not `"production"`) | Confirmed in `tools.py`: both have `"status": "admin"` |

## Implementation

### Target file: `docs/04_mcp_04_server_catalog.md` (mdq-mcp section)

#### Procedure

Add explicit tool status declaration to mdq-mcp section.

#### Method

Direct file edit — add a new line after the Tools section.

#### Details

**Add after line 289 (after the Tools line):**
```markdown
**Tool status:** 7 tools are `production` (`search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`), 2 tools (`fts_consistency_check`, `fts_rebuild`) are `admin`.
```

### Target file: `docs/04_mcp_90_inconsistencies_and_known_issues.md`

#### Procedure

Fix MCP-03 wording and mark MCP-05 as resolved.

#### Method

Direct file edit — replace MCP-03 text and add MCP-05 resolution note.

#### Details

**Replace lines 63-69 (MCP-03):**
```markdown
**Statement B (mdq-mcp section):** mdq-mcp lacks an equivalent tool status declaration in `04_mcp_04_server_catalog.md`.

**Current safe interpretation:** mdq-mcp tools have mixed statuses (production and admin). Cross-reference `scripts/mcp/mdq/tools.py` to verify individual tool status.

**Recommended action:** Add explicit tool status declaration for mdq-mcp similar to rag-pipeline-mcp's declaration.
```

**Add after line 105 (MCP-05):**
```markdown
**Status: RESOLVED — 2026-06-18.** The `stub` marker has been verified absent from both `scripts/mcp/mdq/tools.py` (no `stub` key in any tool entry) and `scripts/mcp/mdq/server.py` (no `stub` field in `/health` endpoint). All 7 non-admin mdq-mcp tools have `"status": "production"`. This issue is closed.
```

### Target file: `tests/test_mdq_metadata_consistency.py` (new file)

#### Procedure

Create unit tests for health metadata consistency and tool metadata consistency.

#### Method

New file creation — add test class with assertions.

#### Details

**Create new file:**
```python
"""tests/test_mdq_metadata_consistency.py

Unit tests for mdq-mcp health and tool metadata consistency.

Verifies:
- No `stub` key in any mdq-mcp tool entry
- All non-admin tools have `"status": "production"`
- Admin tools (`fts_consistency_check`, `fts_rebuild`) have `"status": "admin"`
- Total tool count is 9
- Health response dict contains no `stub` field
"""

from __future__ import annotations

import pytest


class TestMdqToolMetadataConsistency:
    """Verify mdq-mcp tool metadata is consistent (no stub markers, correct statuses)."""

    def test_total_tool_count(self) -> None:
        """mdq-mcp has exactly 9 tools."""
        from mcp.mdq.tools import _MCP_TOOLS

        assert len(_MCP_TOOLS) == 9

    def test_no_stub_keys_in_tools(self) -> None:
        """No mdq-mcp tool entry contains a `stub` key."""
        from mcp.mdq.tools import _MCP_TOOLS

        for tool in _MCP_TOOLS:
            assert "stub" not in tool, f"Tool '{tool['name']}' has unexpected 'stub' key"

    def test_production_tool_statuses(self) -> None:
        """7 non-admin mdq-mcp tools have status='production'."""
        from mcp.mdq.tools import _MCP_TOOLS

        production_tools = {"search_docs", "get_chunk", "outline", "index_paths", "refresh_index", "stats", "grep_docs"}
        for tool in _MCP_TOOLS:
            if tool["name"] in production_tools:
                assert tool.get("status") == "production", f"Tool '{tool['name']}' should have status='production'"

    def test_admin_tool_statuses(self) -> None:
        """2 admin mdq-mcp tools (fts_consistency_check, fts_rebuild) have status='admin'."""
        from mcp.mdq.tools import _MCP_TOOLS

        admin_tools = {"fts_consistency_check", "fts_rebuild"}
        for tool in _MCP_TOOLS:
            if tool["name"] in admin_tools:
                assert tool.get("status") == "admin", f"Tool '{tool['name']}' should have status='admin'"

    def test_all_tools_have_status_field(self) -> None:
        """All 9 mdq-mcp tools have a 'status' field."""
        from mcp.mdq.tools import _MCP_TOOLS

        for tool in _MCP_TOOLS:
            assert "status" in tool, f"Tool '{tool['name']}' is missing 'status' field"
```

### Target file: `tests/test_mdq_metadata_consistency.py` (additional tests)

#### Procedure

Add health response metadata test.

#### Method

Direct file edit — add new test method.

#### Details

**Add after the existing tests:**
```python
class TestMdqHealthMetadataConsistency:
    """Verify mdq-mcp /health response contains no stub field."""

    def test_health_response_no_stub(self) -> None:
        """Simulate the health endpoint response and assert no 'stub' key is present."""
        # Simulate the _ok_response structure from server.py
        health_response = {
            "status": "ok",
            "ready": True,
            "dependencies": {},
            "details": {"service": "mdq-mcp"},
        }

        assert "stub" not in health_response
        assert "stub" not in health_response.get("details", {})

    def test_degraded_health_response_no_stub(self) -> None:
        """Simulate the degraded health response and assert no 'stub' key is present."""
        # Simulate the _degraded_response structure from server.py
        health_response = {
            "status": "degraded",
            "ready": False,
            "dependencies": {"index": "not_ready"},
            "details": {"service": "mdq-mcp"},
        }

        assert "stub" not in health_response
        assert "stub" not in health_response.get("details", {})
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp/mdq/tools.py` | Static import + field assertion | `uv run pytest tests/test_mdq_metadata_consistency.py::test_no_stub_keys_in_tools` | All 9 tools pass; no `stub` key found |
| `scripts/mcp/mdq/tools.py` | Status field assertion per tool | `uv run pytest tests/test_mdq_metadata_consistency.py::test_production_tool_statuses` | 7 tools `"production"`, 2 tools `"admin"` |
| `scripts/mcp/mdq/server.py` | Health response dict inspection | `uv run pytest tests/test_mdq_metadata_consistency.py::test_health_response_no_stub` | No `stub` key in response dict |
| Full test suite | Regression check | `uv run pytest tests/ -m "not integration" -q` | All tests pass, no regressions |
| Documentation consistency | rg search post-fix | `rg "stub.*mdq\|mdq.*stub\|mixed.*stub" docs/` | No results |

## Risks & Mitigations

- **Risk**: Editing `04_mcp_90` MCP-03 removes wording that AI routing systems depend on → **Mitigation**: Replace with accurate wording (production vs admin) rather than deleting; update "Notes for AI reference" section to prevent routing errors
- **Risk**: New tests in `test_mdq_metadata_consistency.py` may be tightly coupled to the exact list of tool names → **Mitigation**: Use the canonical `MDQ_TOOLS` set from `shared/tool_constants.py` as the expected set; hardcode the two admin tools separately
