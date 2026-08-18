"""Generate MCP server inventory from agent config."""

import argparse
import csv
import json
import sys

from scripts.agent.config_builders import build_agent_config
from scripts.shared.mcp_config import TransportType


def generate_inventory() -> list[dict]:
    """Generate inventory data from current configuration."""
    cfg = build_agent_config()
    inventory = []
    for key, server in cfg.mcp.mcp_servers.items():
        entry = {
            "name": key,
            "transport": server.transport.value,
            "startup_mode": server.startup_mode.value,
            "url": server.url if server.transport == TransportType.HTTP else "",
            "cmd": "; ".join(server.cmd) if server.requires_cmd else "",
            "tool_names": ", ".join(server.tool_names) if server.tool_names else "",
            "status": "disabled" if server.is_disabled else "enabled",
        }
        inventory.append(entry)
    return inventory


def output_json(inventory: list[dict]) -> None:
    """Output inventory as JSON."""
    json.dump(inventory, sys.stdout, indent=2, ensure_ascii=False)
    print()


def output_csv(inventory: list[dict]) -> None:
    """Output inventory as CSV."""
    if not inventory:
        return
    writer = csv.DictWriter(sys.stdout, fieldnames=inventory[0].keys())
    writer.writeheader()
    writer.writerows(inventory)


def main() -> None:
    """Generate MCP server inventory."""
    parser = argparse.ArgumentParser(description="Generate MCP server inventory")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    args = parser.parse_args()

    inventory = generate_inventory()

    if args.format == "json":
        output_json(inventory)
    else:
        output_csv(inventory)


if __name__ == "__main__":
    main()
