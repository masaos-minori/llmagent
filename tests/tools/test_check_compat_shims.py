"""tests/tools/test_check_compat_shims.py
Tests for tools/check_compat_shims.py.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.check_compat_shims import (
    ADR_PROHIBITED_PATTERNS,
    COMPAT_PATTERNS,
    ROOT_DIR,
    check_adr_prohibited_patterns,
    check_all,
    check_compat_patterns,
    check_doc_symbols,
    check_gateless_discovery_construction,
    check_mcp_health_reexport_import,
    check_removed_name_reintroduction,
    load_exceptions,
    main,
    validate_exceptions,
)


class TestRootDirResolution:
    """ROOT_DIR must resolve to the actual repository root.

    Regression test for a bug where an extra `.parent` made ROOT_DIR resolve
    one directory too high, causing main()'s default scan to silently see
    zero files (dirs_to_scan entries all failed their exists() guard).
    """

    def test_root_dir_resolves_to_repository_root(self) -> None:
        assert (ROOT_DIR / "scripts").exists()
        assert (ROOT_DIR / "docs").exists()
        assert (ROOT_DIR / "tests").exists()
        assert (ROOT_DIR / "tools").exists()


class TestPatternDetection:
    """Each new pattern is detected in synthetic input."""

    @pytest.mark.parametrize(
        "phrase",
        [
            "re-export stub",
            "compatibility shim",
            "existing imports continue to work",
            "backward-compatible",
            "_cast_enums",
        ],
    )
    def test_new_pattern_detected_in_synthetic_string(
        self, phrase: str, tmp_path: Path
    ) -> None:
        synthetic = tmp_path / "synthetic_test.py"
        synthetic.write_text(f"# {phrase}\n")
        content = synthetic.read_text()
        matched = any(re.search(pat, content) for pat in COMPAT_PATTERNS.values())
        assert matched, f"Pattern for '{phrase}' was not detected"

    @pytest.mark.parametrize(
        ("text", "should_match"),
        [
            ("run /mdq status", True),
            ("`/mdq`", True),
            ("/opt/llm/db/mdq.sqlite", False),
            ("mdq.sqlite", False),
            ("Logs: <log_dir>/mdq-mcp.log", False),
            ("scripts/mcp_servers/mdq/server.py", False),
        ],
    )
    def test_mdq_command_pattern_matches_command_form_only(
        self, text: str, should_match: bool
    ) -> None:
        pattern = COMPAT_PATTERNS["/mdq command"]
        assert bool(re.search(pattern, text)) is should_match

    @pytest.mark.parametrize(
        ("text", "should_match"),
        [
            ("from agent.workflow.approval_ops import x", True),
            ("request_approval(db, task_id)", True),
            ("await self._gate_approval(task)", True),
            ("raise WorkflowPendingApprovalError(a, b)", True),
            ("ctx.workflow.approval_pending = True", True),
            ("ctx.turn.pending_approval_id", True),
            ("ctx.turn.pending_approval_task_id", True),
            ("run /approve to continue", True),
            ("use `/reject`", True),
            ("event approval_requested", True),
            ("ApprovalDecisionType.APPROVED", False),
            ("audit_approval(ctx, tool, risk, args, decision)", False),
            ("log_approval_decision(ctx, outcome)", False),
            ("require_approval_for = []", False),
            ("a workflow definition with require_approval is rejected", False),
            ("CREATE TABLE IF NOT EXISTS approvals", False),
            ("status = 'pending_approval'", False),
            ("run_approval_gate(ctx)", False),
            ("/approve-docs/index.md", False),
        ],
    )
    def test_approval_gate_patterns_match_removed_names_only(
        self, text: str, should_match: bool
    ) -> None:
        matched = any(
            re.search(pattern, text)
            for key, pattern in COMPAT_PATTERNS.items()
            if "post-execution approval stage removed" in key
            or key in ("/approve command", "/reject command")
        )
        assert matched is should_match

    def test_clean_file_has_no_matches(self, tmp_path: Path) -> None:
        clean = tmp_path / "clean.py"
        clean.write_text("# This file has no compat patterns\n")
        issues = check_compat_patterns(clean.read_text(), clean, set())
        assert issues == []

    def test_allowlisted_file_skipped(self, tmp_path: Path) -> None:
        dirty = tmp_path / "allowlisted.py"
        dirty.write_text("# re-export stub for compatibility\n")
        issues = check_compat_patterns(dirty.read_text(), dirty, {dirty})
        assert issues == []


class TestAdrProhibitedPatterns:
    """The ADR-scoped check (REQ-002) fires on a seeded pattern and is
    silent otherwise; distinct from COMPAT_PATTERNS's own detection."""

    def test_seeded_pattern_detected_in_synthetic_code(self, tmp_path: Path) -> None:
        dirty = tmp_path / "synthetic.py"
        dirty.write_text("if disable_workflow:\n    pass\n")
        issues = check_adr_prohibited_patterns(dirty.read_text(), dirty, set())
        assert len(issues) == 1
        assert "ADR-001" in issues[0]

    def test_clean_file_has_no_adr_pattern_matches(self, tmp_path: Path) -> None:
        clean = tmp_path / "clean.py"
        clean.write_text("if some_other_flag:\n    pass\n")
        issues = check_adr_prohibited_patterns(clean.read_text(), clean, set())
        assert issues == []

    def test_allowlisted_file_skipped(self, tmp_path: Path) -> None:
        dirty = tmp_path / "allowlisted.py"
        dirty.write_text("if disable_workflow:\n    pass\n")
        issues = check_adr_prohibited_patterns(dirty.read_text(), dirty, {dirty})
        assert issues == []

    def test_adr001_prose_in_docs_is_not_matched(self, tmp_path: Path) -> None:
        """The Japanese ADR-001 prohibition prose must not self-trigger this
        identifier-shaped check."""
        doc = tmp_path / "adr_prose.md"
        doc.write_text(
            "Workflow無効化モードを設けない。Workflowを迂回する直接実行経路を設けない。\n"
        )
        issues = check_adr_prohibited_patterns(doc.read_text(), doc, set())
        assert issues == []

    def test_every_pattern_maps_to_a_real_adr_id(self) -> None:
        for name, (adr_id, pattern) in ADR_PROHIBITED_PATTERNS.items():
            assert re.match(r"^ADR-\d{3}$", adr_id), (
                f"'{name}' maps to malformed ADR id {adr_id!r}"
            )


