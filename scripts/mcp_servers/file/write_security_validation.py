#!/usr/bin/env python3
"""scripts/mcp_servers/file/write_security_validation.py

File Write self-validation — validate_file_write_security() reports file-write-mcp's own
configuration as a Security Posture, so the server validates itself before HTTP bind instead of
being audited by the Agent.

Held in a sibling module rather than in write_service.py because that module is already 343 lines
and the validator would carry it past the 400-line split trigger in skills/DESIGN.md.

Dependency direction: write_security_validation → common, write_models
"""

from __future__ import annotations

import os
from pathlib import Path

from shared.security.result_dto import (
    REASON_CONFIG_INVALID,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

from mcp_servers.file.common import validate_file_security_base
from mcp_servers.file.write_models import FileWriteConfig


def validate_file_write_security(cfg: FileWriteConfig) -> list[SecurityCheckResult]:
    """File-write's own configuration checks, in the order the posture contract expects.

    The allowed-directories part is delegated to validate_file_security_base() so one definition of
    those rules serves all three file servers. The function never raises for a policy violation and
    performs no filesystem mutation: writability is tested with os.access on the configured
    directory instead of by creating a probe file.

    server.supported_extensions is always not_applicable because write_models.py parses the setting
    while nothing in the write service enforces it. Reporting it as OK would assert an enforcement
    that does not exist, and omitting it would hide the gap from the check-set comparison.

    Messages report counts and setting names only: directory paths and extension patterns are
    sensitive values.
    """
    checks = validate_file_security_base(cfg.allowed_dirs)

    if cfg.max_write_bytes > 0:
        limit_status = SecurityCheckStatus.OK
        limit_reason = REASON_OK
        limit_message = "configured max_write_bytes is positive"
    else:
        limit_status = SecurityCheckStatus.FAILED
        limit_reason = REASON_CONFIG_INVALID
        limit_message = "max_write_bytes is not positive so every write is rejected"
    checks.append(
        SecurityCheckResult(
            check_id="server.max_write_bytes",
            status=limit_status,
            reason_code=limit_reason,
            message=limit_message,
        )
    )

    existing = [entry for entry in cfg.allowed_dirs if entry and Path(entry).is_dir()]
    unwritable = [entry for entry in existing if not os.access(entry, os.W_OK)]
    if not existing:
        writable_status = SecurityCheckStatus.NOT_APPLICABLE
        writable_reason = REASON_NOT_APPLICABLE
        writable_message = (
            "no existing allowed_dirs entry is available to test for writability"
        )
    elif unwritable:
        writable_status = SecurityCheckStatus.FAILED
        writable_reason = REASON_DEPENDENCY_UNREACHABLE
        writable_message = f"{len(unwritable)} of {len(existing)} allowed_dirs entries are not writable"
    else:
        writable_status = SecurityCheckStatus.OK
        writable_reason = REASON_OK
        writable_message = "every existing allowed_dirs entry is writable"
    checks.append(
        SecurityCheckResult(
            check_id="server.write_dirs_writable",
            status=writable_status,
            reason_code=writable_reason,
            message=writable_message,
        )
    )

    checks.append(
        SecurityCheckResult(
            check_id="server.supported_extensions",
            status=SecurityCheckStatus.NOT_APPLICABLE,
            reason_code=REASON_NOT_APPLICABLE,
            message="supported_extensions is parsed but not enforced by the write service",
        )
    )
    return checks
