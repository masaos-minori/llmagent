"""tests/mcp_servers/file/test_file_security_validation.py

Tests for scripts/mcp_servers/file/common.py and the per-server validators built on it:
validate_file_security_base() reports the allowed-directories rules the three file servers share,
validate_file_read_security() adds the read byte limit, validate_file_write_security() adds the
write limit, writability and the unenforced extension setting, validate_file_delete_security() adds
root protection and the audit-log dependency, an empty allowlist stays fatal, and no configured
directory path, extension value, or audit log path is echoed.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from mcp_servers.file.common import validate_file_security_base
from mcp_servers.file.delete_models import FileDeleteConfig
from mcp_servers.file.delete_service import (
    AUDIT_LOG_PATH,
    validate_file_delete_security,
)
from mcp_servers.file.read_models import FileReadConfig
from mcp_servers.file.read_security import validate_file_read_security
from mcp_servers.file.write_models import FileWriteConfig
from mcp_servers.file.write_security_validation import validate_file_write_security
from shared.security.posture_contract import COMMON_CHECK_IDS, REQUIRED_CHECK_IDS
from shared.security.result_dto import (
    REASON_ALLOWED_DIR_INVALID,
    REASON_ALLOWLIST_EMPTY,
    REASON_CONFIG_INVALID,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

BASE_CHECK_IDS = (
    "server.allowed_dirs_configured",
    "server.allowed_dirs_exist",
)
READ_CHECK_IDS = BASE_CHECK_IDS + ("server.max_read_bytes",)
WRITE_CHECK_IDS = BASE_CHECK_IDS + (
    "server.max_write_bytes",
    "server.write_dirs_writable",
    "server.supported_extensions",
)
DELETE_CHECK_IDS = BASE_CHECK_IDS + (
    "server.allowed_root_protected",
    "server.audit_log_writable",
)
FILE_SERVER_KEYS = ("file_read", "file_write", "file_delete")


def _results(allowed_dirs: tuple[str, ...]) -> dict[str, SecurityCheckResult]:
    """The shared base check results keyed by check id."""
    return {
        result.check_id: result for result in validate_file_security_base(allowed_dirs)
    }


class TestAllowedDirsConfigured:
    """An empty allowed_dirs means the server is disabled: a startup failure (REQ-009)."""

    def test_empty_allowlist_fails(self) -> None:
        result = _results(())["server.allowed_dirs_configured"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWLIST_EMPTY

    def test_non_empty_allowlist_is_ok(self, tmp_path: Path) -> None:
        result = _results((str(tmp_path),))["server.allowed_dirs_configured"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestAllowedDirsExist:
    """A configured entry the server cannot operate on is fatal, matching the health deps."""

    def test_existing_directories_are_ok(self, tmp_path: Path) -> None:
        second = tmp_path / "second"
        second.mkdir()
        result = _results((str(tmp_path), str(second)))["server.allowed_dirs_exist"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_missing_directory_fails(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist"
        result = _results((str(missing),))["server.allowed_dirs_exist"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWED_DIR_INVALID

    def test_entry_that_is_a_file_fails(self, tmp_path: Path) -> None:
        target = tmp_path / "not_a_directory"
        target.write_text("x", encoding="utf-8")
        result = _results((str(target),))["server.allowed_dirs_exist"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWED_DIR_INVALID

    def test_empty_entry_fails(self) -> None:
        result = _results(("",))["server.allowed_dirs_exist"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWED_DIR_INVALID

    def test_empty_allowlist_is_not_applicable(self) -> None:
        result = _results(())["server.allowed_dirs_exist"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_failure_reports_the_count_and_not_the_paths(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing_one"
        result = _results((str(tmp_path), str(missing)))["server.allowed_dirs_exist"]
        assert "1 of 2" in result.message
        assert str(tmp_path) not in result.message
        assert str(missing) not in result.message


class TestCheckSet:
    """The base holds only what the three file servers genuinely share."""

    def test_ids_are_the_shared_part_of_every_file_server_contract(self) -> None:
        for server_key in FILE_SERVER_KEYS:
            required = REQUIRED_CHECK_IDS[server_key]
            assert all(check_id in required for check_id in BASE_CHECK_IDS)

    def test_order_is_fixed(self) -> None:
        produced = validate_file_security_base(())
        assert [result.check_id for result in produced] == list(BASE_CHECK_IDS)

    def test_check_set_is_identical_across_configurations(self, tmp_path: Path) -> None:
        configurations = (
            (),
            (str(tmp_path),),
            (str(tmp_path / "missing"),),
            ("",),
        )
        for allowed_dirs in configurations:
            produced = validate_file_security_base(allowed_dirs)
            assert [result.check_id for result in produced] == list(BASE_CHECK_IDS)
            assert len(produced) == len(BASE_CHECK_IDS)

    def test_never_raises_for_a_policy_violation(self) -> None:
        produced = validate_file_security_base(("", "missing"))
        assert all(isinstance(result, SecurityCheckResult) for result in produced)


class TestMessages:
    """Allowed directory paths are sensitive paths (REQ-002)."""

    def test_no_message_names_a_configured_directory(self, tmp_path: Path) -> None:
        private = tmp_path / "private_dir"
        private.mkdir()
        produced = validate_file_security_base((str(private), str(tmp_path / "gone")))
        for result in produced:
            assert "private_dir" not in result.message
            assert str(tmp_path) not in result.message


def _read_results(
    allowed_dirs: tuple[str, ...],
    max_read_bytes: int,
) -> dict[str, SecurityCheckResult]:
    """The file-read check results keyed by check id."""
    cfg = FileReadConfig(
        allowed_dirs=list(allowed_dirs),
        max_read_bytes=max_read_bytes,
    )
    return {result.check_id: result for result in validate_file_read_security(cfg)}


class TestMaxReadBytes:
    """A non-positive byte limit rejects every read: a configuration error (REQ-009)."""

    def test_zero_limit_fails(self) -> None:
        result = _read_results(("dir",), 0)["server.max_read_bytes"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_negative_limit_fails(self) -> None:
        result = _read_results(("dir",), -1)["server.max_read_bytes"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_positive_limit_is_ok(self) -> None:
        result = _read_results(("dir",), 1)["server.max_read_bytes"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_limit_is_reported_even_when_the_directories_are_valid(
        self, tmp_path: Path
    ) -> None:
        result = _read_results((str(tmp_path),), 0)["server.max_read_bytes"]
        dirs_check = _read_results((str(tmp_path),), 0)["server.allowed_dirs_exist"]
        assert dirs_check.status is SecurityCheckStatus.OK
        assert result.status is SecurityCheckStatus.FAILED


class TestFileReadCheckSet:
    """The read validator keeps the shared prefix and appends only read-specific checks."""

    def test_ids_match_the_frozen_contract(self) -> None:
        expected = tuple(
            check_id
            for check_id in REQUIRED_CHECK_IDS["file_read"]
            if check_id not in COMMON_CHECK_IDS
        )
        produced = validate_file_read_security(FileReadConfig())
        assert [result.check_id for result in produced] == list(expected)
        assert expected == READ_CHECK_IDS

    def test_shared_prefix_comes_first(self) -> None:
        produced = validate_file_read_security(FileReadConfig())
        assert [result.check_id for result in produced][:2] == list(BASE_CHECK_IDS)

    def test_check_set_is_identical_across_configurations(self, tmp_path: Path) -> None:
        configurations = (
            ((), 1024000),
            ((str(tmp_path),), 1024000),
            ((str(tmp_path / "missing"),), 0),
            (("",), -1),
        )
        for allowed_dirs, max_read_bytes in configurations:
            produced = validate_file_read_security(
                FileReadConfig(
                    allowed_dirs=list(allowed_dirs),
                    max_read_bytes=max_read_bytes,
                )
            )
            assert [result.check_id for result in produced] == list(READ_CHECK_IDS)

    def test_never_raises_for_a_policy_violation(self) -> None:
        produced = validate_file_read_security(
            FileReadConfig(allowed_dirs=[""], max_read_bytes=0)
        )
        assert all(isinstance(result, SecurityCheckResult) for result in produced)


class TestFileReadMessages:
    """The read-specific checks follow the same no-path rule (REQ-002)."""

    def test_no_message_names_a_configured_directory(self, tmp_path: Path) -> None:
        private = tmp_path / "private_dir"
        private.mkdir()
        produced = validate_file_read_security(
            FileReadConfig(
                allowed_dirs=[str(private), str(tmp_path / "gone")],
                max_read_bytes=0,
            )
        )
        for result in produced:
            assert "private_dir" not in result.message
            assert str(tmp_path) not in result.message


def _write_results(
    allowed_dirs: tuple[str, ...],
    max_write_bytes: int,
    supported_extensions: tuple[str, ...] = (),
) -> dict[str, SecurityCheckResult]:
    """The file-write check results keyed by check id."""
    cfg = FileWriteConfig(
        allowed_dirs=list(allowed_dirs),
        max_write_bytes=max_write_bytes,
        supported_extensions=list(supported_extensions),
    )
    return {result.check_id: result for result in validate_file_write_security(cfg)}


class TestMaxWriteBytes:
    """A non-positive byte limit rejects every write: a configuration error (REQ-009)."""

    def test_zero_limit_fails(self) -> None:
        result = _write_results(("dir",), 0)["server.max_write_bytes"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_positive_limit_is_ok(self) -> None:
        result = _write_results(("dir",), 1)["server.max_write_bytes"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestWriteDirsWritable:
    """An unwritable allowed directory only appears as a request failure today (REQ-009)."""

    def test_writable_directory_is_ok(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(os, "access", lambda path, mode: True)
        result = _write_results((str(tmp_path),), 100)["server.write_dirs_writable"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_unwritable_directory_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(os, "access", lambda path, mode: False)
        result = _write_results((str(tmp_path),), 100)["server.write_dirs_writable"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_empty_allowlist_is_not_applicable(self) -> None:
        result = _write_results((), 100)["server.write_dirs_writable"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_missing_directory_is_not_applicable(self, tmp_path: Path) -> None:
        result = _write_results((str(tmp_path / "missing"),), 100)[
            "server.write_dirs_writable"
        ]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_failure_reports_the_count_and_not_the_paths(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        second = tmp_path / "second"
        second.mkdir()
        monkeypatch.setattr(os, "access", lambda path, mode: False)
        result = _write_results((str(tmp_path), str(second)), 100)[
            "server.write_dirs_writable"
        ]
        assert "2 of 2" in result.message
        assert str(tmp_path) not in result.message
        assert str(second) not in result.message


class TestSupportedExtensions:
    """The posture must not claim an enforcement that does not exist (REQ-009)."""

    def test_always_not_applicable_even_when_configured(self, tmp_path: Path) -> None:
        result = _write_results((str(tmp_path),), 100, (".md", ".txt"))[
            "server.supported_extensions"
        ]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_never_omitted(self) -> None:
        for allowed_dirs, max_write_bytes in (((), 0), (("dir",), 100)):
            produced = _write_results(allowed_dirs, max_write_bytes)
            assert "server.supported_extensions" in produced


class TestFileWriteCheckSet:
    """The write validator keeps the shared prefix and appends only write-specific checks."""

    def test_ids_match_the_frozen_contract(self) -> None:
        expected = tuple(
            check_id
            for check_id in REQUIRED_CHECK_IDS["file_write"]
            if check_id not in COMMON_CHECK_IDS
        )
        produced = validate_file_write_security(FileWriteConfig())
        assert [result.check_id for result in produced] == list(expected)
        assert expected == WRITE_CHECK_IDS

    def test_shared_prefix_comes_first(self) -> None:
        produced = validate_file_write_security(FileWriteConfig())
        assert [result.check_id for result in produced][:2] == list(BASE_CHECK_IDS)

    def test_check_set_is_identical_across_configurations(self, tmp_path: Path) -> None:
        configurations = (
            ((), 1048576),
            ((str(tmp_path),), 1048576),
            ((str(tmp_path / "missing"),), 0),
            (("",), -1),
        )
        for allowed_dirs, max_write_bytes in configurations:
            produced = validate_file_write_security(
                FileWriteConfig(
                    allowed_dirs=list(allowed_dirs),
                    max_write_bytes=max_write_bytes,
                )
            )
            assert [result.check_id for result in produced] == list(WRITE_CHECK_IDS)

    def test_never_raises_for_a_policy_violation(self) -> None:
        produced = validate_file_write_security(
            FileWriteConfig(allowed_dirs=[""], max_write_bytes=0)
        )
        assert all(isinstance(result, SecurityCheckResult) for result in produced)


class TestFileWriteMessages:
    """Directory paths and extension allowlists stay out of the posture (REQ-002)."""

    def test_no_message_names_a_directory_or_an_extension(self, tmp_path: Path) -> None:
        private = tmp_path / "private_dir"
        private.mkdir()
        produced = validate_file_write_security(
            FileWriteConfig(
                allowed_dirs=[str(private), str(tmp_path / "gone")],
                max_write_bytes=0,
                supported_extensions=[".secretext"],
            )
        )
        for result in produced:
            assert "private_dir" not in result.message
            assert str(tmp_path) not in result.message
            assert ".secretext" not in result.message


def _delete_results(
    allowed_dirs: tuple[str, ...],
    audit_log_path: str = AUDIT_LOG_PATH,
) -> dict[str, SecurityCheckResult]:
    """The file-delete check results keyed by check id."""
    cfg = FileDeleteConfig(allowed_dirs=list(allowed_dirs))
    return {
        result.check_id: result
        for result in validate_file_delete_security(cfg, audit_log_path)
    }


class TestAllowedRootProtected:
    """A root-wide allowlist defeats _check_not_deleting_allowed_root() (REQ-009)."""

    def test_root_entry_fails(self) -> None:
        result = _delete_results(("/",))["server.allowed_root_protected"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_entry_that_resolves_to_root_fails(self) -> None:
        result = _delete_results(("/tmp/../",))["server.allowed_root_protected"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_bounded_entry_is_ok(self, tmp_path: Path) -> None:
        result = _delete_results((str(tmp_path),))["server.allowed_root_protected"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_empty_allowlist_is_not_applicable(self) -> None:
        result = _delete_results(())["server.allowed_root_protected"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_root_is_reported_even_when_the_other_checks_are_valid(
        self, tmp_path: Path
    ) -> None:
        results = _delete_results((str(tmp_path), "/"))
        assert results["server.allowed_dirs_exist"].status is SecurityCheckStatus.OK
        assert (
            results["server.allowed_root_protected"].status
            is SecurityCheckStatus.FAILED
        )


class TestAuditLogWritable:
    """A delete server that cannot record what it deleted must not report Ready (REQ-009)."""

    def test_writable_parent_is_ok(self, tmp_path: Path) -> None:
        logs = tmp_path / "logs"
        logs.mkdir()
        result = _delete_results((str(tmp_path),), str(logs / "audit.log"))[
            "server.audit_log_writable"
        ]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_missing_parent_fails(self, tmp_path: Path) -> None:
        result = _delete_results(
            (str(tmp_path),), str(tmp_path / "gone" / "audit.log")
        )["server.audit_log_writable"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_unwritable_parent_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        logs = tmp_path / "logs"
        logs.mkdir()
        monkeypatch.setattr(os, "access", lambda path, mode: False)
        result = _delete_results((str(tmp_path),), str(logs / "audit.log"))[
            "server.audit_log_writable"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_audit_path_that_is_a_directory_fails(self, tmp_path: Path) -> None:
        result = _delete_results((str(tmp_path),), str(tmp_path))[
            "server.audit_log_writable"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_empty_audit_path_is_not_applicable(self, tmp_path: Path) -> None:
        result = _delete_results((str(tmp_path),), "")["server.audit_log_writable"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_failure_does_not_name_the_audit_path(self, tmp_path: Path) -> None:
        result = _delete_results(
            (str(tmp_path),), str(tmp_path / "gone" / "delete_audit.log")
        )["server.audit_log_writable"]
        assert "delete_audit.log" not in result.message
        assert str(tmp_path) not in result.message


class TestFileDeleteCheckSet:
    """The delete validator keeps the shared prefix and appends only delete-specific checks."""

    def test_ids_match_the_frozen_contract(self) -> None:
        expected = tuple(
            check_id
            for check_id in REQUIRED_CHECK_IDS["file_delete"]
            if check_id not in COMMON_CHECK_IDS
        )
        produced = validate_file_delete_security(FileDeleteConfig())
        assert [result.check_id for result in produced] == list(expected)
        assert expected == DELETE_CHECK_IDS

    def test_shared_prefix_comes_first(self) -> None:
        produced = validate_file_delete_security(FileDeleteConfig())
        assert [result.check_id for result in produced][:2] == list(BASE_CHECK_IDS)

    def test_check_set_is_identical_across_configurations(self, tmp_path: Path) -> None:
        configurations = (
            (),
            (str(tmp_path),),
            ("/",),
            ("",),
        )
        for allowed_dirs in configurations:
            produced = validate_file_delete_security(
                FileDeleteConfig(allowed_dirs=list(allowed_dirs))
            )
            assert [result.check_id for result in produced] == list(DELETE_CHECK_IDS)

    def test_never_raises_for_a_policy_violation(self) -> None:
        produced = validate_file_delete_security(
            FileDeleteConfig(allowed_dirs=["/", ""]),
            audit_log_path="/",
        )
        assert all(isinstance(result, SecurityCheckResult) for result in produced)


class TestFileDeleteMessages:
    """Allowed directory paths and the audit log path stay out of the posture (REQ-002)."""

    def test_no_message_names_a_configured_path(self, tmp_path: Path) -> None:
        private = tmp_path / "private_dir"
        private.mkdir()
        produced = validate_file_delete_security(
            FileDeleteConfig(allowed_dirs=[str(private), str(tmp_path / "gone")]),
            audit_log_path=str(tmp_path / "gone" / "delete_audit.log"),
        )
        for result in produced:
            assert "private_dir" not in result.message
            assert str(tmp_path) not in result.message
            assert AUDIT_LOG_PATH not in result.message
