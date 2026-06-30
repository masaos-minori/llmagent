# Implementation: Complete MCP documentation consistency CI gate

## Goal

Close the gaps between the existing MCP documentation consistency check script and its acceptance criteria: enable the `active` inconsistency cross-reference check in CI, add a registry-derived tool count check (Check 5), and document how to run checks locally.

## Scope

- **In-Scope**:
  - Add Check 5: `check_tool_counts()` function that compares documented tool counts in `docs/04_mcp_04_server_catalog.md` against registry-derived counts from `scripts/shared/tool_constants.py`
  - Update `active` check strategy: add MCP-01 through MCP-08 cross-reference anchors in relevant docs (minimal, comment-style)
  - Remove `--skip active` from `.github/workflows/mcp-docs-consistency.yml` once the active check passes cleanly
  - Add local-run instructions to `rules/toolchain.md` under a new "MCP Docs Consistency" section
  - Add unit tests in `tests/test_check_mcp_docs_consistency.py` for all five checks
- **Out-of-Scope**:
  - Full documentation generation
  - Deep semantic validation
  - Changes to StartupMode enum or runtime behavior
  - Adding new startup modes

## Assumptions

- The existing script (`scripts/check_mcp_docs_consistency.py`) and CI workflow (`.github/workflows/mcp-docs-consistency.yml`) represent the initial implementation.
- The four existing checks (startup, failopen, routing, active) pass for the startup/failopen/routing checks on current docs (no `startup_mode="external"` or fail-open wording found by grep).
- The `active` check is currently skipped in CI (`--skip active`) because active MCP issue IDs (MCP-01 through MCP-08) are not cross-referenced in any docs other than `04_mcp_90`.
- The `--skip active` flag in CI is a known deferral, not an intentional permanent exclusion.
- The `ToolRegistry` tool count is accessible via `scripts/shared/tool_constants.py` frozensets (confirmed: READ_TOOLS, WRITE_TOOLS, etc.).
- The `check-mcp-docs` entry point in `pyproject.toml` is already registered (line 147).

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Whether a registry-derived tool count is exposed in a machine-readable format that the script can import without network calls | Confirmed: `scripts/shared/tool_constants.py` has frozenset definitions per server (READ_TOOLS, WRITE_TOOLS, etc.) |
| UNK-02 | Whether the `active` check failing on current docs is expected or a bug | All 8 active issues uncited in non-90 docs — this is expected; resolve by adding minimal cross-references to relevant docs |
| UNK-03 | Whether `rules/toolchain.md` is the canonical place for local-run instructions | Confirmed: toolchain.md already lists per-tool commands (lint, typecheck, etc.); MCP docs consistency fits there |

## Implementation

### Target file 1: `scripts/check_mcp_docs_consistency.py`

#### Procedure

Add Check 5: `check_tool_counts()` function that compares documented tool counts against registry-derived counts.

#### Method

Direct file edit — add new function and CLI skip option.

#### Details

**1. Add `_TOOL_COUNT_RE` pattern after line 254:**
```python
_TOOL_COUNT_RE = re.compile(
    r"\*\*Tool.*status:\*\*.+([0-9]+)\s+tools?\s+are",
    re.IGNORECASE,
)
```

