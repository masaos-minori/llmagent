"""mcp/installer.py
Thin facade: re-exports the public API from the installer sub-modules.

Sub-modules:
  installer_validation.py — name validation and conversion helpers
  installer_port.py       — config-driven port allocation
  installer_templates.py  — template string generation
  installer_writer.py     — file I/O (install_mcp_server)
"""

from mcp.installer_port import scan_used_ports, suggest_port
from mcp.installer_templates import (
    generate_agent_toml_mcp_snippet,
    generate_confd_template,
    generate_config_toml,
    generate_config_toml_for_role,
    generate_initd_script,
    generate_server_script,
    tool_definition_snippet,
)
from mcp.installer_validation import name_to_class, name_to_module, validate_server_name
from mcp.installer_writer import install_mcp_server

__all__ = [
    # validation
    "validate_server_name",
    "name_to_module",
    "name_to_class",
    # port
    "scan_used_ports",
    "suggest_port",
    # templates
    "generate_server_script",
    "generate_config_toml",
    "generate_config_toml_for_role",
    "generate_agent_toml_mcp_snippet",
    "generate_initd_script",
    "generate_confd_template",
    "tool_definition_snippet",
    # writer
    "install_mcp_server",
]
