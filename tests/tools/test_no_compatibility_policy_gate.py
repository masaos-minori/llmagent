"""tests/tools/test_no_compatibility_policy_gate.py

Repository-wide no-compatibility-policy gate (plan 20261107-064415 REQ-007,
AC-002/AC-004/AC-005/AC-007). Retired-name literals never appear in this file:
every retired name and phrase is derived programmatically from the checker
module, so the gate and the checker cannot silently desynchronize.
"""

from __future__ import annotations

import inspect
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import check_compat_shims as checker
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "tools" / "compat_exceptions.toml"

# Derived from the checker (single source of truth): every consolidated name
# and phrase the policy forbids.
COMPAT_PATTERNS: dict[str, str] = dict(checker.COMPAT_PATTERNS)
DOC_CLAIM_PATTERNS: dict[str, re.Pattern[str]] = dict(checker._REMOVED_NAME_PATTERNS)


def _scan_flags() -> tuple[list[str], list[str]]:
    """Run the checker's own scan pipeline over the live tree and return
    (flagged_paths, aggregated findings)."""
    entries, allowlist, _ = checker.load_exceptions(MANIFEST)
    checked = [
        *REPO_ROOT.glob("scripts/**/*.py"),
        *REPO_ROOT.glob("scripts/**/*.md"),
        *REPO_ROOT.glob("docs/**/*.md"),
        *REPO_ROOT.glob("tests/**/*.py"),
        *REPO_ROOT.glob("tests/**/*.md"),
        *(
            p
            for p in REPO_ROOT.glob("tools/**/*.py")
            if p != REPO_ROOT / "tools" / "check_compat_shims.py"
        ),
    ]
    flagged: list[str] = []
    findings: list[str] = []
    for path in sorted(set(checked)):
        issues = checker.check_all(
            path.read_text(encoding="utf-8"),
            path,
            allowlist,
            include_removed_names=True,
        )
        if issues:
            flagged.append(str(path.relative_to(REPO_ROOT)))
            findings.extend(issues)
    return flagged, findings


class TestProductionExceptionZero:
    """AC-002: the manifest holds only `fixture` exemptions; no production-
    category entry (and no id shaped like one) is present."""

    def _entries(self) -> list[dict[str, str]]:
        data = tomllib.load(MANIFEST.open("rb"))
        return list(data.get("compatibility_exceptions", []))

    def test_all_entries_are_fixture_category(self) -> None:
        entries = self._entries()
        assert entries, "manifest must not be empty"
        bad = [e["id"] for e in entries if e["category"] != "fixture"]
        assert bad == []

    def test_no_migration_shaped_ids(self) -> None:
        for entry in self._entries():
            assert not entry["id"].startswith("migration-")
            assert not entry["id"].startswith("compatibility-")

    def test_checker_exemption_is_not_an_entry(self) -> None:
        data = tomllib.load(MANIFEST.open("rb"))
        checker_path = "tools/check_compat_shims.py"
        assert all(e["path"] != checker_path for e in self._entries())
        self_ref = data.get("checker_self_reference", {})
        assert checker_path in self_ref.get("paths", [])


class TestNoLiveReferences:
    """AC-004: zero live references to the consolidated retired names outside
    fixture-manifest paths (done/ archives and the checker itself excluded)."""

    def test_zero_findings_across_live_tree(self) -> None:
        flagged, findings = _scan_flags()
        assert flagged == [], findings


class TestMandatoryConsumerNack:
    """AC-005: the mandatory-consumer NACK signature (post-compatrm003)."""

    def test_consumer_id_is_required(self) -> None:
        from eventbus.delivery_repo import nack_event

        params = inspect.signature(nack_event).parameters
        assert "consumer_id" in params
        assert params["consumer_id"].default is inspect.Parameter.empty


class TestAuthzGenerationOnly:
    """AC-007: the EventBus auth surface exposes the single generation object
    and no eventbus module matches any consolidated legacy pattern."""

    def test_authz_generation_exposed(self) -> None:
        from eventbus.auth import AuthzGeneration

        assert inspect.isclass(AuthzGeneration)

    def test_no_legacy_auth_state_in_eventbus(self) -> None:
        compiled = [re.compile(p) for p in COMPAT_PATTERNS.values()]
        offenders: list[str] = []
        for path in sorted(REPO_ROOT.glob("scripts/eventbus/*.py")):
            text = path.read_text(encoding="utf-8")
            for pattern in compiled:
                match = pattern.search(text)
                if match:
                    offenders.append(f"{path.name}: {match.group(0)!r}")
        assert offenders == []