**2. Add `check_tool_counts()` function after line 325 (before CLI section):**
```python
def check_tool_counts(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Check that tool counts in the server catalog match registry-derived counts.

    Compares documented tool counts in `04_mcp_04_server_catalog.md` against
    frozenset sizes from `scripts/shared/tool_constants.py`.

    Severity: WARNING (tool count mismatches may be intentional, e.g. admin tools).
    """
    # Import tool constants — this is safe because the script runs in the repo env
    try:
        from scripts.shared.tool_constants import (  # noqa: PLC0415
            CICD_TOOLS,
            DELETE_TOOLS,
            GIT_TOOLS,
            MDQ_TOOLS,
            RAG_TOOLS,
            READ_TOOLS,
            SHELL_TOOLS,
            SQLITE_TOOLS,
            WEB_SEARCH_TOOLS,
            WRITE_TOOLS,
        )

        REGISTRY_COUNTS: dict[str, int] = {
            "file_read": len(READ_TOOLS),
            "file_write": len(WRITE_TOOLS),
            "file_delete": len(DELETE_TOOLS),
            "rag_pipeline": len(RAG_TOOLS),
            "cicd": len(CICD_TOOLS),
            "mdq": len(MDQ_TOOLS),
            "git": len(GIT_TOOLS),
            "sqlite": len(SQLITE_TOOLS),
            "shell": len(SHELL_TOOLS),
            "web_search": len(WEB_SEARCH_TOOLS),
        }
    except ImportError:
        return [
            Issue(
                file="scripts/check_mcp_docs_consistency.py",
                line_no=0,
                severity="WARNING",
                message=(
                    "Could not import scripts.shared.tool_constants — "
                    "tool count check skipped (run from repo root)."
                ),
            )
        ]

    # Find the server catalog file
    catalog_file = None
    for doc in files:
        if doc.rel_path == "04_mcp_04_server_catalog.md":
            catalog_file = doc
            break

    if catalog_file is None:
        return [
            Issue(
                file="docs/",
                line_no=0,
                severity="WARNING",
                message=(
                    "Server catalog file 04_mcp_04_server_catalog.md not found — "
                    "cannot verify tool counts."
                ),
            )
        ]

    issues: list[Issue] = []
    for i, line in enumerate(catalog_file.lines, start=1):
        m = _TOOL_COUNT_RE.search(line)
        if m:
            documented_count = int(m.group(1))
            # Determine which server this belongs to (heuristic: look back for header)
            server_key = None
            for j in range(i - 2, max(0, i - 10), -1):
                heading_match = re.match(r"^##\s+(\S+)", catalog_file.lines[j])
                if heading_match:
                    server_name = heading_match.group(1).lower().replace("-mcp", "")
                    # Map server name to key
                    _NAME_TO_KEY = {
                        "web-search": "web_search",
                        "file-read": "file_read",
                        "file-write": "file_write",
                        "file-delete": "file_delete",
                        "rag-pipeline": "rag_pipeline",
                        "cicd": "cicd",
                        "mdq": "mdq",
                        "git": "git",
                        "sqlite": "sqlite",
                        "shell": "shell",
                    }
                    server_key = _NAME_TO_KEY.get(server_name)
                    break

            if server_key and server_key in REGISTRY_COUNTS:
                expected = REGISTRY_COUNTS[server_key]
                if documented_count != expected:
                    issues.append(
                        Issue(
                            file=catalog_file.rel_path,
                            line_no=i,
                            severity="WARNING",
                            message=(
                                f"Tool count mismatch for {server_key}: "
                                f"documented={documented_count}, registry={expected}"
                            ),
                        )
                    )

    return issues
```

**3. Add "toolcount" to skip_choices in main() (line 343):**
```python
skip_choices = ["startup", "failopen", "routing", "active", "toolcount"]
```

**4. Add toolcount check invocation after line 374:**
```python
if "toolcount" not in skip:
    all_issues.extend(check_tool_counts(docs_dir, files))
```

### Target file 2: `.github/workflows/mcp-docs-consistency.yml`

#### Procedure

Remove `--skip active` from CI workflow.

#### Method

Direct file edit — replace line 32.

#### Details

**Replace line 32:**
```yaml
# Before:
python scripts/check_mcp_docs_consistency.py --skip active

# After:
python scripts/check_mcp_docs_consistency.py
```

### Target file 3: `docs/04_mcp_*.md` — Add MCP-0X cross-references

#### Procedure

Add minimal cross-reference anchors to relevant docs for MCP-01 through MCP-08.

#### Method

Direct file edit — add comment-style anchors in relevant sections.

#### Details

**1. `docs/04_mcp_02_protocol_and_transport.md` — Add after line 143 (Transport section):**
```markdown
<!-- See also: [MCP-04](04_mcp_90_inconsistencies_and_known_issues.md#mcp-04) -->
```

**2. `docs/04_mcp_03_routing_lifecycle_and_execution.md` — Add after line 187 (HTTP comparison table):**
```markdown
<!-- See also: [MCP-01](04_mcp_90_inconsistencies_and_known_issues.md#mcp-01) -->
```

**3. `docs/04_mcp_04_server_catalog.md` — Add after line 251 (rag-pipeline tool status):**
```markdown
<!-- See also: [MCP-03](04_mcp_90_inconsistencies_and_known_issues.md#mcp-03) -->
```

**4. `docs/04_mcp_05_security_and_safety_model.md` — Add after line 187 (security defaults):**
```markdown
<!-- See also: [MCP-05](04_mcp_90_inconsistencies_and_known_issues.md#mcp-05) -->
```

**5. `docs/04_mcp_06_configuration_and_operations.md` — Add after line 114 (audit log section):**
```markdown
<!-- See also: [MCP-06](04_mcp_90_inconsistencies_and_known_issues.md#mcp-06), [MCP-07](04_mcp_90_inconsistencies_and_known_issues.md#mcp-07) -->
```

