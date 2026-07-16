"""tests/test_check_mcp_docs_consistency.py

Unit tests for scripts/check_mcp_docs_consistency.py — synthetic doc content,
not references to real doc files.
"""

from __future__ import annotations

from pathlib import Path

from check_mcp_docs_consistency import (
    _ACTIVE_ISSUE_ALLOWLIST,
    DocFile,
    check_active_inconsistencies,
    check_audit_log_single_format,
    check_fail_open_workflow_allowlist,
    check_live_discovery_routing,
    check_routing_authority,
    check_routing_authority_v1tools,
    check_startup_modes,
    check_stdio_active_transport,
    check_strict_validation_skips_unreachable,
    check_tool_names_routing_input,
    check_transport_error_is_error,
    check_watchdog_restarts_on_dependency_failure,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _mk_file(rel: str, lines: list[str]) -> DocFile:
    return DocFile(path=Path(f"/fake/{rel}"), rel_path=rel, lines=lines)


def _mk_issues_file() -> DocFile:
    lines = [
        "# MCP Known Issues\n",
        "## Active Issues\n",
        "### MCP-01: Issue one\n",
        "\n",
        "### MCP-02: Issue two\n",
        "## Resolved\n",
    ]
    return _mk_file("04_mcp_90_inconsistencies_and_known_issues.md", lines)


# ── check_startup_modes ──────────────────────────────────────────────────────


class TestCheckStartupModes:
    def test_valid_mode_passes(self) -> None:
        """Valid startup mode should not produce issues."""
        doc = _mk_file(
            "04_mcp_02_protocol_and_transport.md",
            [
                'startup_mode = "persistent"',
            ],
        )
        issues = check_startup_modes(Path("/fake"), [doc])
        assert not issues

    def test_invalid_mode_raises_error(self) -> None:
        """Invalid startup mode should produce ERROR."""
        doc = _mk_file(
            "04_mcp_02_protocol_and_transport.md",
            [
                'startup_mode = "external"',
            ],
        )
        issues = check_startup_modes(Path("/fake"), [doc])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"
        assert "external" in issues[0].message

    def test_no_startup_mode_no_issue(self) -> None:
        """No startup_mode declaration should not produce issues."""
        doc = _mk_file(
            "04_mcp_02_protocol_and_transport.md",
            [
                "# No startup mode here",
            ],
        )
        issues = check_startup_modes(Path("/fake"), [doc])
        assert not issues

    def test_multiple_modes_each_validated(self) -> None:
        """Multiple startup_mode declarations each validated."""
        docs = [
            _mk_file("04_mcp_02.md", ['startup_mode = "persistent"']),
            _mk_file("04_mcp_03.md", ['startup_mode = "subprocess"']),
        ]
        issues = check_startup_modes(Path("/fake"), docs)
        assert not issues

    def test_multiple_modes_one_invalid(self) -> None:
        """One invalid mode among multiple should produce one ERROR."""
        docs = [
            _mk_file("04_mcp_02.md", ['startup_mode = "persistent"']),
            _mk_file("04_mcp_03.md", ['startup_mode = "external"']),
        ]
        issues = check_startup_modes(Path("/fake"), docs)
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"


# ── check_fail_open_workflow_allowlist ────────────────────────────────────────


class TestCheckFailOpenWorkflowAllowlist:
    def test_no_fail_open_wording_no_issue(self) -> None:
        """No fail-open wording should not produce issues."""
        doc = _mk_file(
            "04_mcp_03_routing_lifecycle_and_execution.md",
            [
                "# No fail-open here",
            ],
        )
        issues = check_fail_open_workflow_allowlist(Path("/fake"), [doc])
        assert not issues

    def test_fail_open_wording_triggers_error(self) -> None:
        """Fail-open wording should produce ERROR."""
        doc = _mk_file(
            "04_mcp_03_routing_lifecycle_and_execution.md",
            [
                "# Fail-open workflow_allowlist bypasses routing authority",
            ],
        )
        issues = check_fail_open_workflow_allowlist(Path("/fake"), [doc])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"


# ── check_routing_authority ──────────────────────────────────────────────────


class TestCheckRoutingAuthority:
    def test_no_stale_language_no_issue(self) -> None:
        """No stale routing language should not produce issues."""
        doc = _mk_file(
            "04_mcp_03_routing_lifecycle_and_execution.md",
            [
                "# Routing is handled by MCP servers",
            ],
        )
        issues = check_routing_authority(Path("/fake"), [doc])
        assert not issues

    def test_stale_language_triggers_error(self) -> None:
        """Stale routing language should produce ERROR."""
        doc = _mk_file(
            "04_mcp_03_routing_lifecycle_and_execution.md",
            [
                "# ToolRegistry is the single source of truth for routing",
            ],
        )
        issues = check_routing_authority(Path("/fake"), [doc])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"


# ── check_active_inconsistencies ─────────────────────────────────────────────


class TestCheckActiveInconsistencies:
    def test_all_issued_cited_no_issue(self) -> None:
        """All active issues cited in other docs should not produce issues."""
        issues_doc = _mk_issues_file()
        other_doc = _mk_file(
            "04_mcp_02_protocol_and_transport.md",
            [
                "See MCP-01 for details.",
                "Refer to MCP-02 for more.",
            ],
        )
        issues = check_active_inconsistencies(Path("/fake"), [issues_doc, other_doc])
        assert not issues

    def test_uncited_issue_not_in_allowlist_triggers_warning(self) -> None:
        """Uncited issue not in allowlist should produce WARNING."""
        # MCP-01 is in the allowlist, so only MCP-02 would be uncited here
        # But we need to test with an issue NOT in the allowlist
        issues_doc_with_new = _mk_file(
            "04_mcp_90_inconsistencies_and_known_issues.md",
            [
                "# MCP Known Issues\n",
                "## Active Issues\n",
                "### MCP-01: Issue one\n",
                "\n",
                "### MCP-99: Uncited issue\n",
                "## Resolved\n",
            ],
        )
        other_doc = _mk_file(
            "04_mcp_02_protocol_and_transport.md",
            [
                "See MCP-01 for details.",
            ],
        )
        issues = check_active_inconsistencies(
            Path("/fake"), [issues_doc_with_new, other_doc]
        )
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert "MCP-99" in issues[0].message

    def test_uncited_issue_in_allowlist_no_warning(self) -> None:
        """Uncited issue in allowlist should not produce WARNING."""
        issues_doc = _mk_issues_file()
        # MCP-01 and MCP-02 are both uncited but MCP-01 is in the allowlist
        # MCP-02 is also in the allowlist, so no warnings expected
        other_doc = _mk_file(
            "04_mcp_02_protocol_and_transport.md",
            [
                "# No cross-references here",
            ],
        )
        issues = check_active_inconsistencies(Path("/fake"), [issues_doc, other_doc])
        assert not issues

    def test_missing_known_issues_file_returns_warning(self) -> None:
        """Missing known-issues file should produce WARNING."""
        doc = _mk_file("04_mcp_02_protocol_and_transport.md", [])
        issues = check_active_inconsistencies(Path("/fake"), [doc])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"


# ── _ACTIVE_ISSUE_ALLOWLIST ──────────────────────────────────────────────────


class TestActiveIssueAllowlist:
    def test_allowlist_contains_expected_issues(self) -> None:
        """Allowlist should contain the expected MCP issue IDs."""
        assert "MCP-01" in _ACTIVE_ISSUE_ALLOWLIST
        assert "MCP-02" in _ACTIVE_ISSUE_ALLOWLIST
        assert "MCP-04" in _ACTIVE_ISSUE_ALLOWLIST
        assert "MCP-06" in _ACTIVE_ISSUE_ALLOWLIST
        assert "MCP-07" in _ACTIVE_ISSUE_ALLOWLIST
        assert "MCP-08" in _ACTIVE_ISSUE_ALLOWLIST

    def test_allowlist_does_not_contain_resolved_issues(self) -> None:
        """Resolved issues should not be in the allowlist."""
        # MCP-03 and MCP-05 are resolved — they should NOT be in the allowlist
        assert "MCP-03" not in _ACTIVE_ISSUE_ALLOWLIST
        assert "MCP-05" not in _ACTIVE_ISSUE_ALLOWLIST


# ── check_live_discovery_routing ─────────────────────────────────────────────


class TestCheckLiveDiscoveryRouting:
    def test_no_stale_language_no_issue(self) -> None:
        """Clean line should not produce issues."""
        doc = _mk_file("04_mcp_03_routing.md", ["The registry handles routing."])
        issues = check_live_discovery_routing(Path("/fake"), [doc])
        assert not issues

    def test_stale_language_triggers_error(self) -> None:
        """Discovery-overrides-registry language should produce ERROR."""
        doc = _mk_file(
            "04_mcp_03_routing.md",
            ["discovery overrides registry for routing"],
        )
        issues = check_live_discovery_routing(Path("/fake"), [doc])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"

    def test_known_issues_file_skipped(self) -> None:
        """Known-issues file should be skipped entirely."""
        doc = _mk_file(
            "04_mcp_90_inconsistencies_and_known_issues.md",
            ["discovery overrides registry for routing"],
        )
        issues = check_live_discovery_routing(Path("/fake"), [doc])
        assert not issues


# ── check_routing_authority_v1tools ──────────────────────────────────────────


class TestCheckRoutingAuthorityV1Tools:
    def test_no_stale_language_no_issue(self) -> None:
        """Clean line should not produce issues."""
        doc = _mk_file(
            "04_mcp_03_routing.md", ["/v1/tools is used for drift detection"]
        )
        issues = check_routing_authority_v1tools(Path("/fake"), [doc])
        assert not issues

    def test_stale_language_triggers_error(self) -> None:
        """/v1/tools-as-routing-authority language should produce ERROR."""
        doc = _mk_file(
            "04_mcp_03_routing.md",
            ["/v1/tools is the routing authority"],
        )
        issues = check_routing_authority_v1tools(Path("/fake"), [doc])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"

    def test_negation_skipped(self) -> None:
        """Negated form should not produce issues."""
        doc = _mk_file(
            "04_mcp_03_routing.md",
            ["/v1/tools is NOT the routing authority"],
        )
        issues = check_routing_authority_v1tools(Path("/fake"), [doc])
        assert not issues


# ── check_tool_names_routing_input ───────────────────────────────────────────


class TestCheckToolNamesRoutingInput:
    def test_no_stale_language_no_issue(self) -> None:
        """Clean line should not produce issues."""
        doc = _mk_file("04_mcp_03_routing.md", ["tool_names is stored for audit"])
        issues = check_tool_names_routing_input(Path("/fake"), [doc])
        assert not issues

    def test_stale_language_triggers_error(self) -> None:
        """tool_names-as-routing-input language should produce ERROR."""
        doc = _mk_file(
            "04_mcp_03_routing.md",
            ["tool_names is a routing input"],
        )
        issues = check_tool_names_routing_input(Path("/fake"), [doc])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"

    def test_negation_skipped(self) -> None:
        """Negated form should not produce issues."""
        doc = _mk_file(
            "04_mcp_03_routing.md",
            ["tool_names is not a routing input"],
        )
        issues = check_tool_names_routing_input(Path("/fake"), [doc])
        assert not issues

    def test_allowlist_file_skipped(self) -> None:
        """04_mcp_90_ file should be skipped entirely."""
        doc = _mk_file(
            "04_mcp_90_inconsistencies_and_known_issues.md",
            ["tool_names is a routing input"],
        )
        issues = check_tool_names_routing_input(Path("/fake"), [doc])
        assert not issues

    def test_fenced_code_block_exempt(self) -> None:
        """Content inside fenced code block should not produce issues."""
        doc = _mk_file(
            "04_mcp_03_routing.md",
            ["```", "tool_names routing determines", "```"],
        )
        issues = check_tool_names_routing_input(Path("/fake"), [doc])
        assert not issues


# ── check_audit_log_single_format ────────────────────────────────────────────


class TestCheckAuditLogSingleFormat:
    def test_no_stale_language_no_issue(self) -> None:
        """Clean line should not produce issues."""
        doc = _mk_file("04_mcp_06_configuration.md", ["The audit log records events."])
        issues = check_audit_log_single_format(Path("/fake"), [doc])
        assert not issues

    def test_audit_kv_only_triggers_error(self) -> None:
        """audit.log key-value format language should produce ERROR."""
        doc = _mk_file(
            "04_mcp_06_configuration.md",
            ["audit.log uses key-value format only"],
        )
        issues = check_audit_log_single_format(Path("/fake"), [doc])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"

    def test_fenced_code_block_exempt(self) -> None:
        """Content inside fenced code block should not produce issues."""
        doc = _mk_file(
            "04_mcp_06_configuration.md",
            ["```", "AUDIT session=abc format=kv", "```"],
        )
        issues = check_audit_log_single_format(Path("/fake"), [doc])
        assert not issues


# ── check_transport_error_is_error ───────────────────────────────────────────


class TestCheckTransportErrorIsError:
    def test_no_stale_language_no_issue(self) -> None:
        """Clean line should not produce issues."""
        doc = _mk_file("04_mcp_03_routing.md", ["Transport errors are logged."])
        issues = check_transport_error_is_error(Path("/fake"), [doc])
        assert not issues

    def test_stale_language_triggers_warning(self) -> None:
        """HttpTransport is_error=True language should produce WARNING."""
        doc = _mk_file(
            "04_mcp_03_routing.md",
            ["HttpTransport returns is_error=True for transport failures"],
        )
        issues = check_transport_error_is_error(Path("/fake"), [doc])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"

    def test_fenced_code_block_exempt(self) -> None:
        """Content inside fenced code block should not produce issues."""
        doc = _mk_file(
            "04_mcp_03_routing.md",
            ["```", "HttpTransport returns is_error=True", "```"],
        )
        issues = check_transport_error_is_error(Path("/fake"), [doc])
        assert not issues

    def test_known_issues_file_skipped(self) -> None:
        """Known-issues file should be skipped entirely."""
        doc = _mk_file(
            "04_mcp_90_inconsistencies_and_known_issues.md",
            ["HttpTransport returns is_error=True for transport failures"],
        )
        issues = check_transport_error_is_error(Path("/fake"), [doc])
        assert not issues

    def test_japanese_negation_no_issue(self) -> None:
        """Japanese negation of the stale claim should not produce a warning."""
        doc = _mk_file(
            "04_mcp_02_03_audit-logging-and-errors.md",
            ["HttpTransport は is_error=True を直接返すことはない"],
        )
        issues = check_transport_error_is_error(Path("/fake"), [doc])
        assert not issues

    def test_japanese_affirmative_stale_still_triggers(self) -> None:
        """Japanese affirmative stale claim (no negation) should still produce a WARNING."""
        doc = _mk_file(
            "04_mcp_02_03_audit-logging-and-errors.md",
            ["HttpTransport は transport 障害時に is_error=True を返す"],
        )
        issues = check_transport_error_is_error(Path("/fake"), [doc])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"


# ── check_stdio_active_transport ─────────────────────────────────────────────


class TestCheckStdioActiveTransport:
    def test_no_stale_language_no_issue(self) -> None:
        """Clean line should not produce issues."""
        doc = _mk_file("04_mcp_03_routing.md", ["The server uses HTTP transport."])
        issues = check_stdio_active_transport(Path("/fake"), [doc])
        assert not issues

    def test_stale_language_triggers_error(self) -> None:
        """stdio reference in non-allowlisted 04_mcp_ file should produce ERROR."""
        doc = _mk_file(
            "04_mcp_03_routing.md",
            ["The stdio transport handles messages."],
        )
        issues = check_stdio_active_transport(Path("/fake"), [doc])
        assert len(issues) >= 1
        assert issues[0].severity == "ERROR"

    def test_allowlist_file_skipped(self) -> None:
        """Allowlisted file should be skipped entirely."""
        doc = _mk_file(
            "04_mcp_02_protocol_and_transport.md",
            ["The stdio transport handles messages."],
        )
        issues = check_stdio_active_transport(Path("/fake"), [doc])
        assert not issues

    def test_fenced_code_block_exempt(self) -> None:
        """Content inside fenced code block should not produce issues."""
        doc = _mk_file(
            "04_mcp_03_routing.md",
            ["```", "stdio --stdio", "```"],
        )
        issues = check_stdio_active_transport(Path("/fake"), [doc])
        assert not issues


# ── check_watchdog_restarts_on_dependency_failure ────────────────────────────


class TestCheckWatchdogRestartsOnDependencyFailure:
    def test_no_stale_language_no_issue(self) -> None:
        """Clean line should not produce issues."""
        doc = _mk_file(
            "04_mcp_06_configuration.md",
            ["The watchdog monitors HTTP status codes."],
        )
        issues = check_watchdog_restarts_on_dependency_failure(Path("/fake"), [doc])
        assert not issues

    def test_stale_language_triggers_error(self) -> None:
        """watchdog-restarts-on-dependency-failure language should produce ERROR."""
        doc = _mk_file(
            "04_mcp_06_configuration.md",
            ["watchdog restarts on every dependency failure"],
        )
        issues = check_watchdog_restarts_on_dependency_failure(Path("/fake"), [doc])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"


# ── check_strict_validation_skips_unreachable ────────────────────────────────


class TestCheckStrictValidationSkipsUnreachable:
    def test_no_stale_language_no_issue(self) -> None:
        """Clean line should not produce issues."""
        doc = _mk_file(
            "04_mcp_06_configuration.md",
            ["Strict validation raises RuntimeError on mismatch."],
        )
        issues = check_strict_validation_skips_unreachable(Path("/fake"), [doc])
        assert not issues

    def test_stale_language_triggers_error(self) -> None:
        """strict-skip-unreachable language should produce ERROR."""
        doc = _mk_file(
            "04_mcp_06_configuration.md",
            ["strict validation skip unreachable servers"],
        )
        issues = check_strict_validation_skips_unreachable(Path("/fake"), [doc])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"
