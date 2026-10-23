"""scripts/mcp_servers/mdq/__main__.py

Entry point: python -m mcp_servers.mdq"""

from mcp_servers.mdq.mdq_server import MdqMCPServer

if __name__ == "__main__":
    MdqMCPServer().run_http()
