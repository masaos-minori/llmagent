"""Entry point: python -m mcp.mdq.server"""

from mcp.mdq.server import MdqMCPServer

server = MdqMCPServer()
server.run_http()