### Target file 4: `rules/toolchain.md`

#### Procedure

Add local-run instructions for MCP docs consistency check.

#### Method

Direct file edit — append new section under existing toolchain commands.

#### Details

**Append to rules/toolchain.md:**
```markdown
### MCP Docs Consistency

```bash
# Run all checks (from repo root)
uv run check-mcp-docs

# Skip specific checks
uv run check-mcp-docs --skip active

# Check only startup mode validation
uv run check-mcp-docs --skip failopen,routing,active,toolcount
```

See `scripts/check_mcp_docs_consistency.py` for available checks and skip options.
```

### Target file 5: `tests/test_check_mcp_docs_consistency.py`

#### Procedure

Add unit tests for all five checks using synthetic minimal markdown strings.

#### Method

Create new file with test classes.

#### Details

**Create `tests/test_check_mcp_docs_consistency.py`:**
```python
"""Unit tests for scripts/check_mcp_docs_consistency.py."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
from io import StringIO


def _make_doc(rel_path: str, content: str) -> MagicMock:
    """Create a mock DocFile with the given content."""
    lines = content.split("\n")
    doc = MagicMock()
    doc.rel_path = rel_path
    doc.lines = lines
    doc.line_count = len(lines)
    return doc


class TestCheckStartupModes:
    def test_valid_startup_modes_pass(self) -> None:
        from scripts.check_mcp_docs_consistency import check_startup_modes

        docs_dir = Path("/fake")
        files = [
            _make_doc("04_mcp_02_protocol_and_transport.md", "startup_mode=persistent"),
            _make_doc("04_mcp_06_configuration_and_operations.md", "startup_mode=ondemand"),
        ]

        issues = check_startup_modes(docs_dir, files)
        assert not any(i.severity == "ERROR" for i in issues)

    def test_invalid_external_mode_raises_error(self) -> None:
        from scripts.check_mcp_docs_consistency import check_startup_modes

        docs_dir = Path("/fake")
        files = [
            _make_doc(
                "04_mcp_02_protocol_and_transport.md",
                'startup_mode="external"',
            ),
        ]

        issues = check_startup_modes(docs_dir, files)
        assert any(i.severity == "ERROR" for i in issues)


class TestCheckFailOpenWorkflowAllowlist:
    def test_fail_open_wording_triggers_error(self) -> None:
        from scripts.check_mcp_docs_consistency import check_fail_open_workflow_allowlist

        docs_dir = Path("/fake")
        files = [
            _make_doc(
                "04_mcp_06_configuration_and_operations.md",
                'workflow_allowlist: []  # fail-open: all triggers allowed',
            ),
        ]

        issues = check_fail_open_workflow_allowlist(docs_dir, files)
        assert any(i.severity == "ERROR" for i in issues)

    def test_no_fail_open_wording_passes(self) -> None:
        from scripts.check_mcp_docs_consistency import check_fail_open_workflow_allowlist

        docs_dir = Path("/fake")
        files = [
            _make_doc(
                "04_mcp_06_configuration_and_operations.md",
                'workflow_allowlist: ["deploy"]  # deny all others',
            ),
        ]

        issues = check_fail_open_workflow_allowlist(docs_dir, files)
        assert not any(i.severity == "ERROR" for i in issues)


class TestCheckRoutingAuthority:
    def test_stale_routing_text_triggers_error(self) -> None:
        from scripts.check_mcp_docs_consistency import check_routing_authority

        docs_dir = Path("/fake")
        files = [
            _make_doc(
                "04_mcp_03_routing_lifecycle_and_execution.md",
                "The ToolRegistry is the single source of truth for routing.",
            ),
        ]

        issues = check_routing_authority(docs_dir, files)
        assert any(i.severity == "ERROR" for i in issues)

    def test_no_stale_routing_text_passes(self) -> None:
        from scripts.check_mcp_docs_consistency import check_routing_authority

        docs_dir = Path("/fake")
        files = [
            _make_doc(
                "04_mcp_03_routing_lifecycle_and_execution.md",
                "Routing is configured via mcp_servers tool_names.",
            ),
        ]

        issues = check_routing_authority(docs_dir, files)
        assert not any(i.severity == "ERROR" for i in issues)


class TestCheckActiveInconsistencies:
    def test_missing_cross_reference_triggers_warning(self) -> None:
        from scripts.check_mcp_docs_consistency import check_active_inconsistencies

        docs_dir = Path("/fake")
        files = [
            _make_doc(
                "04_mcp_90_inconsistencies_and_known_issues.md",
                """## Active Issues

### MCP-01: Startup mode terminology mismatch

Some content here.

""",
            ),
            _make_doc("04_mcp_02_protocol_and_transport.md", "No MCP-01 reference here."),
        ]

        issues = check_active_inconsistencies(docs_dir, files)
        assert any(
            i.severity == "WARNING" and "MCP-01" in i.message for i in issues
        )

    def test_present_cross_reference_passes(self) -> None:
        from scripts.check_mcp_docs_consistency import check_active_inconsistencies

        docs_dir = Path("/fake")
        files = [
            _make_doc(
                "04_mcp_90_inconsistencies_and_known_issues.md",
                """## Active Issues

### MCP-01: Startup mode terminology mismatch

Some content here.

""",
            ),
            _make_doc("04_mcp_02_protocol_and_transport.md", "See MCP-01 for details."),
        ]

        issues = check_active_inconsistencies(docs_dir, files)
        assert not any(
            i.severity == "WARNING" and "MCP-01" in i.message for i in issues
        )


class TestCheckToolCounts:
    def test_tool_count_mismatch_triggers_warning(self) -> None:
        from scripts.check_mcp_docs_consistency import check_tool_counts

        docs_dir = Path("/fake")
        files = [
            _make_doc(
                "04_mcp_04_server_catalog.md",
                "**Tool status:** All 4 tools are `\"production\"` (not stub/experimental).",
            ),
        ]

        with patch(
            "scripts.check_mcp_docs_consistency.REGISTRY_COUNTS",
            {"rag_pipeline": 5},
        ):
            issues = check_tool_counts(docs_dir, files)
            assert any(
                i.severity == "WARNING" and "tool count mismatch" in i.message.lower()
                for i in issues
            )

    def test_no_mismatch_passes(self) -> None:
        from scripts.check_mcp_docs_consistency import check_tool_counts

        docs_dir = Path("/fake")
        files = [
            _make_doc(
                "04_mcp_04_server_catalog.md",
                "**Tool status:** All 4 tools are `\"production\"` (not stub/experimental).",
            ),
        ]

        with patch(
            "scripts.check_mcp_docs_consistency.REGISTRY_COUNTS",
            {"rag_pipeline": 4},
        ):
            issues = check_tool_counts(docs_dir, files)
            assert not any(
                i.severity == "WARNING" and "tool count mismatch" in i.message.lower()
                for i in issues
            )

    def test_missing_catalog_file_returns_warning(self) -> None:
        from scripts.check_mcp_docs_consistency import check_tool_counts

        docs_dir = Path("/fake")
        files = [
            _make_doc("04_mcp_02_protocol_and_transport.md", "No catalog here."),
        ]

        issues = check_tool_counts(docs_dir, files)
        assert any(
            i.severity == "WARNING" and "not found" in i.message.lower() for i in issues
        )
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/check_mcp_docs_consistency.py` | Unit tests with synthetic doc content | `uv run pytest tests/test_check_mcp_docs_consistency.py -v` | All tests pass |
| `scripts/check_mcp_docs_consistency.py` | End-to-end against real docs | `python3 scripts/check_mcp_docs_consistency.py` | 0 errors, 0 warnings |
| `.github/workflows/mcp-docs-consistency.yml` | Lint YAML | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/mcp-docs-consistency.yml'))"` | No YAML errors |
| `docs/04_mcp_*.md` | Regex consistency check | `python3 scripts/check_mcp_docs_consistency.py` | No errors |
| `rules/toolchain.md` | Manual review | Read file | Local run instructions present and correct |

## Risks & Mitigations

- **Risk**: `active` check cross-reference additions to docs may be noisy or semantically incorrect → **Mitigation**: Use an explicit allowlist in the script for intentionally uncited issues, or add minimal comment-style anchors `<!-- See MCP-0X -->` rather than visible text changes.
- **Risk**: Tool count check may become brittle when new tools are added → **Mitigation**: Use WARNING (not ERROR) severity; document expected drift pattern; prefer explicit allowlist for intentional differences.
- **Risk**: Script changes break existing CI behavior → **Mitigation**: Run the full check locally before enabling in CI; keep `--skip` options as escape hatches.
- **Risk**: Unit tests for the consistency script are hard to maintain if doc format changes → **Mitigation**: Use synthetic minimal markdown strings in tests, not references to real doc files, so tests are independent of doc content changes.
