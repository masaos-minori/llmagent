"""Static and unit tests for the Agent-side configuration isolation boundary."""

from __future__ import annotations

import pathlib

_FORBIDDEN_SECURITY_IMPORTS = [
    "from mcp_servers.shell.shell_models",
    "from mcp_servers.git.git_models",
    "from mcp_servers.github.github_models_config",
    "from mcp_servers.cicd.cicd_models",
]
_AGENT_DIR = pathlib.Path("scripts/agent")


def test_only_audit_module_imports_security_server_config() -> None:
    """ADR-002 INV-01: no Agent module imports an MCP server's config models.

    The name is kept as a stable ADR citation anchor. The exemption this test used to give
    ``security_audit_config.py`` is gone, because the module it exempted no longer exists, so the scan
    now covers every file under ``scripts/agent/``.
    """
    violations: list[str] = []
    for py_file in _AGENT_DIR.rglob("*.py"):
        content = py_file.read_text()
        for pattern in _FORBIDDEN_SECURITY_IMPORTS:
            if pattern in content:
                violations.append(f"{py_file}: {pattern}")
    assert not violations, (
        "Direct security server config imports inside Agent modules:\n"
        + "\n".join(violations)
    )


def test_audit_dtos_hold_no_secret_fields() -> None:
    """ADR-002 Exceptions: the Agent's security DTOs carry posture fields only, never secrets.

    Retargeted from the deleted audit config DTOs to the posture DTOs that replaced them.
    """
    import dataclasses

    from shared.security import posture_contract, result_dto

    secret_fields = {"auth_token", "github_token", "token", "api_key", "password"}
    dto_classes = [
        obj
        for module in (result_dto, posture_contract)
        for obj in vars(module).values()
        if dataclasses.is_dataclass(obj)
    ]
    assert dto_classes, "the security DTO modules expose no dataclasses"
    for cls in dto_classes:
        names = {field.name for field in dataclasses.fields(cls)}
        assert not names & secret_fields, (cls.__name__, names & secret_fields)
