"""tests/mcp_servers/_auth_headers.py

Authorization header for tests that call the Bearer-authenticated MCP server
applications (shell, github, file-read, file-write, file-delete).

The token is the value tests/conftest.py assigns to the five
MCP_*_AUTH_TOKEN environment variables; keep the two in step.
"""

from __future__ import annotations

MCP_TEST_TOKEN = "test-token"
MCP_TEST_AUTH_HEADERS: dict[str, str] = {"Authorization": f"Bearer {MCP_TEST_TOKEN}"}