class TestDirectoryPositionalArgument:
    """A directory passed as a positional file argument must be expanded into its
    contained files (mirroring the no-args scan), not crash with IsADirectoryError.
    """

    def test_directory_with_violation_is_expanded_and_flagged(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / "dirty.py").write_text("# re-export stub for compatibility\n")
        (tmp_path / "clean.py").write_text("# nothing to see here\n")
        monkeypatch.setattr(sys, "argv", ["check_compat_shims", str(tmp_path)])

        exit_code = main()

        assert exit_code == 1
        assert "dirty.py" in capsys.readouterr().err

    def test_directory_with_no_violations_returns_clean_without_crashing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / "clean.py").write_text("# nothing to see here\n")
        monkeypatch.setattr(sys, "argv", ["check_compat_shims", str(tmp_path)])

        exit_code = main()

        assert exit_code == 0

    def test_relative_directory_argument_does_not_crash(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Regression test: expanded glob results must be resolved to absolute
        paths, or filepath.relative_to(ROOT_DIR) raises ValueError for any
        relative directory argument that yields a match or allowlist check."""
        (tmp_path / "clean.py").write_text("# nothing to see here\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["check_compat_shims", "."])

        exit_code = main()

        assert exit_code == 0


def _check(content: str) -> list[str]:
    return check_compat_patterns(content, Path("scripts/test.py"), set())


class TestWorkflowEnforcementPatterns:
    """Each workflow enforcement pattern is detected in synthetic input."""

    def test_detects_workflow_mode_field_reference(self) -> None:
        assert any(
            "workflow_mode field reference" in i
            for i in _check("workflow_mode: str = 'auto'")
        )

    def test_detects_allow_startup_fallback(self) -> None:
        assert any(
            "allow_startup_fallback" in i
            for i in _check("if self.allow_startup_fallback():")
        )

    def test_detects_is_workflow_enabled(self) -> None:
        assert any(
            "is_workflow_enabled" in i
            for i in _check("if not policy.is_workflow_enabled():")
        )

    def test_detects_requires_startup_definition(self) -> None:
        assert any(
            "requires_startup_definition" in i
            for i in _check("policy.requires_startup_definition()")
        )

    def test_detects_allow_turn_fallback(self) -> None:
        assert any(
            "allow_turn_fallback" in i
            for i in _check("if policy.allow_turn_fallback():")
        )

    def test_detects_workflow_mode_disabled_string(self) -> None:
        assert any(
            "workflow_mode=disabled" in i for i in _check('workflow_mode="disabled"')
        )

    def test_detects_workflow_mode_auto_string(self) -> None:
        assert any("workflow_mode=auto" in i for i in _check('workflow_mode="auto"'))

    def test_detects_workflow_mode_disabled_log(self) -> None:
        assert any(
            "Workflow mode=disabled" in i
            for i in _check('logger.info("Workflow mode=disabled")')
        )

    def test_detects_direct_llm_path_phrase(self) -> None:
        assert any("direct LLM path" in i for i in _check("# direct LLM path fallback"))

    def test_detects_direct_execution_fallback_phrase(self) -> None:
        assert any(
            "direct-execution fallback" in i
            for i in _check("# direct-execution fallback")
        )

    def test_detects_workflow_execution_policy_import(self) -> None:
        assert any(
            "WorkflowExecutionPolicy import" in i
            for i in _check(
                "from agent.workflow_execution_policy import WorkflowExecutionPolicy"
            )
        )

    def test_detects_workflow_execution_policy_module_import(self) -> None:
        assert any(
            "workflow_execution_policy module import" in i
            for i in _check("import workflow_execution_policy")
        )

    def test_allowlisted_file_not_flagged(self) -> None:
        issues = check_compat_patterns(
            "workflow_mode: str = 'auto'",
            Path("scripts/test.py"),
            {Path("scripts/test.py")},
        )
        assert issues == []

    def test_unrelated_mode_assignment_not_flagged(self) -> None:
        issues = _check('display_mode = "compact"')
        assert not any("workflow_mode field reference" in i for i in issues)


class TestRemovedNameReintroduction:
    """check_removed_name_reintroduction() — compatterms REQ-003's
    simple-absence case: `_update_null_fill` and the ToolRouteResolver+
    server_configs co-occurrence, both scoped to docs/*.md only, both
    exempted inside historical/resolved context."""

    def test_update_null_fill_flagged_outside_historical_context(
        self, tmp_path: Path
    ) -> None:
        doc = tmp_path / "example.md"
        doc.write_text("`_update_null_fill()` is the current fallback path.\n")
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert len(issues) == 1
        assert "_update_null_fill" in issues[0]

    def test_update_null_fill_exempted_in_historical_context(
        self, tmp_path: Path
    ) -> None:
        doc = tmp_path / "example.md"
        doc.write_text(
            "**Status**: resolved\n\n"
            "This entry records that `_update_null_fill()` was removed.\n"
        )
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert issues == []

    def test_non_markdown_file_is_not_checked(self, tmp_path: Path) -> None:
        py_file = tmp_path / "example.py"
        py_file.write_text("# _update_null_fill() is current\n")
        issues = check_removed_name_reintroduction(py_file.read_text(), py_file)
        assert issues == []

    def test_tool_route_resolver_server_configs_flagged_same_section(
        self, tmp_path: Path
    ) -> None:
        doc = tmp_path / "example.md"
        doc.write_text(
            "## ToolRouteResolver\n\n"
            "- **Configuration:** accepts `server_configs` for backward "
            "compatibility.\n"
        )
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert len(issues) == 1
        assert "ToolRouteResolver+server_configs" in issues[0]

    def test_tool_route_resolver_server_configs_exempted_in_historical_section(
        self, tmp_path: Path
    ) -> None:
        doc = tmp_path / "example.md"
        doc.write_text(
            "## ToolRouteResolver (historical)\n\n"
            "- **Removed:** previously accepted `server_configs`.\n"
        )
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert issues == []

    @pytest.mark.parametrize(
        "denial",
        [
            "## ToolRouteResolver\n\n"
            "- **Config:** no `server_configs` parameter is accepted.\n",
            "## ToolRouteResolver\n\n"
            "- **Config:** No `server_configs` parameter exists.\n",
            "## ToolRouteResolver\n\n"
            "- **Config:** `server_configs` does not exist as a "
            "constructor argument.\n",
        ],
    )
    def test_tool_route_resolver_server_configs_negation_not_flagged(
        self, denial: str, tmp_path: Path
    ) -> None:
        """A `server_configs` mention that denies the stale resolver argument
        (any casing, any of the observed phrasings) documents the absence and
        must not be flagged, even though ToolRouteResolver and server_configs
        co-occur in the same section."""
        doc = tmp_path / "example.md"
        doc.write_text(denial)
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert issues == []

    def test_server_configs_alone_without_class_name_not_flagged(
        self, tmp_path: Path
    ) -> None:
        """server_configs unrelated to ToolRouteResolver (e.g. ToolExecutor's
        own, still-current field) must not be flagged."""
        doc = tmp_path / "example.md"
        doc.write_text(
            "## ToolExecutor\n\n"
            "- **Configuration:** `server_configs` is the active MCP "
            "execution configuration.\n"
        )
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert issues == []


class TestRemovedCommandNamePatterns:
    """GV-017: the four removed slash-command names are reintroduced-as-current
    only when they appear in slash-command form; ordinary words and
    historical-context mentions are exempt."""

    @pytest.mark.parametrize(
        ("name", "usage"),
        [
            ("/diff", "Run /diff to see what changed this session."),
            ("/system", "Type /system coding to switch presets."),
            ("/audit", "Use /audit tail to browse recent events."),
            ("/workflow", "Invoke /workflow to run the pipeline."),
        ],
    )
    def test_removed_command_names_flagged_as_current(
        self, name: str, usage: str, tmp_path: Path
    ) -> None:
        doc = tmp_path / "example.md"
        doc.write_text(f"{usage}\n")
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert any(name in issue for issue in issues), (
            f"Expected {name!r} to be flagged as a current-spec reintroduction"
        )

    @pytest.mark.parametrize("word", ["diff", "system", "audit", "workflow"])
    def test_bare_words_not_flagged(self, word: str, tmp_path: Path) -> None:
        """Ordinary prose uses of the removed names must not false-positive."""
        doc = tmp_path / "example.md"
        doc.write_text(
            f"This section discusses the {word} tool and its {word} behavior.\n"
        )
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert issues == []

    def test_removed_names_exempted_in_historical_context(self, tmp_path: Path) -> None:
        doc = tmp_path / "example.md"
        doc.write_text(
            "**Status**: resolved\n\n"
            "Previously you could run /diff, /system, /audit, and /workflow.\n"
        )
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert issues == []

    @pytest.mark.parametrize(
        ("text", "should_match"),
        [
            # Slash-command form — a genuine reintroduction, must be flagged.
            ("Run /diff to see what changed this session.", True),
            ("Use `/audit` tail to browse recent events.", True),
            # Path/filename/identifier substrings — the GV-017 false positives
            # that the tightened matcher must reject.
            ("`scripts/mcp_servers/audit.py` exports AuditRecord.", False),
            ("`scripts/eventbus/audit.py` writes the audit log.", False),
            ("tail -f <log_dir>/audit.log | jq .", False),
            ("`dict/system.dic` is the external Sudachi dictionary.", False),
            ("Routing/audit/Config gates unauthorized access.", False),
            ("`agent/workflow/workflow_engine.py` manages stages.", False),
            ("`tests/agent/workflow/test_workflow_loader.py` rejects it.", False),
        ],
    )
    def test_removed_slash_command_matches_command_form_only(
        self, text: str, should_match: bool, tmp_path: Path
    ) -> None:
        """GV-017: the removed slash-command names match only in command form;
        path separators, filenames, and identifier substrings must not."""
        doc = tmp_path / "example.md"
        doc.write_text(f"{text}\n")
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert (len(issues) > 0) == should_match


class TestCheckAllRemovedNamesGating:
    """check_all()'s `include_removed_names` defaults to False so the
    existing .pre-commit-config.yaml wiring (a bare invocation with no
    flags) is unaffected by this new, currently-non-compliant check."""

    def test_default_does_not_include_removed_names_check(self, tmp_path: Path) -> None:
        doc = tmp_path / "example.md"
        doc.write_text("`_update_null_fill()` is the current fallback path.\n")
        issues = check_all(doc.read_text(), doc, allowlist=set())
        assert issues == []

    def test_opt_in_includes_removed_names_check(self, tmp_path: Path) -> None:
        doc = tmp_path / "example.md"
        doc.write_text("`_update_null_fill()` is the current fallback path.\n")
        issues = check_all(
            doc.read_text(), doc, allowlist=set(), include_removed_names=True
        )
        assert len(issues) == 1


class TestManifestValidation:
    """validate_exceptions() enforces the manifest schema (REQ-002): required
    fields, a known category, a parseable non-past expires date, and unique ids.
    Each defect prints to stderr and raises SystemExit(1) naming the id."""

    def _entry(self, **overrides: str) -> str:
        fields = {
            "id": "test-id",
            "path": "tests/agent/test_x.py",
            "reason": "because",
            "owner": "Repository owner",
            "expires": "2027-01-01",
            "removal_condition": "when done",
            "category": "fixture",
        }
        fields.update(overrides)
        body = "[[compatibility_exceptions]]\n"
        for key, value in fields.items():
            body += f'{key} = "{value}"\n'
        return body

    def _write(self, tmp_path: Path, body: str) -> Path:
        path = tmp_path / "compat_exceptions.toml"
        path.write_text(body)
        return path

    def test_valid_manifest_passes(self, tmp_path: Path) -> None:
        path = self._write(tmp_path, self._entry())
        entries, _, _ = load_exceptions(path)
        validate_exceptions(entries)  # must not raise

    def test_missing_field_fails_naming_id(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = self._write(
            tmp_path,
            self._entry(reason=""),  # drop reason via empty string
        )
        # _entry builds `reason = ""`; load then validate.
        entries, _, _ = load_exceptions(path)
        with pytest.raises(SystemExit) as exc:
            validate_exceptions(entries)
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "test-id" in err
        assert "reason" in err

    def test_unknown_category_fails_naming_id(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = self._write(tmp_path, self._entry(category="bogus"))
        entries, _, _ = load_exceptions(path)
        with pytest.raises(SystemExit) as exc:
            validate_exceptions(entries)
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "test-id" in err
        assert "bogus" in err

    def test_unparseable_date_fails_naming_id(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = self._write(tmp_path, self._entry(expires="not-a-date"))
        entries, _, _ = load_exceptions(path)
        with pytest.raises(SystemExit) as exc:
            validate_exceptions(entries)
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "test-id" in err

    def test_expired_date_fails_naming_id(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = self._write(tmp_path, self._entry(expires="2000-01-01"))
        entries, _, _ = load_exceptions(path)
        with pytest.raises(SystemExit) as exc:
            validate_exceptions(entries)
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "test-id" in err

    def test_duplicate_id_fails_naming_id(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        body = self._entry(id="dup") + "\n" + self._entry(id="dup")
        path = self._write(tmp_path, body)
        entries, _, _ = load_exceptions(path)
        with pytest.raises(SystemExit) as exc:
            validate_exceptions(entries)
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "dup" in err


class TestManifestParity:
    """The live manifest holds exactly the 21 paths that still produce findings
    under check_all(..., allowlist=set(), include_removed_names=True)."""

    def test_loaded_paths_match_needed_paths(self) -> None:
        _, allowlist, _ = load_exceptions(ROOT_DIR / "tools" / "compat_exceptions.toml")
        expected = {
            ROOT_DIR / "docs/22_mcp/mcp_00_document-guide.md",
            ROOT_DIR / "docs/22_mcp/mcp_07_tool_schema_export_policy.md",
            ROOT_DIR
            / "docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md",
            ROOT_DIR / "scripts/shared/tool_registry.py",
            ROOT_DIR / "tests/agent/commands/test_cmd_registry_note_removal.py",
            ROOT_DIR / "tests/agent/commands/test_removed_commands.py",
            ROOT_DIR / "tests/agent/services/test_mcp_tool_discovery.py",
            ROOT_DIR / "tests/agent/services/test_mcp_tool_discovery_posture_gate.py",
            ROOT_DIR / "tests/agent/shared/test_startup_validation_pipeline.py",
            ROOT_DIR / "tests/agent/test_rag_get_cfg.py",
            ROOT_DIR / "tests/agent/test_startup_mcp_starter.py",
            ROOT_DIR / "tests/conftest.py",
            ROOT_DIR / "tests/db/test_create_schema.py",
            ROOT_DIR / "tests/mcp_servers/rag_pipeline/test_mcp_rag_pipeline.py",
            ROOT_DIR
            / "tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py",
            ROOT_DIR / "tests/mcp_servers/test_mcp_tool_schema_exports.py",
            ROOT_DIR / "tests/shared/test_tool_registry.py",
            ROOT_DIR / "tests/shared/test_tool_registry_counts.py",
            ROOT_DIR / "tests/shared/test_tool_registry_reset_protection.py",
            ROOT_DIR / "tests/tools/test_check_compat_shims.py",
            ROOT_DIR / "tools/check_compat_shims.py",
        }
        assert allowlist == expected
        assert len(expected) == 21
        assert all(p.exists() for p in allowlist)


class TestDocSymbolExitCode:
    """--check-doc-symbols findings are blocking: each one fails the run."""

    def _run(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        findings: list[SimpleNamespace],
    ) -> int:
        (tmp_path / "clean.py").write_text("# nothing to see here\n")
        monkeypatch.setattr(
            "tools.check_compat_shims.check_doc_symbols", lambda *_a, **_k: findings
        )
        monkeypatch.setattr(
            sys,
            "argv",
            ["check_compat_shims", "--check-doc-symbols", str(tmp_path)],
        )
        return main()

    def test_finding_fails_the_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        finding = SimpleNamespace(file="docs/x.md", line_no=3, message="stale `f()`")
        assert self._run(tmp_path, monkeypatch, [finding]) == 1

    def test_no_finding_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert self._run(tmp_path, monkeypatch, []) == 0


class TestDocSymbolStage:
    """check_doc_symbols() drops names defined under tools/
    and manifest allowances, reports genuine stale references, and skips
    historical-context lines. The live corpus is clean once allowances apply.

    NOTE: check_function_references() bails out when repo_root has no scripts/
    directory (extract_defined_function_names() returns an empty index), so every
    temp-repo test below creates an empty scripts/ first.
    """

    def _docs_dir(self, tmp_path: Path) -> Path:
        docs = tmp_path / "docs"
        docs.mkdir()
        return docs

    def _ensure_repo(self, tmp_path: Path) -> None:
        (tmp_path / "scripts").mkdir(exist_ok=True)

    def test_live_manifest_is_clean(self) -> None:
        _, _, allowances = load_exceptions(
            ROOT_DIR / "tools" / "compat_exceptions.toml"
        )
        assert check_doc_symbols(ROOT_DIR, ROOT_DIR / "docs", allowances) == []

    def test_stale_reference_reported(self, tmp_path: Path) -> None:
        self._ensure_repo(tmp_path)
        docs = self._docs_dir(tmp_path)
        (docs / "example.md").write_text("Call `nonexistent_symbol()` to proceed.\n")
        issues = check_doc_symbols(tmp_path, docs, frozenset())
        assert len(issues) == 1
        assert "nonexistent_symbol" in issues[0].message

    def test_scripts_defined_function_not_reported(self, tmp_path: Path) -> None:
        self._ensure_repo(tmp_path)
        docs = self._docs_dir(tmp_path)
        (docs / "example.md").write_text("Call `existing_script_func()`.\n")
        scripts = tmp_path / "scripts"
        (scripts / "mod.py").write_text("def existing_script_func():\n    pass\n")
        assert check_doc_symbols(tmp_path, docs, frozenset()) == []

    def test_historical_context_line_not_reported(self, tmp_path: Path) -> None:
        self._ensure_repo(tmp_path)
        docs = self._docs_dir(tmp_path)
        (docs / "example.md").write_text(
            "**Status**: resolved\n\n`old_func()` was removed.\n"
        )
        assert check_doc_symbols(tmp_path, docs, frozenset()) == []

    def test_allowance_not_reported(self, tmp_path: Path) -> None:
        self._ensure_repo(tmp_path)
        docs = self._docs_dir(tmp_path)
        (docs / "example.md").write_text("Call `allowed_name()`.\n")
        assert check_doc_symbols(tmp_path, docs, frozenset({"allowed_name"})) == []

    def test_tools_defined_function_not_reported(self, tmp_path: Path) -> None:
        self._ensure_repo(tmp_path)
        docs = self._docs_dir(tmp_path)
        (docs / "example.md").write_text("Call `tool_local_func()`.\n")
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        (tools_dir / "helper.py").write_text("def tool_local_func():\n    pass\n")
        assert check_doc_symbols(tmp_path, docs, frozenset()) == []


class TestMcpHealthReexportImport:
    """AST rule: shared.mcp_config must not be a source of Health names."""

    def test_multiline_reexport_import_is_flagged(self) -> None:
        content = (
            "from shared.mcp_config import (\n"
            "    McpServerConfig,\n"
            "    McpServerHealthRegistry,\n"
            "    McpServerHealthState,\n"
            ")\n"
        )
        issues = check_mcp_health_reexport_import(content, Path("scripts/test.py"))
        assert len(issues) == 2
        assert "shared.mcp_config" in issues[0] and ":1:" in issues[0]

    def test_canonical_import_is_clean(self) -> None:
        content = "from shared.mcp_health import McpServerHealthState\n"
        assert check_mcp_health_reexport_import(content, Path("scripts/test.py")) == []

    def test_other_mcp_config_names_are_clean(self) -> None:
        content = "from shared.mcp_config import McpServerConfig, TransportType\n"
        assert check_mcp_health_reexport_import(content, Path("scripts/test.py")) == []

    def test_non_python_file_is_skipped(self) -> None:
        content = "from shared.mcp_config import McpServerHealthState\n"
        assert check_mcp_health_reexport_import(content, Path("docs/test.md")) == []


class TestGatelessDiscoveryConstruction:
    """AST rule: McpToolDiscoveryService requires the posture_gates argument."""

    def test_gateless_construction_is_flagged(self) -> None:
        content = "svc = McpToolDiscoveryService(ctx)\n"
        issues = check_gateless_discovery_construction(content, Path("scripts/test.py"))
        assert len(issues) == 1
        assert "posture_gates" in issues[0] and ":1:" in issues[0]

    def test_keyword_gates_construction_is_clean(self) -> None:
        content = "svc = McpToolDiscoveryService(ctx, posture_gates=gates)\n"
        assert (
            check_gateless_discovery_construction(content, Path("scripts/test.py"))
            == []
        )

    def test_positional_gates_construction_is_clean(self) -> None:
        content = "svc = McpToolDiscoveryService(ctx, gates)\n"
        assert (
            check_gateless_discovery_construction(content, Path("scripts/test.py"))
            == []
        )

    def test_multiline_gateless_construction_is_flagged(self) -> None:
        content = "svc = McpToolDiscoveryService(\n    ctx,\n)\n"
        issues = check_gateless_discovery_construction(content, Path("tests/test.py"))
        assert len(issues) == 1


class TestNewAstRulesWiring:
    def test_check_all_runs_both_new_rules_by_default(self) -> None:
        content = (
            "from shared.mcp_config import McpServerHealthState\n"
            "svc = McpToolDiscoveryService(ctx)\n"
        )
        issues = check_all(content, Path("scripts/test.py"), allowlist=set())
        assert any("removed shared.mcp_config re-export path" in i for i in issues)
        assert any("without posture_gates" in i for i in issues)

    def test_allowlisted_negative_test_file_is_exempt(self) -> None:
        content = "with pytest.raises(TypeError):\n    McpToolDiscoveryService(ctx)\n"
        path = Path("tests/agent/services/test_mcp_tool_discovery_posture_gate.py")
        assert check_all(content, path, allowlist={path}) == []
