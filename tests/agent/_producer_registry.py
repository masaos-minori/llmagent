"""tests/agent/_producer_registry.py

RuntimeToolRegistry fixture seeded from the producers' shipped TOOL_LIST
declarations.

agentcfg003 (REQ-007 authority inversion) makes the live tool declarations the
classification input for the policy/audit middleware, so tests that exercise
registry-backed paths must seed a real registry from the producer declarations
instead of hand-rolled stubs: tiers, scope keys/kinds, side-effect classes and
preview capabilities then match what ships.
"""

from __future__ import annotations

import importlib
from typing import Any

from shared.runtime_tool import RuntimeTool, build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry

# Mirrors `tests/mcp_servers/test_tool_schema_contract.py::_TOOL_LIST_MODULES`
# (module path, server_key). Keep in sync when a producer module is added.
PRODUCER_TOOL_LISTS: list[tuple[str, str]] = [
    ("mcp_servers.file.read_tools", "file"),
    ("mcp_servers.file.write_tools", "file"),
    ("mcp_servers.file.delete_tools", "file"),
    ("mcp_servers.git.git_tools", "git"),
    ("mcp_servers.github.tools_repository", "github"),
    ("mcp_servers.github.tools_file", "github"),
    ("mcp_servers.github.tools_issues", "github"),
    ("mcp_servers.github.tools_pull_requests", "github"),
    ("mcp_servers.cicd.cicd_tools", "cicd"),
    ("mcp_servers.rag_pipeline.rag_pipeline_tools", "rag_pipeline"),
    ("mcp_servers.mdq.mdq_tools", "mdq"),
    ("mcp_servers.shell.shell_tools", "shell"),
    ("mcp_servers.web_search.web_search_tools", "web_search"),
]


def make_producer_registry() -> RuntimeToolRegistry:
    """Build a RuntimeToolRegistry from every producer TOOL_LIST declaration."""
    tools: dict[str, RuntimeTool] = {}
    for module_path, server_key in PRODUCER_TOOL_LISTS:
        for entry in getattr(importlib.import_module(module_path), "TOOL_LIST"):
            fields: dict[str, Any] = dict(entry)
            name = str(fields["name"])
            tools[name] = build_runtime_tool(
                name=name,
                server_key=server_key,
                description=str(fields.get("description", "")),
                input_schema=fields.get("inputSchema"),
                raw_definition=fields,
                status=str(fields.get("status", "active")),
                is_write=bool(fields["is_write"]),
                requires_serial=bool(fields.get("requires_serial", False)),
                resource_scope_kind=str(fields["resource_scope_kind"]),
                resource_scope_keys=fields["resource_scope_keys"],
                agent_safety_tier=fields["agent_safety_tier"],
                side_effect_class=fields["side_effect_class"],
                retry_policy=fields["retry_policy"],
                reconciliation_policy=fields["reconciliation_policy"],
                idempotency_required=bool(fields["idempotency_required"]),
                preview_capability=fields["preview_capability"],
                policy_version=str(fields["policy_version"]),
            )
    return RuntimeToolRegistry(
        tools=tools,
        allowed_servers=frozenset({key for _, key in PRODUCER_TOOL_LISTS}),
    )


# name -> declared agent_safety_tier, derived from the producer declarations.
# Replaces the removed config/agent.toml [tool_safety_tiers] mirror fixture
# (agentcfg003 REQ-005): the declarations are the tier source of record.
PRODUCER_TIERS: dict[str, str] = {
    tool.name: tool.agent_safety_tier for tool in make_producer_registry().all_tools()
}
