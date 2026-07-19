"""Entry point: python -m mcp_servers.mdq.server"""

from mcp_servers.mdq.mdq_server import MdqMCPServer

server = MdqMCPServer()
server.run_http()
