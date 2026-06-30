"""Entry point: python -m mcp.mdq.server"""

import sys

from mcp.mdq.server import MdqMCPServer

server = MdqMCPServer()
if "--stdio" in sys.argv:
    import asyncio

    asyncio.run(server.run_stdio())
else:
    server.run_http()
