"""Entry point: python -m mcp_servers.mdq.server"""

from mcp_servers.mdq.server import MdqMCPServer

server = MdqMCPServer()
server.run_http()  # type: ignore[attr-defined]
