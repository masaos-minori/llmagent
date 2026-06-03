"""mcp/installer_writer.py
File I/O layer for MCP server installation.
Creates template files in the repository tree.
"""

from __future__ import annotations

from pathlib import Path

from mcp.installer_port import _REPO_ROOT
from mcp.installer_templates import (
    generate_confd_template,
    generate_config_toml_for_role,
    generate_initd_script,
    generate_server_script,
)
from mcp.installer_validation import name_to_module, validate_server_name


def install_mcp_server(
    server_name: str,
    port: int,
    *,
    with_confd: bool = False,
    role: str = "",
    repo_root: Path | None = None,
) -> list[str]:
    """Write template files to the repository tree.

    Returns a list of created file paths.
    Raises FileExistsError if any target file already exists.
    Raises ValueError if server_name fails validation.
    """
    err = validate_server_name(server_name)
    if err:
        raise ValueError(err)

    root = repo_root if repo_root is not None else _REPO_ROOT
    module = name_to_module(server_name)

    targets: dict[Path, str] = {
        root / "scripts" / "mcp" / module / "__init__.py": "",
        root / "scripts" / "mcp" / module / "server.py": generate_server_script(
            server_name,
            module,
            port,
        ),
        root / "config" / f"{module}_mcp_server.toml": generate_config_toml_for_role(
            server_name,
            role,
        ),
        root / "init.d" / server_name: generate_initd_script(server_name, module, port),
    }
    if with_confd:
        targets[root / "conf.d" / server_name] = generate_confd_template(server_name)

    existing = [str(p) for p in targets if p.exists()]
    if existing:
        raise FileExistsError(f"File(s) already exist: {', '.join(existing)}")

    created: list[str] = []
    for path, content in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if path.parent.name == "init.d":
            path.chmod(0o755)
        created.append(str(path))
    return created