class TestCheckerBlocking:
    """AC-006 rotation proof: the checker blocks at repo root with zero
    findings, a sandbox fixture is rejected when its exemption entry is
    deleted, and passes again when the entry is restored."""

    _SENTENCE = (
        "The workflow database migrates forward on startup to the target schema.\n"
    )

    def test_repo_root_run_passes(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.check_compat_shims",
                "--check-removed-names",
                "--check-doc-symbols",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def _sandbox(self, tmp_path: Path) -> Path:
        (tmp_path / "tools").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / "tools" / "check_compat_shims.py", tmp_path / "tools")
        shutil.copy(MANIFEST, tmp_path / "tools" / "compat_exceptions.toml")
        fixture_doc = tmp_path / "docs" / "sandbox_fixture.md"
        fixture_doc.write_text(self._SENTENCE)
        return fixture_doc

    @staticmethod
    def _entry_block() -> str:
        return (
            "[[compatibility_exceptions]]\n"
            'id = "sandbox-fixture-doc"\n'
            'path = "docs/sandbox_fixture.md"\n'
            'reason = "sandbox fixture carrying a claim phrase as fixture data"\n'
            'owner = "Repository owner"\n'
            'expires = "2027-01-01"\n'
            'removal_condition = "remove when the sandbox fixture no longer needs it"\n'
            'category = "fixture"\n'
        )

    def _run(self, tmp_path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.check_compat_shims",
                "--check-removed-names",
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

    def test_rotation_reject_then_recover(self, tmp_path: Path) -> None:
        fixture_doc = self._sandbox(tmp_path)
        manifest = tmp_path / "tools" / "compat_exceptions.toml"
        original = manifest.read_text(encoding="utf-8")

        # Exempted: fixture entry present -> clean run.
        manifest.write_text(original + self._entry_block(), encoding="utf-8")
        result = self._run(tmp_path)
        assert result.returncode == 0, result.stdout + result.stderr

        # Rotated out: entry deleted while the claim remains -> blocking finding.
        manifest.write_text(original, encoding="utf-8")
        result = self._run(tmp_path)
        assert result.returncode == 1
        assert "sandbox_fixture.md" in result.stdout + result.stderr

        # Recovered: entry restored -> clean again.
        manifest.write_text(original + self._entry_block(), encoding="utf-8")
        result = self._run(tmp_path)
        assert result.returncode == 0, result.stdout + result.stderr

        assert fixture_doc.exists()  # sandbox mutated no real repo file


class TestOptionPairIdentity:
    """REQ-004 / AC-003: the pre-commit hook and the CI run step invoke
    exactly the same blocking option pair, with no allowlist override;
    pyproject/tox carry no checker invocation (drift tripwire)."""

    def _precommit_entry(self) -> str:
        config = yaml.safe_load(
            (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
        )
        for repo in config["repos"]:
            for hook in repo.get("hooks", []):
                if hook.get("id") == "check-compat-shims":
                    return hook["entry"]
        raise AssertionError("check-compat-shims hook not found")

    def _ci_run_step(self) -> str:
        workflow = yaml.safe_load(
            (
                REPO_ROOT / ".github" / "workflows" / "backward-compat-check.yml"
            ).read_text(encoding="utf-8")
        )
        for job in workflow["jobs"].values():
            for step in job.get("steps", []):
                run = step.get("run", "")
                if "check_compat_shims" in run:
                    return run
        raise AssertionError("checker run step not found")

    @pytest.mark.parametrize("getter", [_precommit_entry, _ci_run_step])
    def test_blocking_option_pair(self, getter) -> None:
        invocation = getter(self)
        assert "--check-removed-names" in invocation
        assert "--check-doc-symbols" in invocation
        assert "--allowlist" not in invocation

    def test_no_checker_invocation_in_pyproject_or_tox(self) -> None:
        for name in ("pyproject.toml", "tox.ini"):
            path = REPO_ROOT / name
            if path.exists():
                assert "check_compat_shims" not in path.read_text(encoding="utf-8")


class TestGateFileSelfAudit:
    """The gate file carries no retired-name literal: every checker pattern
    name must be absent from its own text."""

    def test_no_retired_name_literals(self) -> None:
        text = Path(__file__).read_text(encoding="utf-8")
        offenders = [name for name in COMPAT_PATTERNS if name in text]
        offenders += [name for name in DOC_CLAIM_PATTERNS if name in text]
        assert offenders == []
